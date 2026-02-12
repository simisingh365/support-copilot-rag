"""
RAG API endpoint for querying the RAG system.

Provides:
- POST /api/rag/query endpoint for RAG queries
"""

import logging
import traceback
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.embeddings import EmbeddingGenerator
from app.core.rag import RAGChain
from app.core.retrieval import RetrievalEngine
from app.db.models import RAGQuery
from app.db.session import Session, get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/rag", tags=["RAG"])

# Initialize core components at module level
embedding_generator = EmbeddingGenerator()
retrieval_engine = RetrievalEngine(embedding_generator)
rag_chain = RAGChain(retrieval_engine)


class RAGQueryRequest(BaseModel):
    """
    Request model for RAG query endpoint.
    
    Attributes:
        query: The user's question (required).
        ticket_id: Optional ticket ID to associate with the query.
        k: Number of context chunks to retrieve (default: 5, range: 1-10).
    """
    query: str = Field(..., min_length=1, description="The user's question")
    ticket_id: Optional[str] = Field(None, description="Optional ticket ID")
    k: int = Field(default=5, ge=1, le=10, description="Number of context chunks to retrieve")
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate that query is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class RAGQueryResponse(BaseModel):
    """
    Response model for RAG query endpoint.
    
    Attributes:
        answer: The generated answer.
        sources: List of source information.
        citations: List of citation references.
        metrics: Performance metrics.
        query_id: Unique ID for the query.
    """
    answer: str
    sources: list
    citations: list
    metrics: dict
    query_id: str


@router.post("/query", response_model=RAGQueryResponse, status_code=status.HTTP_200_OK)
async def query_rag(
    request: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query the RAG system and generate an answer.

    This endpoint:
    1. Retrieves relevant chunks from the knowledge base
    2. Generates an answer using OpenAI with retrieved context
    3. Returns the answer with sources, citations, and metrics
    4. Saves the query to the database for analytics

    Args:
        request: The RAG query request.
        db: Database session.

    Returns:
        RAGQueryResponse: The generated answer with metadata.

    Raises:
        HTTPException: If the query fails.

    Example:
        ```json
        {
            "query": "What is the refund policy?",
            "k": 5
        }
        ```
    """
    query_id = str(uuid.uuid4())
    logger.info(f"Received RAG query: {request.query[:100]}... (k={request.k})")

    try:
        # Call RAG chain
        logger.info("Calling RAG chain...")
        result = await rag_chain.query_with_ticket(
            query_text=request.query,
            k=request.k,
            ticket_id=request.ticket_id
        )
        logger.info(f"RAG chain returned result with {len(result.get('sources', []))} sources")

        # Save query to database
        rag_query = RAGQuery(
            id=query_id,
            query_text=request.query,
            answer=result["answer"],
            sources=result["sources"],
            citations=result["citations"],
            retrieval_method="SEMANTIC",
            retrieval_time=result["metrics"]["retrieval_time_ms"],
            response_time=result["metrics"]["response_time_ms"],
            num_chunks=result["metrics"]["num_chunks_retrieved"],
            ticket_id=request.ticket_id
        )

        db.add(rag_query)
        db.commit()
        logger.info(f"Query saved to database with ID: {query_id}")

        # Return response
        return RAGQueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            citations=result["citations"],
            metrics=result["metrics"],
            query_id=query_id
        )

    except ValueError as e:
        logger.error(f"ValueError in RAG query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Exception in RAG query: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process RAG query: {str(e)}"
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for the RAG API.
    
    Returns:
        dict: Health status information.
    """
    try:
        collection_count = retrieval_engine.get_collection_count()
        return {
            "status": "healthy",
            "collection_name": retrieval_engine.collection_name,
            "collection_count": collection_count,
            "model": rag_chain.model
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )
