from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.deps import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.ticket import Ticket
from app.models.conversation import Conversation
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketResponse,
    TicketUpdateRequest,
)
from app.actions.escalation import escalate_ticket


router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ticket",
    description="Create a support escalation ticket"
)
def create_ticket(
    request: TicketCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new support ticket.
    
    Request Body:
        conversation_id: ID of associated conversation
        title: Ticket title
        description: Detailed description
        priority: Priority level (low, medium, high, critical)
        category: Issue category
    
    Returns:
        TicketResponse: Created ticket
    """
    try:
        # Verify conversation exists and belongs to user
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Create ticket
        ticket = Ticket(
            conversation_id=request.conversation_id,
            created_by_id=current_user.id,
            title=request.title,
            description=request.description,
            priority=request.priority,
            category=request.category,
            status="OPEN",
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        logger.info(
            f"Ticket created: {ticket.id} (priority: {request.priority}) "
            f"by user: {current_user.id}"
        )
        
        return TicketResponse.from_orm(ticket)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ticket"
        )


@router.get(
    "",
    response_model=List[TicketResponse],
    summary="List tickets",
    description="Retrieve all tickets for current user"
)
def list_tickets(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all tickets for the current user with filters.
    
    Query Parameters:
        status_filter: Filter by status (open, in_progress, resolved, closed)
        priority_filter: Filter by priority (low, medium, high, critical)
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 50)
    
    Returns:
        List[TicketResponse]: List of tickets
    """
    try:
        query = db.query(Ticket).filter(Ticket.created_by_id == current_user.id)
        
        if status_filter:
            query = query.filter(Ticket.status == status_filter.upper())
        
        if priority_filter:
            query = query.filter(Ticket.priority == priority_filter.upper())
        
        tickets = query.offset(skip).limit(limit).all()
        
        logger.info(
            f"Retrieved {len(tickets)} tickets for user: {current_user.id}"
        )
        
        return [TicketResponse.from_orm(t) for t in tickets]
    except Exception as e:
        logger.error(f"Error retrieving tickets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tickets"
        )


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Get ticket",
    description="Retrieve ticket details"
)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get details of a specific ticket.
    
    Path Parameters:
        ticket_id: ID of the ticket
    
    Returns:
        TicketResponse: Ticket details
    """
    try:
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.created_by_id == current_user.id
        ).first()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        logger.info(
            f"Retrieved ticket: {ticket_id} by user: {current_user.id}"
        )
        
        return TicketResponse.from_orm(ticket)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket"
        )


@router.put(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Update ticket",
    description="Update ticket details"
)
def update_ticket(
    ticket_id: int,
    request: TicketUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a ticket.
    
    Path Parameters:
        ticket_id: ID of the ticket
    
    Request Body:
        title: Updated title (optional)
        description: Updated description (optional)
        status: Updated status (optional)
        priority: Updated priority (optional)
        assigned_to_id: Assigned agent ID (optional)
    
    Returns:
        TicketResponse: Updated ticket
    """
    try:
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.created_by_id == current_user.id
        ).first()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Update fields
        if request.title is not None:
            ticket.title = request.title
        
        if request.description is not None:
            ticket.description = request.description
        
        if request.status is not None:
            ticket.status = request.status
        
        if request.priority is not None:
            ticket.priority = request.priority
        
        if request.assigned_to_id is not None:
            # Verify agent exists
            agent = db.query(User).filter(User.id == request.assigned_to_id).first()
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            ticket.assigned_to_id = request.assigned_to_id
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        logger.info(
            f"Updated ticket: {ticket_id} by user: {current_user.id}"
        )
        
        return TicketResponse.from_orm(ticket)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket"
        )


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ticket",
    description="Delete a ticket"
)
def delete_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a ticket.
    
    Path Parameters:
        ticket_id: ID of the ticket
    """
    try:
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.created_by_id == current_user.id
        ).first()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        db.delete(ticket)
        db.commit()
        
        logger.info(
            f"Deleted ticket: {ticket_id} by user: {current_user.id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete ticket"
        )


@router.post(
    "/{ticket_id}/escalate",
    status_code=status.HTTP_200_OK,
    summary="Escalate ticket",
    description="Escalate a ticket to higher support level"
)
def escalate_ticket(
    ticket_id: int,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Escalate a ticket.
    
    Path Parameters:
        ticket_id: ID of the ticket
    
    Request Body:
        reason: Reason for escalation
    
    Returns:
        dict: Success message
    """
    try:
        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.created_by_id == current_user.id
        ).first()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Update ticket status
        ticket.status = "ESCALATED"
        db.add(ticket)
        db.commit()
        
        logger.info(
            f"Escalated ticket: {ticket_id}, reason: {reason}, "
            f"by user: {current_user.id}"
        )
        
        return {
            "message": "Ticket escalated successfully",
            "ticket_id": ticket_id,
            "new_status": "ESCALATED"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error escalating ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to escalate ticket"
        )


@router.get(
    "/stats/summary",
    response_model=dict,
    summary="Get ticket statistics",
    description="Get ticket statistics for current user"
)
def get_ticket_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get ticket statistics.
    
    Returns:
        dict: Ticket statistics
    """
    try:
        tickets = db.query(Ticket).filter(
            Ticket.created_by_id == current_user.id
        ).all()
        
        open_count = len([t for t in tickets if t.status == "OPEN"])
        in_progress_count = len([t for t in tickets if t.status == "IN_PROGRESS"])
        resolved_count = len([t for t in tickets if t.status == "RESOLVED"])
        closed_count = len([t for t in tickets if t.status == "CLOSED"])
        
        critical_count = len([t for t in tickets if t.priority == "CRITICAL"])
        high_count = len([t for t in tickets if t.priority == "HIGH"])
        
        logger.info(
            f"Retrieved ticket statistics for user: {current_user.id}"
        )
        
        return {
            "total_tickets": len(tickets),
            "open": open_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "closed": closed_count,
            "critical_priority": critical_count,
            "high_priority": high_count,
            "average_priority": (critical_count * 4 + high_count * 3) / len(tickets) if tickets else 0,
        }
    except Exception as e:
        logger.error(f"Error retrieving ticket stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket statistics"
        )
