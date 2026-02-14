from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.deps import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.sentiment_log import SentimentLog
from app.models.conversation import Conversation
from app.schemas.sentiment import (
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    SentimentLogResponse,
)
from app.sentiment.analyzer import analyze_sentiment


router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


@router.post(
    "/analyze",
    response_model=SentimentAnalysisResponse,
    summary="Analyze sentiment",
    description="Analyze sentiment of provided text"
)
def analyze_text_sentiment(
    request: SentimentAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze the sentiment of a text input.
    
    Request Body:
        text: Text to analyze
        context: Optional context for analysis
    
    Returns:
        SentimentAnalysisResponse: Sentiment score and classification
    """
    try:
        # Run sentiment analysis
        sentiment_result = analyze_sentiment(request.text)
        
        # Log the analysis
        sentiment_log = SentimentLog(
            user_id=current_user.id,
            text=request.text,
            sentiment_score=sentiment_result.get('score'),
            sentiment_label=sentiment_result.get('label'),
            context=request.context,
        )
        db.add(sentiment_log)
        db.commit()
        db.refresh(sentiment_log)
        
        logger.info(
            f"Sentiment analyzed for user: {current_user.id}, "
            f"score: {sentiment_result.get('score')}"
        )
        
        return SentimentAnalysisResponse(
            score=sentiment_result.get('score'),
            label=sentiment_result.get('label'),
            confidence=sentiment_result.get('confidence'),
            analysis_id=sentiment_log.id,
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze sentiment"
        )


@router.get(
    "/conversation/{conversation_id}",
    response_model=dict,
    summary="Get conversation sentiment",
    description="Get sentiment analysis for an entire conversation"
)
def get_conversation_sentiment(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get sentiment statistics for a conversation.
    
    Path Parameters:
        conversation_id: ID of the conversation
    
    Returns:
        dict: Sentiment statistics and trend analysis
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
        
        # Get all sentiment logs for conversation messages
        from app.models.message import Message
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).all()
        
        sentiment_scores = [m.sentiment_score for m in messages if m.sentiment_score]
        
        if not sentiment_scores:
            return {
                "conversation_id": conversation_id,
                "total_messages": len(messages),
                "messages_analyzed": 0,
                "average_sentiment": None,
                "trend": "N/A"
            }
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        # Determine trend
        if len(sentiment_scores) > 1:
            trend = "improving" if sentiment_scores[-1] > sentiment_scores[0] else "declining"
        else:
            trend = "stable"
        
        logger.info(
            f"Retrieved sentiment stats for conversation: {conversation_id}, "
            f"average: {avg_sentiment}"
        )
        
        return {
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "messages_analyzed": len(sentiment_scores),
            "average_sentiment": round(avg_sentiment, 2),
            "min_sentiment": round(min(sentiment_scores), 2),
            "max_sentiment": round(max(sentiment_scores), 2),
            "trend": trend,
            "scores": sentiment_scores,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation sentiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sentiment analysis"
        )


@router.get(
    "/user/logs",
    response_model=List[SentimentLogResponse],
    summary="Get user sentiment logs",
    description="Retrieve all sentiment analyses for current user"
)
def get_user_sentiment_logs(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all sentiment analysis logs for the current user.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 50)
    
    Returns:
        List[SentimentLogResponse]: Sentiment analysis logs
    """
    try:
        logs = db.query(SentimentLog).filter(
            SentimentLog.user_id == current_user.id
        ).offset(skip).limit(limit).all()
        
        logger.info(
            f"Retrieved {len(logs)} sentiment logs for user: {current_user.id}"
        )
        
        return [SentimentLogResponse.from_orm(log) for log in logs]
    except Exception as e:
        logger.error(f"Error retrieving sentiment logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sentiment logs"
        )


@router.get(
    "/user/summary",
    response_model=dict,
    summary="Get sentiment summary",
    description="Get sentiment summary statistics for current user"
)
def get_user_sentiment_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get sentiment summary statistics for the current user.
    
    Returns:
        dict: Sentiment statistics across all user interactions
    """
    try:
        logs = db.query(SentimentLog).filter(
            SentimentLog.user_id == current_user.id
        ).all()
        
        if not logs:
            return {
                "user_id": current_user.id,
                "total_analyses": 0,
                "average_sentiment": None,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
            }
        
        scores = [log.sentiment_score for log in logs if log.sentiment_score]
        labels = [log.sentiment_label for log in logs if log.sentiment_label]
        
        avg_sentiment = sum(scores) / len(scores) if scores else None
        
        positive_count = labels.count("positive")
        negative_count = labels.count("negative")
        neutral_count = labels.count("neutral")
        
        logger.info(
            f"Retrieved sentiment summary for user: {current_user.id}"
        )
        
        return {
            "user_id": current_user.id,
            "total_analyses": len(logs),
            "average_sentiment": round(avg_sentiment, 2) if avg_sentiment else None,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_percentage": round((positive_count / len(logs) * 100), 1) if logs else 0,
            "negative_percentage": round((negative_count / len(logs) * 100), 1) if logs else 0,
            "neutral_percentage": round((neutral_count / len(logs) * 100), 1) if logs else 0,
        }
    except Exception as e:
        logger.error(f"Error retrieving sentiment summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sentiment summary"
        )
