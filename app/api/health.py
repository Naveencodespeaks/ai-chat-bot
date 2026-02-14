from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/api/health", tags=["health"])


class HealthResponse(BaseModel):
	status: str
	timestamp: datetime


@router.get("/", response_model=HealthResponse, summary="Liveness probe")
def liveness():
	return HealthResponse(status="ok", timestamp=datetime.utcnow())


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
def readiness():
	return HealthResponse(status="ready", timestamp=datetime.utcnow())
