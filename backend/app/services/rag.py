"""
RAG Service - Retrieval Augmented Generation for Architecture Documents
Uses ChromaDB for vector storage and sentence-transformers for embeddings
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

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
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentChunk,
    DocumentMetadata,
)
from app.services.document_parser import create_document_parser, DocumentChunk as ParserChunk

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for document storage and retrieval"""

    def __init__(
        self,
        chroma_persist_directory: str = "./data/chromadb",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        if chromadb is None:
            raise ImportError(
                "ChromaDB is not installed. Install with: pip install chromadb"
            )

        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is not installed. Install with: pip install sentence-transformers"
            )

        self.chroma_persist_directory = chroma_persist_directory
        self.embedding_model_name = embedding_model

        # Initialize ChromaDB client
        try:
            self.client = chromadb.Client(
                Settings(
                    persist_directory=chroma_persist_directory,
                    anonymized_telemetry=False,
                )
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise

        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name="architecture_docs",
                metadata={"description": "Architecture documentation and knowledge base"},
            )
        except Exception as e:
            logger.error(f"Failed to create ChromaDB collection: {e}")
            raise

        # Initialize embedding model
        try:
            self.embedder = SentenceTransformer(embedding_model)
            logger.info(f"Loaded embedding model: {embedding_model}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

        # Initialize document parser
        self.parser = create_document_parser()

    async def upload_document(
        self, file_path: str, filename: str, file_type: str
    ) -> DocumentUploadResponse:
        """Upload and process a document"""

        try:
            # Parse document into chunks
            chunks: List[ParserChunk] = self.parser.parse_file(file_path, file_type)

            if len(chunks) == 0:
                return DocumentUploadResponse(
                    document_id="",
                    chunks_created=0,
                    success=False,
                    message="Document is empty or could not be parsed",
                )

            # Generate unique document ID
            document_id = str(uuid.uuid4())
            upload_date = datetime.now().isoformat()

            # Generate embeddings for all chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedder.encode(chunk_texts, show_progress_bar=False)

            # Prepare data for ChromaDB
            ids = [f"{document_id}_{chunk.chunk_id}" for chunk in chunks]
            metadatas = [
                {
                    "document_id": document_id,
                    "filename": filename,
                    "file_type": file_type,
                    "upload_date": upload_date,
                    "chunk_index": chunk.metadata["chunk_index"],
                    **chunk.metadata,
                }
                for chunk in chunks
            ]

            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                documents=chunk_texts,
                metadatas=metadatas,
            )

            logger.info(
                f"Uploaded document {filename} ({document_id}): {len(chunks)} chunks"
            )

            return DocumentUploadResponse(
                document_id=document_id,
                chunks_created=len(chunks),
                success=True,
                message=f"Successfully uploaded {filename} with {len(chunks)} chunks",
            )

        except Exception as e:
            logger.error(f"Failed to upload document {filename}: {e}", exc_info=True)
            return DocumentUploadResponse(
                document_id="",
                chunks_created=0,
                success=False,
                message=f"Upload failed: {str(e)}",
            )

    async def search_documents(
        self, query: str, top_k: int = 5
    ) -> DocumentSearchResponse:
        """Search for relevant document chunks"""

        try:
            # Generate query embedding
            query_embedding = self.embedder.encode(query, show_progress_bar=False)

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
            )

            # Parse results
            chunks: List[DocumentChunk] = []

            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chunk_id = results["ids"][0][i]
                    content = results["documents"][0][i]
                    metadata_raw = results["metadatas"][0][i]
                    distance = results["distances"][0][i] if "distances" in results else 0.0

                    # Convert distance to similarity score (lower is better, so invert)
                    score = 1.0 / (1.0 + distance)

                    # Build DocumentMetadata
                    doc_metadata = DocumentMetadata(
                        filename=metadata_raw.get("filename", "Unknown"),
                        file_type=metadata_raw.get("file_type", "unknown"),
                        upload_date=metadata_raw.get("upload_date", ""),
                        num_chunks=1,  # We don't track this per chunk
                    )

                    chunk = DocumentChunk(
                        chunk_id=chunk_id,
                        content=content,
                        score=score,
                        metadata=doc_metadata,
                    )
                    chunks.append(chunk)

            logger.info(f"Search query '{query}': found {len(chunks)} results")

            return DocumentSearchResponse(
                chunks=chunks,
                query=query,
                success=True,
            )

        except Exception as e:
            logger.error(f"Failed to search documents: {e}", exc_info=True)
            return DocumentSearchResponse(
                chunks=[],
                query=query,
                success=False,
            )

    def get_collection_stats(self) -> dict:
        """Get statistics about the document collection"""

        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection.name,
                "embedding_model": self.embedding_model_name,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "total_chunks": 0,
                "error": str(e),
            }

    async def list_documents(self) -> List[dict]:
        """List all unique documents in the collection"""
        try:
            # Get all data from collection
            results = self.collection.get()

            # Extract unique documents
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
            logger.info(f"Found {len(documents)} unique documents")
            return documents

        except Exception as e:
            logger.error(f"Failed to list documents: {e}", exc_info=True)
            return []

    async def delete_document(self, document_id: str):
        """Delete all chunks for a document"""
        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )

            if results and results.get("ids"):
                ids_to_delete = results["ids"]
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted document {document_id}: {len(ids_to_delete)} chunks")
            else:
                logger.warning(f"Document {document_id} not found")

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}", exc_info=True)
            raise

    async def get_stats(self) -> dict:
        """Get comprehensive statistics about the RAG system"""
        try:
            stats = self.get_collection_stats()
            documents = await self.list_documents()
            stats["total_documents"] = len(documents)
            stats["recent_documents"] = documents[:5]  # Last 5 documents
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "error": str(e)
            }


# Helper function to create RAG service instance
def create_rag_service() -> RAGService:
    """Create a RAGService instance"""
    return RAGService()
