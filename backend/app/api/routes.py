"""
Main API routes for BrandAI.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "BrandAI API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# TODO: Implement POST /generate endpoint
# TODO: Implement GET /status/{run_id} endpoint
