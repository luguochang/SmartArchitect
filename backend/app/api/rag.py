"""
RAG Knowledge Base API Router
Handles document upload and semantic search
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
import logging
import os
import tempfile
from datetime import datetime

from app.models.schemas import (
    DocumentUploadResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
)
from app.services.rag import create_rag_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize RAG service
rag_service = None

def get_rag_service():
    """Lazy initialization of RAG service"""
    global rag_service
    if rag_service is None:
        rag_service = create_rag_service()
    return rag_service


@router.post("/rag/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
):
    """Upload and index a document for RAG

    Supports PDF, Markdown (.md), and Docx formats

    Args:
        file: Document file to upload

    Returns:
        DocumentUploadResponse with document ID and chunks created
    """
    try:
        logger.info(f"Uploading document: {file.filename}")

        # Validate file type
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension == ".md":
            file_type = "markdown"
        elif file_extension == ".pdf":
            file_type = "pdf"
        elif file_extension in [".docx", ".doc"]:
            file_type = "docx"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported: .pdf, .md, .docx"
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # Process document
            service = get_rag_service()
            response = await service.upload_document(
                file_path=tmp_file_path,
                filename=file.filename,
                file_type=file_type
            )

            logger.info(f"Document uploaded successfully: {response.document_id}, {response.chunks_created} chunks")

            return response

        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post("/rag/search", response_model=DocumentSearchResponse)
async def search_documents(request: DocumentSearchRequest):
    """Search the RAG knowledge base

    Performs semantic search across all indexed documents

    Args:
        request: Search query and parameters

    Returns:
        DocumentSearchResponse with relevant chunks
    """
    try:
        logger.info(f"Searching documents: '{request.query}' (top_k={request.top_k})")

        service = get_rag_service()
        response = await service.search_documents(
            query=request.query,
            top_k=request.top_k
        )

        logger.info(f"Found {len(response.chunks)} relevant chunks")

        return response

    except Exception as e:
        logger.error(f"Document search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search documents: {str(e)}"
        )


@router.get("/rag/documents")
async def list_documents():
    """List all documents in the knowledge base

    Returns:
        List of document metadata
    """
    try:
        service = get_rag_service()
        documents = await service.list_documents()

        return {
            "documents": documents,
            "total": len(documents)
        }

    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/rag/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the knowledge base

    Args:
        document_id: ID of document to delete

    Returns:
        Success message
    """
    try:
        service = get_rag_service()
        await service.delete_document(document_id)

        logger.info(f"Deleted document: {document_id}")

        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully"
        }

    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/rag/health")
async def rag_health():
    """RAG service health check

    Returns:
        Service status and configuration
    """
    try:
        service = get_rag_service()
        stats = await service.get_stats()

        return {
            "status": "healthy",
            "supported_formats": ["pdf", "markdown", "docx"],
            "embedding_model": "all-MiniLM-L6-v2",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
