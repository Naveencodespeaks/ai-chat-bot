"""
Sentiment request/response schemas

Pydantic models used by sentiment API endpoints.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SentimentAnalysisRequest(BaseModel):
	"""Request body for sentiment analysis."""

	text: str = Field(..., min_length=1, description="Text to analyze")
	context: Optional[str] = Field(None, description="Optional context to influence analysis")


class SentimentAnalysisResponse(BaseModel):
	"""Response for sentiment analysis."""

	score: float = Field(..., description="Sentiment score (-1 to 1 or 0-1 depending on impl)")
	label: str = Field(..., description="Sentiment label: positive/negative/neutral")
	confidence: Optional[float] = Field(None, description="Confidence of the prediction (0-1)")
	analysis_id: Optional[int] = Field(None, description="ID of persisted analysis record")


class SentimentLogResponse(BaseModel):
	"""Representation of a stored sentiment analysis log."""

	id: int
	user_id: int
	text: Optional[str]
	sentiment_score: Optional[float]
	sentiment_label: Optional[str]
	confidence: Optional[float]
	context: Optional[str]
	created_at: Optional[datetime]

	model_config = {"from_attributes": True}


class SentimentSummary(BaseModel):
	user_id: int
	total_analyses: int
	average_sentiment: Optional[float]
	positive_count: int
	negative_count: int
	neutral_count: int
	positive_percentage: float
	negative_percentage: float
	neutral_percentage: float

 
