"""
RAG Service - Retrieval Augmented Generation for Architecture Documents.

Primary mode:
- ChromaDB + sentence-transformers vector retrieval

Fallback mode (when vector deps are unavailable):
- lightweight lexical retrieval with persisted local index
"""

import json
import logging
import math
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from app.models.schemas import (
    DocumentUploadResponse,
    DocumentSearchResponse,
    DocumentChunk,
    DocumentMetadata,
)
from app.services.document_parser import create_document_parser, DocumentChunk as ParserChunk

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for document storage and retrieval."""

    def __init__(
        self,
        chroma_persist_directory: str = "./data/chromadb",
        embedding_model: str = "all-MiniLM-L6-v2",
        fallback_index_path: str = "./data/rag_fallback_index.json",
    ):
        self.chroma_persist_directory = chroma_persist_directory
        self.embedding_model_name = embedding_model
        self.fallback_index_path = Path(fallback_index_path)

        self.client = None
        self.collection = None
        self.embedder = None
        self.backend_mode = "vector"

        self._fallback_chunks: List[dict] = []
        self._fallback_documents: dict = {}

        self.parser = create_document_parser()

        vector_deps_ready = chromadb is not None and SentenceTransformer is not None

        if vector_deps_ready:
            try:
                self.client = chromadb.Client(
                    Settings(
                        persist_directory=chroma_persist_directory,
                        anonymized_telemetry=False,
                    )
                )
                self.collection = self.client.get_or_create_collection(
                    name="architecture_docs",
                    metadata={"description": "Architecture documentation and knowledge base"},
                )
                self.embedder = SentenceTransformer(embedding_model)
                logger.info("RAG initialized in vector mode with model: %s", embedding_model)
            except Exception as e:
                logger.warning("Vector RAG initialization failed, switching to fallback mode: %s", e)
                self._init_fallback_mode()
        else:
            missing = []
            if chromadb is None:
                missing.append("chromadb")
            if SentenceTransformer is None:
                missing.append("sentence-transformers")
            logger.warning(
                "Vector RAG dependencies missing (%s), using lexical fallback mode",
                ", ".join(missing) if missing else "unknown",
            )
            self._init_fallback_mode()

    def _init_fallback_mode(self):
        self.backend_mode = "fallback"
        self.embedding_model_name = "lexical-tf-fallback-v1"
        self.client = None
        self.collection = None
        self.embedder = None
        self._load_fallback_index()

    def _load_fallback_index(self):
        try:
            if not self.fallback_index_path.exists():
                self._fallback_chunks = []
                self._fallback_documents = {}
                return

            data = json.loads(self.fallback_index_path.read_text(encoding="utf-8"))
            self._fallback_chunks = data.get("chunks", [])
            documents = data.get("documents", [])
            self._fallback_documents = {
                doc["document_id"]: doc for doc in documents if doc.get("document_id")
            }
            logger.info(
                "Loaded fallback RAG index: %d docs, %d chunks",
                len(self._fallback_documents),
                len(self._fallback_chunks),
            )
        except Exception as e:
            logger.warning("Failed to load fallback RAG index, starting empty: %s", e)
            self._fallback_chunks = []
            self._fallback_documents = {}

    def _save_fallback_index(self):
        try:
            self.fallback_index_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "documents": list(self._fallback_documents.values()),
                "chunks": self._fallback_chunks,
                "updated_at": datetime.now().isoformat(),
            }
            self.fallback_index_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Failed to persist fallback RAG index: %s", e)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        if not text:
            return []
        import re

        # Keep English words/numbers and CJK chars for mixed-language queries
        return re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]", text.lower())

    @staticmethod
    def _cosine_similarity(a: Counter, b: Counter) -> float:
        if not a or not b:
            return 0.0
        intersection = set(a.keys()) & set(b.keys())
        numerator = sum(a[t] * b[t] for t in intersection)
        denom_a = math.sqrt(sum(v * v for v in a.values()))
        denom_b = math.sqrt(sum(v * v for v in b.values()))
        if denom_a == 0 or denom_b == 0:
            return 0.0
        return float(numerator / (denom_a * denom_b))

    def _fallback_score(self, query: str, content: str) -> float:
        q_tokens = self._tokenize(query)
        d_tokens = self._tokenize(content)
        if not q_tokens or not d_tokens:
            return 0.0

        q_counter = Counter(q_tokens)
        d_counter = Counter(d_tokens)
        cosine = self._cosine_similarity(q_counter, d_counter)

        overlap = len(set(q_tokens) & set(d_tokens))
        coverage = overlap / max(len(set(q_tokens)), 1)

        return 0.7 * cosine + 0.3 * coverage

    async def upload_document(
        self, file_path: str, filename: str, file_type: str
    ) -> DocumentUploadResponse:
        """Upload and process a document."""
        try:
            chunks: List[ParserChunk] = self.parser.parse_file(file_path, file_type)
            if len(chunks) == 0:
                return DocumentUploadResponse(
                    document_id="",
                    chunks_created=0,
                    success=False,
                    message="Document is empty or could not be parsed",
                )

            document_id = str(uuid.uuid4())
            upload_date = datetime.now().isoformat()

            if self.backend_mode == "vector":
                chunk_texts = [chunk.content for chunk in chunks]
                embeddings = self.embedder.encode(chunk_texts, show_progress_bar=False)

                ids = [f"{document_id}_{chunk.chunk_id}" for chunk in chunks]
                metadatas = [
                    {
                        "document_id": document_id,
                        "filename": filename,
                        "file_type": file_type,
                        "upload_date": upload_date,
                        "chunk_index": chunk.metadata.get("chunk_index", 0),
                        **chunk.metadata,
                    }
                    for chunk in chunks
                ]

                self.collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    documents=chunk_texts,
                    metadatas=metadatas,
                )
            else:
                self._fallback_documents[document_id] = {
                    "document_id": document_id,
                    "filename": filename,
                    "file_type": file_type,
                    "upload_date": upload_date,
                    "num_chunks": len(chunks),
                }

                for chunk in chunks:
                    chunk_id = f"{document_id}_{chunk.chunk_id}"
                    self._fallback_chunks.append(
                        {
                            "chunk_id": chunk_id,
                            "document_id": document_id,
                            "content": chunk.content,
                            "metadata": {
                                "document_id": document_id,
                                "filename": filename,
                                "file_type": file_type,
                                "upload_date": upload_date,
                                "chunk_index": chunk.metadata.get("chunk_index", 0),
                                **chunk.metadata,
                            },
                        }
                    )

                self._save_fallback_index()

            logger.info(
                "Uploaded document %s (%s): %d chunks via %s mode",
                filename,
                document_id,
                len(chunks),
                self.backend_mode,
            )

            return DocumentUploadResponse(
                document_id=document_id,
                chunks_created=len(chunks),
                success=True,
                message=f"Successfully uploaded {filename} with {len(chunks)} chunks",
            )

        except Exception as e:
            logger.error("Failed to upload document %s: %s", filename, e, exc_info=True)
            return DocumentUploadResponse(
                document_id="",
                chunks_created=0,
                success=False,
                message=f"Upload failed: {str(e)}",
            )

    async def search_documents(self, query: str, top_k: int = 5) -> DocumentSearchResponse:
        """Search for relevant document chunks."""
        try:
            chunks: List[DocumentChunk] = []

            if self.backend_mode == "vector":
                query_embedding = self.embedder.encode(query, show_progress_bar=False)
                results = self.collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=top_k,
                )

                if results.get("ids") and len(results["ids"][0]) > 0:
                    for i in range(len(results["ids"][0])):
                        chunk_id = results["ids"][0][i]
                        content = results["documents"][0][i]
                        metadata_raw = results["metadatas"][0][i]
                        distance = results["distances"][0][i] if "distances" in results else 0.0
                        score = 1.0 / (1.0 + distance)

                        doc_metadata = DocumentMetadata(
                            filename=metadata_raw.get("filename", "Unknown"),
                            file_type=metadata_raw.get("file_type", "unknown"),
                            upload_date=metadata_raw.get("upload_date", ""),
                            num_chunks=1,
                        )

                        chunks.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                content=content,
                                score=score,
                                metadata=doc_metadata,
                            )
                        )
            else:
                ranked = []
                for chunk in self._fallback_chunks:
                    score = self._fallback_score(query, chunk.get("content", ""))
                    if score <= 0:
                        continue
                    ranked.append((score, chunk))

                ranked.sort(key=lambda x: x[0], reverse=True)
                for score, chunk in ranked[:top_k]:
                    metadata_raw = chunk.get("metadata", {})
                    doc_id = metadata_raw.get("document_id")
                    doc_info = self._fallback_documents.get(doc_id, {})
                    doc_metadata = DocumentMetadata(
                        filename=metadata_raw.get("filename", "Unknown"),
                        file_type=metadata_raw.get("file_type", "unknown"),
                        upload_date=metadata_raw.get("upload_date", ""),
                        num_chunks=doc_info.get("num_chunks", 1),
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk.get("chunk_id", ""),
                            content=chunk.get("content", ""),
                            score=float(score),
                            metadata=doc_metadata,
                        )
                    )

            logger.info("Search query '%s': found %d results via %s mode", query, len(chunks), self.backend_mode)
            return DocumentSearchResponse(chunks=chunks, query=query, success=True)

        except Exception as e:
            logger.error("Failed to search documents: %s", e, exc_info=True)
            return DocumentSearchResponse(chunks=[], query=query, success=False)

    def get_collection_stats(self) -> dict:
        """Get statistics about the document collection."""
        try:
            if self.backend_mode == "vector":
                count = self.collection.count()
                collection_name = self.collection.name
            else:
                count = len(self._fallback_chunks)
                collection_name = "fallback_index"

            return {
                "total_chunks": count,
                "collection_name": collection_name,
                "embedding_model": self.embedding_model_name,
                "mode": self.backend_mode,
            }
        except Exception as e:
            logger.error("Failed to get collection stats: %s", e)
            return {
                "total_chunks": 0,
                "mode": self.backend_mode,
                "error": str(e),
            }

    async def list_documents(self) -> List[dict]:
        """List all unique documents in the collection."""
        try:
            if self.backend_mode == "vector":
                results = self.collection.get()
                documents_map = {}
                if results and results.get("metadatas"):
                    for metadata in results["metadatas"]:
                        doc_id = metadata.get("document_id")
                        if doc_id and doc_id not in documents_map:
                            documents_map[doc_id] = {
                                "document_id": doc_id,
                                "filename": metadata.get("filename", "Unknown"),
                                "file_type": metadata.get("file_type", "unknown"),
                                "upload_date": metadata.get("upload_date", ""),
                            }
                documents = list(documents_map.values())
            else:
                documents = list(self._fallback_documents.values())

            documents.sort(key=lambda d: d.get("upload_date", ""), reverse=True)
            logger.info("Found %d unique documents", len(documents))
            return documents

        except Exception as e:
            logger.error("Failed to list documents: %s", e, exc_info=True)
            return []

    async def delete_document(self, document_id: str):
        """Delete all chunks for a document."""
        try:
            if self.backend_mode == "vector":
                results = self.collection.get(where={"document_id": document_id})
                if results and results.get("ids"):
                    ids_to_delete = results["ids"]
                    self.collection.delete(ids=ids_to_delete)
                    logger.info("Deleted document %s: %d chunks", document_id, len(ids_to_delete))
                else:
                    logger.warning("Document %s not found", document_id)
            else:
                before = len(self._fallback_chunks)
                self._fallback_chunks = [
                    c for c in self._fallback_chunks if c.get("document_id") != document_id
                ]
                self._fallback_documents.pop(document_id, None)
                self._save_fallback_index()
                deleted = before - len(self._fallback_chunks)
                if deleted > 0:
                    logger.info("Deleted document %s: %d chunks (fallback)", document_id, deleted)
                else:
                    logger.warning("Document %s not found (fallback)", document_id)

        except Exception as e:
            logger.error("Failed to delete document %s: %s", document_id, e, exc_info=True)
            raise

    async def get_stats(self) -> dict:
        """Get comprehensive statistics about the RAG system."""
        try:
            stats = self.get_collection_stats()
            documents = await self.list_documents()
            stats["total_documents"] = len(documents)
            stats["recent_documents"] = documents[:5]
            stats["mode"] = self.backend_mode
            return stats
        except Exception as e:
            logger.error("Failed to get stats: %s", e)
            return {"error": str(e), "mode": self.backend_mode}


# Helper function to create RAG service instance
def create_rag_service() -> RAGService:
    """Create a RAGService instance."""
    return RAGService()
