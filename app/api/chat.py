from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.deps import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationResponse,
    ConversationCreateRequest,
)
from app.actions.engine import process_user_message


router = APIRouter(prefix="/api/chat", tags=["chat"])


# -------------------------------------------------
# CONVERSATION ENDPOINTS
# -------------------------------------------------


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    description="Start a new chat conversation session"
)
def create_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new conversation for the current user.
    
    Returns:
        ConversationResponse: The created conversation with metadata
    """
    try:
        conversation = Conversation(
            user_id=current_user.id,
            status="OPEN"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        logger.info(
            f"Conversation created: {conversation.id} for user: {current_user.id}"
        )
        
        return ConversationResponse.from_orm(conversation)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.get(
    "/conversations",
    response_model=List[ConversationResponse],
    summary="Get user conversations",
    description="Retrieve all conversations for the current user"
)
def get_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all conversations for the current user with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 50)
    
    Returns:
        List[ConversationResponse]: List of conversations
    """
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).offset(skip).limit(limit).all()
        
        logger.info(
            f"Retrieved {len(conversations)} conversations for user: {current_user.id}"
        )
        
        return [ConversationResponse.from_orm(c) for c in conversations]
    except Exception as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation details",
    description="Retrieve a specific conversation with all messages"
)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get details of a specific conversation.
    
    Path Parameters:
        conversation_id: ID of the conversation
    
    Returns:
        ConversationResponse: Conversation details with all messages
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        logger.info(
            f"Retrieved conversation: {conversation_id} for user: {current_user.id}"
        )
        
        return ConversationResponse.from_orm(conversation)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete a conversation and all its messages"
)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a specific conversation.
    
    Path Parameters:
        conversation_id: ID of the conversation to delete
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        db.delete(conversation)
        db.commit()
        
        logger.info(
            f"Deleted conversation: {conversation_id} for user: {current_user.id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


# -------------------------------------------------
# MESSAGE ENDPOINTS
# -------------------------------------------------


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
    description="Send a message in a conversation and get AI response"
)
def send_message(
    conversation_id: int,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message in a conversation.
    
    The system will:
    1. Analyze sentiment
    2. Retrieve relevant context from RAG
    3. Generate AI response
    4. Run escalation checks
    5. Log the exchange
    
    Path Parameters:
        conversation_id: ID of the conversation
    
    Request Body:
        content: Message content
    
    Returns:
        ChatMessageResponse: User message + AI response with metadata
    """
    try:
        # Verify conversation ownership
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Process the message through the engine
        result = process_user_message(
            db=db,
            conversation=conversation,
            user_id=current_user.id,
            content=request.content
        )
        
        logger.info(
            f"Message processed in conversation: {conversation_id}, "
            f"user: {current_user.id}, sentiment: {result['sentiment']}"
        )
        
        return ChatMessageResponse(
            user_message=result['user_message'],
            bot_response=result['bot_response'],
            sentiment_score=result['sentiment'],
            requires_escalation=result.get('requires_escalation', False),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[ChatMessageResponse],
    summary="Get conversation messages",
    description="Retrieve all messages in a conversation"
)
def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all messages in a conversation with pagination.
    
    Path Parameters:
        conversation_id: ID of the conversation
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 100)
    
    Returns:
        List[ChatMessageResponse]: List of messages
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).offset(skip).limit(limit).all()
        
        logger.info(
            f"Retrieved {len(messages)} messages from conversation: {conversation_id}"
        )
        
        return [ChatMessageResponse.from_orm(m) for m in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )


@router.delete(
    "/conversations/{conversation_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete message",
    description="Delete a specific message from a conversation"
)
def delete_message(
    conversation_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a specific message from a conversation.
    
    Path Parameters:
        conversation_id: ID of the conversation
        message_id: ID of the message to delete
    """
    try:
        # Verify conversation ownership
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        message = db.query(Message).filter(
            Message.id == message_id,
            Message.conversation_id == conversation_id
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        db.delete(message)
        db.commit()
        
        logger.info(
            f"Deleted message: {message_id} from conversation: {conversation_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )
