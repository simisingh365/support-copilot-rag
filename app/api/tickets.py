"""
Ticket management API endpoints.

Provides:
- POST /api/tickets - Create a new ticket
- GET /api/tickets - List all tickets
- GET /api/tickets/{ticket_id}/messages - Get ticket messages
- POST /api/tickets/{ticket_id}/messages - Add message to ticket
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.db.models import Message, MessageRole, Ticket, TicketPriority, TicketStatus
from app.db.session import Session, get_db

# Create router
router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


class CreateTicketRequest(BaseModel):
    """
    Request model for creating a ticket.
    
    Attributes:
        subject: Ticket subject (required).
        content: Ticket content (required).
        priority: Ticket priority (default: MEDIUM).
        customer_id: Optional customer ID.
    """
    subject: str = Field(..., min_length=1, description="Ticket subject")
    content: str = Field(..., min_length=1, description="Ticket content")
    priority: str = Field(default="MEDIUM", description="Ticket priority")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    
    @field_validator("subject", "content")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that field is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority value."""
        valid_priorities = [p.value for p in TicketPriority]
        if v.upper() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v.upper()


class CreateMessageRequest(BaseModel):
    """
    Request model for creating a message.
    
    Attributes:
        role: Message role (USER, ASSISTANT, or SYSTEM).
        content: Message content (required).
    """
    role: str = Field(..., description="Message role: USER, ASSISTANT, or SYSTEM")
    content: str = Field(..., min_length=1, description="Message content")
    
    @field_validator("content")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that content is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role value."""
        valid_roles = [r.value for r in MessageRole]
        if v.upper() not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v.upper()


class TicketResponse(BaseModel):
    """
    Response model for a ticket.
    
    Attributes:
        id: Ticket ID.
        subject: Ticket subject.
        content: Ticket content.
        status: Ticket status.
        priority: Ticket priority.
        customer_id: Customer ID.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """
    id: str
    subject: str
    content: str
    status: str
    priority: str
    customer_id: Optional[str]
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """
    Response model for a message.
    
    Attributes:
        id: Message ID.
        ticket_id: Ticket ID.
        role: Message role.
        content: Message content.
        created_at: Creation timestamp.
    """
    id: str
    ticket_id: str
    role: str
    content: str
    created_at: str


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: CreateTicketRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new support ticket.
    
    Args:
        request: The ticket creation request.
        db: Database session.
    
    Returns:
        TicketResponse: The created ticket.
    
    Raises:
        HTTPException: If ticket creation fails.
    
    Example:
        ```json
        {
            "subject": "Issue with API",
            "content": "I'm having trouble with the API...",
            "priority": "HIGH",
            "customer_id": "cust_123"
        }
        ```
    """
    try:
        ticket_id = str(uuid.uuid4())
        
        ticket = Ticket(
            id=ticket_id,
            subject=request.subject,
            content=request.content,
            status=TicketStatus.OPEN.value,
            priority=request.priority,
            customer_id=request.customer_id
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        return TicketResponse(
            id=ticket.id,
            subject=ticket.subject,
            content=ticket.content,
            status=ticket.status,
            priority=ticket.priority,
            customer_id=ticket.customer_id,
            created_at=ticket.created_at.isoformat(),
            updated_at=ticket.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ticket: {str(e)}"
        )


@router.get("/", response_model=List[TicketResponse], status_code=status.HTTP_200_OK)
async def list_tickets(
    db: Session = Depends(get_db)
):
    """
    List all support tickets.
    
    Args:
        db: Database session.
    
    Returns:
        List[TicketResponse]: List of all tickets.
    
    Raises:
        HTTPException: If listing fails.
    """
    try:
        tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
        
        return [
            TicketResponse(
                id=ticket.id,
                subject=ticket.subject,
                content=ticket.content,
                status=ticket.status,
                priority=ticket.priority,
                customer_id=ticket.customer_id,
                created_at=ticket.created_at.isoformat(),
                updated_at=ticket.updated_at.isoformat()
            )
            for ticket in tickets
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tickets: {str(e)}"
        )


@router.get("/{ticket_id}", response_model=TicketResponse, status_code=status.HTTP_200_OK)
async def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific ticket by ID.
    
    Args:
        ticket_id: The ticket ID.
        db: Database session.
    
    Returns:
        TicketResponse: The ticket details.
    
    Raises:
        HTTPException: If ticket not found or retrieval fails.
    """
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket with ID '{ticket_id}' not found."
            )
        
        return TicketResponse(
            id=ticket.id,
            subject=ticket.subject,
            content=ticket.content,
            status=ticket.status,
            priority=ticket.priority,
            customer_id=ticket.customer_id,
            created_at=ticket.created_at.isoformat(),
            updated_at=ticket.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ticket: {str(e)}"
        )


@router.get("/{ticket_id}/messages", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
async def get_ticket_messages(
    ticket_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all messages for a specific ticket.
    
    Args:
        ticket_id: The ticket ID.
        db: Database session.
    
    Returns:
        List[MessageResponse]: List of messages for the ticket.
    
    Raises:
        HTTPException: If ticket not found or retrieval fails.
    """
    try:
        # Verify ticket exists
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket with ID '{ticket_id}' not found."
            )
        
        messages = db.query(Message).filter(
            Message.ticket_id == ticket_id
        ).order_by(Message.created_at.asc()).all()
        
        return [
            MessageResponse(
                id=message.id,
                ticket_id=message.ticket_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at.isoformat()
            )
            for message in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ticket messages: {str(e)}"
        )


@router.post("/{ticket_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_ticket_message(
    ticket_id: str,
    request: CreateMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Add a message to a ticket.
    
    Args:
        ticket_id: The ticket ID.
        request: The message creation request.
        db: Database session.
    
    Returns:
        MessageResponse: The created message.
    
    Raises:
        HTTPException: If ticket not found or message creation fails.
    
    Example:
        ```json
        {
            "role": "USER",
            "content": "I need help with..."
        }
        ```
    """
    try:
        # Verify ticket exists
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket with ID '{ticket_id}' not found."
            )
        
        message_id = str(uuid.uuid4())
        
        message = Message(
            id=message_id,
            ticket_id=ticket_id,
            role=request.role,
            content=request.content
        )
        
        db.add(message)
        
        # Update ticket's updated_at timestamp
        from sqlalchemy import func
        ticket.updated_at = func.utcnow()
        
        db.commit()
        db.refresh(message)
        
        return MessageResponse(
            id=message.id,
            ticket_id=message.ticket_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )


@router.patch("/{ticket_id}/status", status_code=status.HTTP_200_OK)
async def update_ticket_status(
    ticket_id: str,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update the status of a ticket.
    
    Args:
        ticket_id: The ticket ID.
        status: The new status (OPEN, IN_PROGRESS, RESOLVED, CLOSED).
        db: Database session.
    
    Returns:
        dict: Success message.
    
    Raises:
        HTTPException: If ticket not found or update fails.
    """
    try:
        # Validate status
        valid_statuses = [s.value for s in TicketStatus]
        if status.upper() not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Get ticket
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket with ID '{ticket_id}' not found."
            )
        
        # Update status
        ticket.status = status.upper()
        db.commit()
        
        return {
            "success": True,
            "message": f"Ticket status updated to {status.upper()}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ticket status: {str(e)}"
        )
