"""
Main API routes for BrandAI.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.request import AdGenerationRequest, MediaType
from app.models.response import GenerationResponse, StatusResponse, FinalResponse
from app.models.run import RunStatus
from app.core.orchestrator import orchestrator
from app.core.run_manager import run_manager
from app.core.exceptions import RunNotFoundError, ValidationError, WorkflowError, FileUploadError
from app.services.storage_service import storage_service
from app.services.logger import app_logger

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "BrandAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "generate": "POST /generate",
            "status": "GET /status/{run_id}",
            "health": "GET /health"
        }
    }


@router.post("/generate", response_model=GenerationResponse)
async def generate_ad(
    background_tasks: BackgroundTasks,
    prompt: str = Form(..., description="Description of how the ad should be and what it should convey", min_length=10, max_length=1000),
    media_type: MediaType = Form(..., description="Type of media to generate: 'image' or 'video'"),
    brand_website_url: Optional[str] = Form(None, description="Optional brand website URL for scraping brand kit information"),
    logo: Optional[UploadFile] = File(None, description="Brand logo image file"),
    product: Optional[UploadFile] = File(None, description="Product image file")
):
    """
    Generate an advertisement (image or video).
    
    This endpoint:
    1. Accepts file uploads (logo, product images)
    2. Validates input
    3. Creates a run and starts the workflow in background
    4. Returns run_id for status tracking
    
    Args:
        prompt: Description of the ad
        media_type: 'image' or 'video'
        brand_website_url: Optional brand website URL
        logo: Optional logo image file
        product: Optional product image file
    
    Returns:
        GenerationResponse with run_id and status
    """
    try:
        app_logger.info(f"Received /generate request: media_type={media_type}, has_logo={logo is not None}, has_product={product is not None}")
        
        # Validate inputs
        if not prompt or len(prompt.strip()) < 10:
            raise ValidationError("Prompt must be at least 10 characters long")
        
        # Convert MediaType enum to string if needed
        media_type_str = media_type.value if isinstance(media_type, MediaType) else str(media_type)
        if media_type_str not in ["image", "video"]:
            raise ValidationError("media_type must be 'image' or 'video'")
        
        # Save uploaded files
        logo_path = None
        product_path = None
        
        if logo:
            try:
                # Validate file type
                if not logo.filename:
                    raise FileUploadError("Logo file must have a filename")
                
                # Check file extension
                logo_ext = Path(logo.filename).suffix.lower()
                if logo_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                    raise FileUploadError(f"Logo file must be an image (jpg, jpeg, png, webp), got: {logo_ext}")
                
                # Read file content
                logo_content = await logo.read()
                if len(logo_content) == 0:
                    raise FileUploadError("Logo file is empty")
                
                # Save file
                logo_path = storage_service.save_brand_asset(
                    file_content=logo_content,
                    asset_type="logo",
                    filename=logo.filename
                )
                app_logger.info(f"Logo saved: {logo_path}")
            
            except Exception as e:
                raise FileUploadError(f"Error saving logo: {str(e)}")
        
        if product:
            try:
                # Validate file type
                if not product.filename:
                    raise FileUploadError("Product file must have a filename")
                
                # Check file extension
                product_ext = Path(product.filename).suffix.lower()
                if product_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                    raise FileUploadError(f"Product file must be an image (jpg, jpeg, png, webp), got: {product_ext}")
                
                # Read file content
                product_content = await product.read()
                if len(product_content) == 0:
                    raise FileUploadError("Product file is empty")
                
                # Save file
                product_path = storage_service.save_brand_asset(
                    file_content=product_content,
                    asset_type="product",
                    filename=product.filename
                )
                app_logger.info(f"Product saved: {product_path}")
            
            except Exception as e:
                raise FileUploadError(f"Error saving product: {str(e)}")
        
        # Create run
        run = run_manager.create_run(
            prompt=prompt,
            media_type=media_type_str,
            brand_website_url=brand_website_url
        )
        run_id = run.run_id
        
        app_logger.info(f"Created run {run_id} for {media_type_str} generation")
        
        # Start workflow in background (non-blocking)
        background_tasks.add_task(
            execute_workflow,
            run_id=run_id,
            prompt=prompt,
            media_type=media_type_str,
            brand_website_url=brand_website_url,
            logo_path=str(logo_path) if logo_path else None,
            product_path=str(product_path) if product_path else None
        )
        
        app_logger.info(f"Background task added for run {run_id}, returning response immediately")
        
        # Estimate time (rough estimates)
        estimated_time = 120 if media_type_str == "image" else 300  # 2 min for image, 5 min for video
        
        response = GenerationResponse(
            run_id=run_id,
            status=RunStatus.PENDING,
            message="Ad generation started. Use the run_id to check status.",
            estimated_time=estimated_time
        )
        
        app_logger.info(f"Returning response for run {run_id}")
        return response
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except FileUploadError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        app_logger.error(f"Error in /generate endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def execute_workflow(
    run_id: str,
    prompt: str,
    media_type: str,
    brand_website_url: Optional[str],
    logo_path: Optional[str],
    product_path: Optional[str]
):
    """Execute workflow in background (non-blocking)."""
    try:
        app_logger.info(f"Starting workflow execution for run {run_id}")
        
        # Run synchronous orchestrator.execute() in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                orchestrator.execute,
                run_id,
                prompt,
                media_type,
                brand_website_url,
                logo_path,
                product_path,
                3  # max_retries
            )
        
        app_logger.info(f"Workflow completed for run {run_id}: {result.get('status')}")
    
    except Exception as e:
        app_logger.error(f"Error executing workflow for run {run_id}: {e}")
        run_manager.fail_run(run_id, str(e))


@router.get("/status/{run_id}", response_model=StatusResponse)
async def get_status(run_id: str):
    """
    Get the status of an ad generation run.
    
    Args:
        run_id: Unique run ID returned from /generate endpoint
    
    Returns:
        StatusResponse with current status and progress
    """
    try:
        run = run_manager.get_run(run_id)
        
        if not run:
            raise RunNotFoundError(run_id)
        
        # Check if workflow is complete
        if run.status == RunStatus.COMPLETED:
            # Get final result if available
            # The orchestrator stores results in run_manager
            pass
        
        return StatusResponse(
            run_id=run.run_id,
            status=run.status,
            progress=run.progress,
            current_stage=run.current_stage,
            message=run.error_message if run.status == RunStatus.FAILED else None,
            created_at=run.created_at,
            updated_at=run.updated_at
        )
    
    except RunNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        app_logger.error(f"Error in /status endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/result/{run_id}", response_model=FinalResponse)
async def get_result(run_id: str):
    """
    Get the final result of a completed ad generation run.
    
    Args:
        run_id: Unique run ID
    
    Returns:
        FinalResponse with generated ad and critique report
    """
    try:
        run = run_manager.get_run(run_id)
        
        if not run:
            raise RunNotFoundError(run_id)
        
        if run.status != RunStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Run {run_id} is not completed yet. Current status: {run.status}"
            )
        
        # Get final ad path
        final_ad_path = run.final_ad_path
        
        # Get critique report if available
        critique_report = None
        if run.critique_results:
            # Convert critique results to CritiqueReport model
            from app.models.response import CritiqueReport
            try:
                critique_report = CritiqueReport(**run.critique_results)
            except:
                pass
        
        return FinalResponse(
            run_id=run.run_id,
            status=run.status,
            success=True,
            critique_report=critique_report,
            retry_count=run.retry_count,
            completed_at=run.completed_at or run.updated_at
        )
    
    except RunNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error in /result endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
