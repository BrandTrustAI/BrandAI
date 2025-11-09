"""
FastAPI application entry point for BrandAI.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import health, routes
from app.core.exceptions import BrandAIException
from app.services.logger import app_logger

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
app.include_router(routes.router, tags=["Generation"], prefix="/api/v1")


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors."""
    errors = exc.errors()
    error_msg = f"Validation error: {errors}"
    print(error_msg)  # Also print to stdout for Docker logs
    app_logger.error(error_msg)
    
    # Log form data if available
    try:
        form = await request.form()
        form_keys = list(form.keys())
        print(f"Form data keys: {form_keys}")  # Print to stdout
        app_logger.error(f"Form data keys: {form_keys}")
        for key in form_keys:
            if key in ['logo', 'product']:
                file = form[key]
                file_info = f"  {key}: {file.filename if hasattr(file, 'filename') else 'N/A'}"
                print(file_info)
                app_logger.error(file_info)
            else:
                value = form[key]
                field_info = f"  {key}: {value[:100] if isinstance(value, str) and len(value) > 100 else value}"
                print(field_info)
                app_logger.error(field_info)
    except Exception as e:
        error_detail = f"Could not read form data: {e}"
        print(error_detail)
        app_logger.error(error_detail)
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": errors
        }
    )


@app.exception_handler(BrandAIException)
async def brandai_exception_handler(request: Request, exc: BrandAIException):
    """Handle BrandAI custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.APP_ENV == "development" else None
        }
    )


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
