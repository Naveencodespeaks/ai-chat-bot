"""
Document Schema Definitions

Request and response models for document upload, management, and retrieval endpoints.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents a chunk of a document for RAG."""
    
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk text content")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    chunk_order: int = Field(..., description="Sequential order of chunk in document")
    metadata: dict = Field(default_factory=dict, description="Chunk-specific metadata")


class DocumentUploadRequest(BaseModel):
    """Request body for document upload."""
    
    title: Optional[str] = Field(None, description="Document title (auto-extracted if not provided)")
    tags: Optional[List[str]] = Field(default_factory=list, description="Document tags for categorization")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Policy Document",
                "tags": ["policy", "customer-service"],
                "metadata": {"source": "internal", "version": "1.0"}
            }
        }


class DocumentCreateRequest(BaseModel):
    """Request body for creating document from text content."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., min_length=1, description="Document text content")
    document_type: Optional[str] = Field("text", description="Document type (text, markdown, code, etc.)")
    tags: Optional[List[str]] = Field(default_factory=list, description="Document tags")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Support Policy",
                "content": "Our support team operates 24/7...",
                "document_type": "text",
                "tags": ["policy", "support"],
                "metadata": {"priority": "high"}
            }
        }


class DocumentResponse(BaseModel):
    """Response model for document."""
    
    id: str = Field(..., description="Document ID")
    owner_id: str = Field(..., description="User ID of document owner")
    title: str = Field(..., description="Document title")
    file_path: Optional[str] = Field(None, description="Path to stored document file")
    document_type: str = Field(..., description="Type of document")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    page_count: Optional[int] = Field(None, description="Number of pages")
    chunk_count: int = Field(default=0, description="Number of chunks created")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    metadata: dict = Field(default_factory=dict, description="Document metadata")
    is_processed: bool = Field(default=False, description="Whether document is processed and indexed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "doc_123",
                "owner_id": "user_456",
                "title": "Support Policy",
                "file_path": "/storage/documents/doc_123.pdf",
                "document_type": "pdf",
                "file_size": 102400,
                "page_count": 5,
                "chunk_count": 15,
                "tags": ["policy", "support"],
                "metadata": {"source": "internal"},
                "is_processed": True,
                "created_at": "2026-02-14T10:00:00Z",
                "updated_at": "2026-02-14T10:05:00Z"
            }
        }


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Documents per page")
    documents: List[DocumentResponse] = Field(..., description="List of documents")


class DocumentDeleteResponse(BaseModel):
    """Response model for document deletion."""
    
    message: str = Field(..., description="Deletion status message")
    deleted_count: int = Field(..., description="Number of deleted documents/chunks")
    document_id: str = Field(..., description="ID of deleted document")


class DocumentChunkResponse(BaseModel):
    """Response model for document chunks."""
    
    document_id: str = Field(..., description="Document ID")
    chunk_count: int = Field(..., description="Total chunks")
    chunks: List[DocumentChunk] = Field(..., description="List of document chunks")


class DocumentSearchRequest(BaseModel):
    """Request body for document search."""
    
    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    document_id: Optional[str] = Field(None, description="Filter by specific document")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")


class DocumentSearchResult(BaseModel):
    """Single search result for document content."""
    
    document_id: str = Field(..., description="Source document ID")
    title: str = Field(..., description="Document title")
    chunk_id: str = Field(..., description="Chunk ID that matched")
    content: str = Field(..., description="Matched chunk content")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score (0-1)")
    page_number: Optional[int] = Field(None, description="Page number if applicable")


class DocumentSearchResponse(BaseModel):
    """Response model for document search results."""
    
    query: str = Field(..., description="Search query")
    result_count: int = Field(..., description="Number of results")
    results: List[DocumentSearchResult] = Field(..., description="Search results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "customer service policy",
                "result_count": 3,
                "results": [
                    {
                        "document_id": "doc_123",
                        "title": "Support Policy",
                        "chunk_id": "chunk_5",
                        "content": "Our customer service team...",
                        "relevance_score": 0.95,
                        "page_number": 2
                    }
                ]
            }
        }


class DocumentBatchDeleteRequest(BaseModel):
    """Request body for batch delete documents."""
    
    document_ids: List[str] = Field(..., min_items=1, description="List of document IDs to delete")


class DocumentBatchDeleteResponse(BaseModel):
    """Response model for batch delete."""
    
    message: str = Field(..., description="Operation status")
    deleted_count: int = Field(..., description="Number of documents deleted")
    failed_count: int = Field(..., description="Number of deletions that failed")
    failed_ids: List[str] = Field(default_factory=list, description="IDs that failed to delete")


class DocumentIngestionStatus(BaseModel):
    """Status of document ingestion process."""
    
    document_id: str = Field(..., description="Document ID")
    status: str = Field(..., description="Status: pending, processing, completed, failed")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    chunks_processed: int = Field(default=0, description="Chunks processed so far")
    total_chunks: Optional[int] = Field(None, description="Total chunks to process")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: datetime = Field(..., description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    class Config:
        from_attributes = True
 
