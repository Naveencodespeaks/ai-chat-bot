from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime

from app.core.logging import logger
from app.db.deps import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.documents import Document
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadRequest,
    DocumentCreateRequest,
)
from app.rag.ingest import ingest_document
from app.core.config import settings


router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document",
    description="Upload and ingest a document for RAG"
)
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a document for RAG ingestion.
    
    Supported formats: PDF, TXT, MD, DOCX
    
    The system will:
    1. Store the document metadata
    2. Extract and chunk the content
    3. Generate embeddings
    4. Store in vector database
    
    Request Parameters:
        file: Document file (multipart/form-data)
        metadata: Optional JSON metadata
    
    Returns:
        DocumentResponse: Created document information
    """
    try:
        # Validate file
        allowed_extensions = {".pdf", ".txt", ".md", ".docx"}
        file_ext = f".{file.filename.split('.')[-1].lower()}"
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Supported: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Create document record
        document = Document(
            id=f"doc_{int(datetime.now().timestamp() * 1000)}",
            title=file.filename,
            name=file.filename,
            file_path=f"uploads/{file.filename}",
            document_type=file.content_type or "application/octet-stream",
            content_type=file.content_type or "application/octet-stream",
            file_size=len(content),
            owner_id=current_user.id,
            meta=metadata or {},
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Ingest document asynchronously
        asyncio.create_task(
            ingest_document_async(document.id, content, db)
        )
        
        logger.info(
            f"Document uploaded: {document.id} ({file.filename}) by user: {current_user.id}"
        )
        
        return DocumentResponse(**document.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create document from URL/content",
    description="Create a document from raw content or URL"
)
def create_document(
    request: DocumentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a document from raw content.
    
    Request Body:
        title: Document title
        content: Document content
        source_url: Optional source URL
        metadata: Optional metadata dictionary
    
    Returns:
        DocumentResponse: Created document information
    """
    try:
        document = Document(
            id=f"doc_{int(datetime.now().timestamp() * 1000)}",
            title=request.title,
            name=request.title,
            file_path=f"content/{request.title}",
            document_type="text",
            content_type="text/plain",
            file_size=len(request.content),
            owner_id=current_user.id,
            meta=request.metadata or {},
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Ingest document
        asyncio.create_task(
            ingest_document_async(document.id, request.content.encode(), db)
        )
        
        logger.info(
            f"Document created: {document.id} ({request.title}) by user: {current_user.id}"
        )
        
        return DocumentResponse(**document.to_dict())
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document"
        )


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="List documents",
    description="Retrieve all ingested documents"
)
def list_documents(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all documents with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 50)
    
    Returns:
        List[DocumentResponse]: List of documents
    """
    try:
        documents = db.query(Document).offset(skip).limit(limit).all()
        
        logger.info(
            f"Retrieved {len(documents)} documents for user: {current_user.id}"
        )
        
        return [DocumentResponse(**d.to_dict()) for d in documents]
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
    description="Retrieve details of a specific document"
)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get details of a specific document.
    
    Path Parameters:
        document_id: ID of the document
    
    Returns:
        DocumentResponse: Document details
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        logger.info(
            f"Retrieved document: {document_id} for user: {current_user.id}"
        )
        
        return DocumentResponse(**document.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Delete a document and its embeddings"
)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a document and remove its embeddings from vector DB.
    
    Path Parameters:
        document_id: ID of the document to delete
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        db.delete(document)
        db.commit()
        
        logger.info(
            f"Deleted document: {document_id} by user: {current_user.id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.get(
    "/{document_id}/chunks",
    response_model=List[dict],
    summary="Get document chunks",
    description="Retrieve vector store chunks for a document"
)
def get_document_chunks(
    document_id: str,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all chunks for a document.
    
    Path Parameters:
        document_id: ID of the document
    
    Query Parameters:
        skip: Number of chunks to skip (default: 0)
        limit: Maximum chunks to return (default: 20)
    
    Returns:
        List[dict]: List of document chunks with metadata
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get chunks from vector database
        from app.db.vector import vector_client
        chunks = vector_client.scroll(
            collection_name=settings.RAG_COLLECTION,
            scroll_filter={"document_id": document_id},
            limit=limit,
            offset=skip,
        )
        
        logger.info(
            f"Retrieved chunks for document: {document_id}"
        )
        
        return chunks
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chunks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chunks"
        )


# Helper function for async ingestion
async def ingest_document_async(document_id: str, content: bytes, db: Session):
    """Background task to ingest document"""
    try:
        # Parse content based on file type
        from app.rag.chunker import chunk_content
        from app.rag.embedding import generate_embeddings
        
        # Extract text from content
        text_content = content.decode('utf-8', errors='ignore')
        
        # Chunk the content
        chunks = chunk_content(text_content, metadata={"document_id": document_id})
        
        # Generate embeddings and store
        for chunk in chunks:
            embedding = generate_embeddings(chunk['text'])
            # Store in vector database
            ingest_document(chunk, embedding)
        
        logger.info(f"Document {document_id} ingestion completed")
    except Exception as e:
        logger.error(f"Error ingesting document {document_id}: {str(e)}")

