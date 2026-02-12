"""
Knowledge management API endpoints.

Provides:
- POST /api/knowledge/ingest - Ingest a document into the knowledge base
- GET /api/knowledge/documents - List all documents in the knowledge base
"""

import logging
import traceback
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.chunking import Chunk, get_chunker
from app.core.embeddings import EmbeddingGenerator
from app.core.retrieval import RetrievalEngine
from app.db.models import KnowledgeChunk, KnowledgeDocument
from app.db.session import Session, get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])

# Initialize core components at module level
embedding_generator = EmbeddingGenerator()
retrieval_engine = RetrievalEngine(embedding_generator)


class IngestDocumentRequest(BaseModel):
    """
    Request model for document ingestion.
    
    Attributes:
        title: Document title (required).
        content: Document content (required).
        category: Optional document category.
        tags: Optional list of tags.
        chunking_strategy: Chunking strategy to use (default: "fixed_size").
    """
    title: str = Field(..., min_length=1, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    category: Optional[str] = Field(None, description="Document category")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    chunking_strategy: str = Field(
        default="fixed_size",
        description="Chunking strategy: 'fixed_size' or 'semantic'"
    )
    
    @field_validator("title", "content")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that field is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator("chunking_strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        """Validate chunking strategy."""
        if v not in ["fixed_size", "semantic"]:
            raise ValueError("chunking_strategy must be 'fixed_size' or 'semantic'")
        return v


class IngestDocumentResponse(BaseModel):
    """
    Response model for document ingestion.
    
    Attributes:
        success: Whether the ingestion was successful.
        document_id: The ID of the created document.
        chunks_count: Number of chunks created.
        message: Success message.
    """
    success: bool
    document_id: str
    chunks_count: int
    message: str


class DocumentResponse(BaseModel):
    """
    Response model for a document.
    
    Attributes:
        id: Document ID.
        title: Document title.
        category: Document category.
        tags: Document tags.
        chunk_count: Number of chunks.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """
    id: str
    title: str
    category: Optional[str]
    tags: Optional[List[str]]
    chunk_count: int
    created_at: str
    updated_at: str


@router.post("/ingest", response_model=IngestDocumentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    request: IngestDocumentRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest a document into the knowledge base.

    This endpoint:
    1. Creates a KnowledgeDocument record
    2. Chunks the document using the specified strategy
    3. Generates embeddings for each chunk
    4. Saves chunks to the database
    5. Adds chunks to ChromaDB for retrieval

    Args:
        request: The document ingestion request.
        db: Database session.

    Returns:
        IngestDocumentResponse: Success status with document ID and chunk count.

    Raises:
        HTTPException: If ingestion fails.

    Example:
        ```json
        {
            "title": "Refund Policy",
            "content": "Our refund policy allows...",
            "category": "Policies",
            "tags": ["refund", "policy"],
            "chunking_strategy": "fixed_size"
        }
        ```
    """
    document_id = str(uuid.uuid4())
    logger.info(f"Received ingest request for document: {request.title}")

    try:
        # Create document record
        logger.info("Creating document record...")
        document = KnowledgeDocument(
            id=document_id,
            title=request.title,
            content=request.content,
            category=request.category,
            tags={"tags": request.tags} if request.tags else None,
            chunk_count=0
        )

        db.add(document)
        db.flush()  # Get the document ID
        logger.info(f"Document record created with ID: {document_id}")

        # Chunk the document
        logger.info(f"Chunking document with strategy: {request.chunking_strategy}")
        chunker = get_chunker(request.chunking_strategy)
        chunks: List[Chunk] = chunker.chunk(request.content)

        if not chunks:
            raise ValueError("Document produced no chunks after chunking")

        logger.info(f"Document chunked into {len(chunks)} chunks")

        # Generate embeddings for all chunks
        logger.info("Generating embeddings for chunks...")
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = await embedding_generator.generate_embeddings(chunk_texts)
        logger.info(f"Generated {len(embeddings)} embeddings")

        # Save chunks to database
        logger.info("Saving chunks to database...")
        chunk_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)

            knowledge_chunk = KnowledgeChunk(
                id=chunk_id,
                document_id=document_id,
                chunk_index=i,
                content=chunk.text,
                embedding=embedding,
                chunk_metadata={
                    **chunk.metadata,
                    "document_id": document_id,
                    "document_title": request.title,
                    "category": request.category,
                    "tags": request.tags
                }
            )

            db.add(knowledge_chunk)

        # Update document chunk count
        document.chunk_count = len(chunks)

        # Add chunks to ChromaDB
        logger.info("Adding chunks to ChromaDB...")
        await retrieval_engine.add_documents(
            documents=chunk_texts,
            ids=chunk_ids,
            metadatas=[
                {
                    "document_id": document_id,
                    "document_title": request.title,
                    "category": request.category,
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]
        )
        logger.info("Chunks added to ChromaDB successfully")

        db.commit()
        logger.info(f"Document '{request.title}' ingested successfully")

        return IngestDocumentResponse(
            success=True,
            document_id=document_id,
            chunks_count=len(chunks),
            message=f"Document '{request.title}' ingested successfully with {len(chunks)} chunks."
        )

    except ValueError as e:
        logger.error(f"ValueError in document ingestion: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Exception in document ingestion: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )


@router.get("/documents", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
async def list_documents(
    db: Session = Depends(get_db)
):
    """
    List all documents in the knowledge base.
    
    Args:
        db: Database session.
    
    Returns:
        List[DocumentResponse]: List of all documents.
    
    Raises:
        HTTPException: If listing fails.
    """
    try:
        documents = db.query(KnowledgeDocument).all()
        
        return [
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                category=doc.category,
                tags=doc.tags.get("tags") if doc.tags else None,
                chunk_count=doc.chunk_count,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat()
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID.
    
    Args:
        document_id: The document ID.
        db: Database session.
    
    Returns:
        DocumentResponse: The document details.
    
    Raises:
        HTTPException: If document not found or retrieval fails.
    """
    try:
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found."
            )
        
        return DocumentResponse(
            id=document.id,
            title=document.title,
            category=document.category,
            tags=document.tags.get("tags") if document.tags else None,
            chunk_count=document.chunk_count,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document from the knowledge base.
    
    This will delete the document and all its chunks from both
    the database and ChromaDB.
    
    Args:
        document_id: The document ID.
        db: Database session.
    
    Returns:
        dict: Success message.
    
    Raises:
        HTTPException: If document not found or deletion fails.
    """
    try:
        # Get document
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found."
            )
        
        # Get all chunk IDs
        chunks = db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == document_id
        ).all()
        
        chunk_ids = [chunk.id for chunk in chunks]
        
        # Delete chunks from ChromaDB
        if chunk_ids:
            retrieval_engine.delete_documents(chunk_ids)
        
        # Delete document (chunks will be cascade deleted)
        db.delete(document)
        db.commit()
        
        return {
            "success": True,
            "message": f"Document '{document.title}' deleted successfully."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
