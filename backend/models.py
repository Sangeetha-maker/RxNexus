"""Pydantic Request & Response Schemas for PayerRx Optimizer API."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    data_ready: bool
    total_opportunities: int
    datasets_cataloged: int


class ScoreSimulationRequest(BaseModel):
    cost: float = Field(0.30, ge=0.0, le=1.0)
    utilization: float = Field(0.25, ge=0.0, le=1.0)
    friction: float = Field(0.20, ge=0.0, le=1.0)
    adherence: float = Field(0.15, ge=0.0, le=1.0)
    alternative: float = Field(0.10, ge=0.0, le=1.0)


class ReviewActionRequest(BaseModel):
    status: str = Field(..., description="Review status: New, Under Review, Validated, Dismissed, Needs More Data")
    notes: Optional[str] = ""
    reviewer: Optional[str] = "Payer Pharmacy Analyst"


class AssistantQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    opportunity_id: Optional[str] = None
