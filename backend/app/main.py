"""
FastAPI application entry point for BrandAI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import health, routes

# Create FastAPI application
app = FastAPI(
    title="BrandAI API",
    description="AI Critique Engine for Generated Ads",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(routes.router, tags=["Generation"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Validate configuration
    try:
        settings.validate()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"⚠️  Configuration warning: {e}")
    
    # Create necessary directories
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    # Note: RAG not used - using direct data passing and few-shot prompts instead
    
    print(f"🚀 BrandAI API started on {settings.API_HOST}:{settings.API_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    print("🛑 BrandAI API shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.APP_ENV == "development"
    )
