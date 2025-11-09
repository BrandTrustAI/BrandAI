"""
Health check endpoints.
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Dict

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    Returns API status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "BrandAI API"
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict:
    """
    Detailed health check endpoint.
    Returns comprehensive system status.
    """
    from app.config import settings
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "BrandAI API",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "config": {
            "gcp_project_id": settings.GCP_PROJECT_ID if settings.GCP_PROJECT_ID else "not_set",
            "vertex_ai_enabled": settings.VERTEX_AI_ENABLED,
            "gemini_api_key_set": bool(settings.GEMINI_API_KEY),
        }
    }
