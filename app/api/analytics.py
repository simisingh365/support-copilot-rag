"""
Analytics API endpoint.

Provides:
- GET /api/analytics/overview - Get system analytics overview
"""

from typing import Dict

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.models import RAGQuery
from app.db.session import Session, get_db

# Create router
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", status_code=status.HTTP_200_OK)
async def get_analytics_overview(
    db: Session = Depends(get_db)
):
    """
    Get analytics overview for the RAG system.
    
    This endpoint calculates and returns:
    - Total number of queries
    - Average retrieval time
    - Average response time
    - Retrieval method distribution
    
    Args:
        db: Database session.
    
    Returns:
        dict: Analytics metrics.
    
    Raises:
        HTTPException: If analytics calculation fails.
    """
    try:
        # Query all RAG queries
        queries = db.query(RAGQuery).all()
        
        if not queries:
            # Return zeros for empty database
            return {
                "total_queries": 0,
                "avg_retrieval_time_ms": 0.0,
                "avg_response_time_ms": 0.0,
                "avg_total_time_ms": 0.0,
                "retrieval_distribution": {},
                "queries_per_day": {}
            }
        
        # Convert to DataFrame for analysis
        data = []
        for query in queries:
            data.append({
                "id": query.id,
                "query_text": query.query_text,
                "retrieval_time": query.retrieval_time or 0,
                "response_time": query.response_time or 0,
                "retrieval_method": query.retrieval_method,
                "num_chunks": query.num_chunks or 0,
                "created_at": query.created_at
            })
        
        df = pd.DataFrame(data)
        
        # Calculate metrics
        total_queries = len(df)
        avg_retrieval_time = float(df["retrieval_time"].mean()) if total_queries > 0 else 0.0
        avg_response_time = float(df["response_time"].mean()) if total_queries > 0 else 0.0
        avg_total_time = avg_retrieval_time + avg_response_time
        
        # Retrieval method distribution
        retrieval_distribution = df["retrieval_method"].value_counts().to_dict()
        
        # Queries per day
        df["date"] = pd.to_datetime(df["created_at"]).dt.date
        queries_per_day = df.groupby("date").size().to_dict()
        queries_per_day = {str(k): int(v) for k, v in queries_per_day.items()}
        
        return {
            "total_queries": total_queries,
            "avg_retrieval_time_ms": round(avg_retrieval_time, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "avg_total_time_ms": round(avg_total_time, 2),
            "retrieval_distribution": retrieval_distribution,
            "queries_per_day": queries_per_day
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/queries", status_code=status.HTTP_200_OK)
async def get_queries(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get recent RAG queries.
    
    Args:
        limit: Maximum number of queries to return. Default: 100.
        db: Database session.
    
    Returns:
        list: List of recent queries.
    
    Raises:
        HTTPException: If retrieval fails.
    """
    try:
        if limit <= 0 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000"
            )
        
        queries = db.query(RAGQuery).order_by(
            RAGQuery.created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "id": query.id,
                "query_text": query.query_text,
                "answer": query.answer[:200] + "..." if query.answer and len(query.answer) > 200 else query.answer,
                "retrieval_time_ms": query.retrieval_time,
                "response_time_ms": query.response_time,
                "num_chunks": query.num_chunks,
                "created_at": query.created_at.isoformat()
            }
            for query in queries
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queries: {str(e)}"
        )


@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_system_stats(
    db: Session = Depends(get_db)
):
    """
    Get system statistics.
    
    Returns counts for various entities in the system.
    
    Args:
        db: Database session.
    
    Returns:
        dict: System statistics.
    
    Raises:
        HTTPException: If retrieval fails.
    """
    try:
        from app.db.models import Ticket, Message, KnowledgeDocument, KnowledgeChunk
        
        stats = {
            "tickets": db.query(Ticket).count(),
            "messages": db.query(Message).count(),
            "documents": db.query(KnowledgeDocument).count(),
            "chunks": db.query(KnowledgeChunk).count(),
            "queries": db.query(RAGQuery).count()
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )
