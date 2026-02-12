"""
Main FastAPI application for the RAG Customer Support System.

Provides:
- FastAPI app with CORS middleware
- All API routers included
- Root endpoint with API information
"""
import logging
import sys
import traceback
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analytics, knowledge, rag, tickets
from app.db.session import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    
    Initializes the database on startup.
    """
    # Startup
    print("Starting RAG Customer Support System...")
    init_db()
    print("Database initialized.")
    print("API is ready to accept requests.")
    
    yield
    
    # Shutdown
    print("Shutting down RAG Customer Support System...")


# Create FastAPI application
app = FastAPI(
    title="RAG Customer Support System",
    description="A Retrieval-Augmented Generation system for customer support with knowledge base management.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(rag.router)
app.include_router(knowledge.router)
app.include_router(tickets.router)
app.include_router(analytics.router)


# Global exception handler for detailed error logging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to log all exceptions with full details.
    """
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    logger.error(f"Request path: {request.url.path}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {type(exc).__name__}: {str(exc)}",
            "path": request.url.path,
            "method": request.method
        }
    )


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        dict: API information including message, docs URL, and available endpoints.
    """
    return {
        "message": "Welcome to the RAG Customer Support System API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "rag": {
                "query": "/api/rag/query",
                "health": "/api/rag/health"
            },
            "knowledge": {
                "ingest": "/api/knowledge/ingest",
                "documents": "/api/knowledge/documents",
                "document_detail": "/api/knowledge/documents/{document_id}",
                "delete_document": "/api/knowledge/documents/{document_id}"
            },
            "tickets": {
                "create": "/api/tickets/",
                "list": "/api/tickets/",
                "get": "/api/tickets/{ticket_id}",
                "messages": "/api/tickets/{ticket_id}/messages",
                "add_message": "/api/tickets/{ticket_id}/messages",
                "update_status": "/api/tickets/{ticket_id}/status"
            },
            "analytics": {
                "overview": "/api/analytics/overview",
                "queries": "/api/analytics/queries",
                "stats": "/api/analytics/stats"
            }
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status.
    """
    return {
        "status": "healthy",
        "service": "RAG Customer Support System",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
