"""
SQLAlchemy database models for the RAG Customer Support System.

Models:
- Ticket: Customer support tickets
- Message: Chat messages for tickets
- KnowledgeDocument: KB documents
- KnowledgeChunk: Document chunks with embeddings
- RAGQuery: RAG query tracking with metrics
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class TicketStatus(str, Enum):
    """Ticket status enumeration."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketPriority(str, Enum):
    """Ticket priority enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class RetrievalMethod(str, Enum):
    """Retrieval method enumeration."""
    SEMANTIC = "SEMANTIC"
    HYBRID = "HYBRID"


class Ticket(Base):
    """
    Customer support ticket model.
    
    Represents a customer support ticket with subject, content, status,
    priority, and customer information.
    """
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), 
        default=TicketStatus.OPEN.value, 
        nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(20), 
        default=TicketPriority.MEDIUM.value, 
        nullable=False
    )
    customer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationship with messages
    messages: Mapped[list["Message"]] = relationship(
        "Message", 
        back_populates="ticket", 
        cascade="all, delete-orphan"
    )
    
    # Relationship with RAG queries
    rag_queries: Mapped[list["RAGQuery"]] = relationship(
        "RAGQuery", 
        back_populates="ticket"
    )

    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, subject='{self.subject}', status={self.status})>"


class Message(Base):
    """
    Chat message model for tickets.
    
    Represents individual messages within a ticket conversation.
    """
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("tickets.id", ondelete="CASCADE"), 
        nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        nullable=False
    )

    # Relationship with ticket
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, ticket_id={self.ticket_id}, role={self.role})>"


class KnowledgeDocument(Base):
    """
    Knowledge base document model.
    
    Represents a document in the knowledge base that can be chunked
    and used for RAG retrieval.
    """
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationship with chunks
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", 
        back_populates="document", 
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeDocument(id={self.id}, title='{self.title}', chunk_count={self.chunk_count})>"


class KnowledgeChunk(Base):
    """
    Document chunk model with embeddings.
    
    Represents a chunk of a knowledge document with its embedding
    vector for semantic search.
    """
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"), 
        nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list[float]]] = mapped_column(JSON, nullable=True)
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        nullable=False
    )

    # Relationship with document
    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument", 
        back_populates="chunks"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class RAGQuery(Base):
    """
    RAG query tracking model with metrics.
    
    Tracks all RAG queries with performance metrics and results.
    """
    __tablename__ = "rag_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sources: Mapped[Optional[list[dict]]] = mapped_column(JSON, nullable=True)
    citations: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    retrieval_method: Mapped[str] = mapped_column(
        String(20), 
        default=RetrievalMethod.SEMANTIC.value, 
        nullable=False
    )
    retrieval_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    num_chunks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ticket_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        ForeignKey("tickets.id", ondelete="SET NULL"), 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        nullable=False
    )

    # Relationship with ticket
    ticket: Mapped[Optional["Ticket"]] = relationship("Ticket", back_populates="rag_queries")

    def __repr__(self) -> str:
        return f"<RAGQuery(id={self.id}, query_text='{self.query_text[:50]}...', retrieval_time={self.retrieval_time})>"
