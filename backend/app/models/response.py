"""
Response models for BrandAI API.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.models.run import RunStatus


class ScoreCard(BaseModel):
    """Individual dimension score."""
    dimension: str = Field(..., description="Evaluation dimension name")
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")
    feedback: str = Field(..., description="Detailed feedback for this dimension")
    issues: Optional[List[str]] = Field(None, description="List of issues found")
    suggestions: Optional[List[str]] = Field(None, description="Suggestions for improvement")


class VariationResult(BaseModel):
    """Result for a single generated ad variation."""
    variation_id: str = Field(..., description="Unique ID for this variation")
    file_path: str = Field(..., description="Path to generated ad file")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    scorecard: List[ScoreCard] = Field(..., description="Detailed scorecard per dimension")
    passed: bool = Field(..., description="Whether this variation passed all criteria")
    rank: Optional[int] = Field(None, description="Ranking among all variations (1 = best)")


class CritiqueReport(BaseModel):
    """Complete critique report for generated ads."""
    run_id: str = Field(..., description="Run ID this report belongs to")
    total_variations: int = Field(..., description="Total number of variations generated")
    passed_variations: int = Field(..., description="Number of variations that passed")
    failed_variations: int = Field(..., description="Number of variations that failed")
    best_variation: Optional[VariationResult] = Field(None, description="Best variation result")
    all_variations: List[VariationResult] = Field(..., description="All variation results")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Report generation timestamp")


class GenerationResponse(BaseModel):
    """Initial response after starting ad generation."""
    run_id: str = Field(..., description="Unique run ID for tracking")
    status: RunStatus = Field(..., description="Current run status")
    message: str = Field(..., description="Status message")
    estimated_time: Optional[int] = Field(None, description="Estimated completion time in seconds")


class StatusResponse(BaseModel):
    """Response for run status check."""
    run_id: str = Field(..., description="Run ID")
    status: RunStatus = Field(..., description="Current status")
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    current_stage: Optional[str] = Field(None, description="Current processing stage")
    message: Optional[str] = Field(None, description="Status message")
    created_at: datetime = Field(..., description="Run creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class FinalResponse(BaseModel):
    """Final response with generated ads and critique report."""
    run_id: str = Field(..., description="Run ID")
    status: RunStatus = Field(..., description="Final status")
    success: bool = Field(..., description="Whether generation was successful")
    critique_report: Optional[CritiqueReport] = Field(None, description="Critique report if available")
    variations: Optional[List[Dict[str, Any]]] = Field(None, description="List of generated ad variations")
    error: Optional[str] = Field(None, description="Error message if generation failed")
    retry_count: int = Field(0, description="Number of retry attempts made")
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Completion timestamp")
