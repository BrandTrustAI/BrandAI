"""
Main API routes for BrandAI.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse

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
            "result": "GET /result/{run_id}",
            "media": "GET /media/{path:path}",
            "health": "GET /health"
        }
    }


@router.post("/generate", response_model=GenerationResponse)
async def generate_ad(
    background_tasks: BackgroundTasks,
    prompt: str = Form(..., description="Description of how the ad should be and what it should convey"),
    media_type: str = Form(..., description="Type of media to generate: 'image' or 'video'"),
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
        app_logger.info(f"Received /generate request: prompt_length={len(prompt) if prompt else 0}, media_type={media_type}, has_logo={logo is not None}, has_product={product is not None}")
        
        # Validate inputs
        if not prompt or len(prompt.strip()) < 10:
            app_logger.error(f"Invalid prompt: length={len(prompt) if prompt else 0}")
            raise ValidationError("Prompt must be at least 10 characters long")
        
        # Validate and convert media_type
        media_type_str = str(media_type).lower().strip()
        if media_type_str not in ["image", "video"]:
            app_logger.error(f"Invalid media_type: {media_type}")
            raise ValidationError("media_type must be 'image' or 'video'")
        
        # Convert to MediaType enum for internal use
        media_type_enum = MediaType(media_type_str)
        
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
        app_logger.error(f"Validation error: {e}")
        import traceback
        app_logger.error(traceback.format_exc())
        raise HTTPException(status_code=422, detail=str(e))
    except FileUploadError as e:
        app_logger.error(f"File upload error: {e}")
        import traceback
        app_logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Unexpected error in /generate: {e}")
        import traceback
        app_logger.error(traceback.format_exc())
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
        
        # Get critique report if available (only for scores, not for file paths)
        critique_report = None
        variations = []
        
        # DIRECTLY scan storage directory for generated files - THIS IS THE ONLY SOURCE
        storage_dir = settings.storage_dir
        ads_dir = storage_dir / "ads" / run_id
        
        app_logger.info(f"Scanning for generated files in: {ads_dir}")
        if ads_dir.exists() and ads_dir.is_dir():
            # Find all image and video files
            for file_path in sorted(ads_dir.iterdir()):  # Sort for consistent ordering
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".mov"]:
                        # Get relative path from storage_dir (e.g., "ads/{run_id}/var_1.png")
                        relative_path = file_path.relative_to(storage_dir)
                        media_path = str(relative_path).replace('\\', '/')  # Normalize path separators
                        
                        # Determine media type
                        media_type = "video" if ext in [".mp4", ".webm", ".mov"] else "image"
                        
                        # Extract variation_id from filename (e.g., var_1.png -> var_1)
                        variation_id = file_path.stem  # Gets filename without extension
                        
                        variations.append({
                            "variation_id": variation_id,
                            "file_path": media_path,
                            "media_type": media_type,
                            "overall_score": 0.0  # Will be populated from critique_report if available
                        })
                        app_logger.info(f"Found generated file: {variation_id} -> {media_path}")
        else:
            app_logger.warning(f"Directory does not exist: {ads_dir}")
        
        app_logger.info(f"Found {len(variations)} files in storage directory: {ads_dir}")
        
        # Get critique report ONLY to update scores, NOT for file paths
        if run.critique_results:
            # Convert critique results to CritiqueReport model
            from app.models.response import CritiqueReport
            try:
                # critique_results is a dict, parse it
                critique_data = run.critique_results if isinstance(run.critique_results, dict) else run.critique_results.dict() if hasattr(run.critique_results, 'dict') else {}
                critique_report = CritiqueReport(**critique_data)
                
                app_logger.info(f"Critique report loaded: {len(critique_report.all_variations) if critique_report.all_variations else 0} variations")
                
                # Update overall_score from critique report if variations already found
                if critique_report.all_variations and variations:
                    app_logger.info("Updating overall_score from critique report")
                    # Create a map of variation_id -> overall_score from critique report
                    score_map = {}
                    for var in critique_report.all_variations:
                        var_id = var.variation_id if hasattr(var, 'variation_id') else var.get('variation_id', '')
                        score = var.overall_score if hasattr(var, 'overall_score') else var.get('overall_score', 0.0)
                        if var_id:
                            score_map[var_id] = score
                    
                    # Update variations with scores
                    for var in variations:
                        var_id = var.get('variation_id', '')
                        if var_id in score_map:
                            var['overall_score'] = score_map[var_id]
                            app_logger.info(f"Updated score for {var_id}: {score_map[var_id]}")
            except Exception as e:
                app_logger.warning(f"Error parsing critique report: {e}")
                import traceback
                app_logger.error(traceback.format_exc())
        
        # If no variations found in directory, log warning
        if not variations:
            app_logger.warning(f"No generated files found in {ads_dir} for run {run_id}")
        
        app_logger.info(f"Returning {len(variations)} variations in result")
        if variations:
            for var in variations:
                app_logger.info(f"  Variation: {var['variation_id']} - {var['file_path']} ({var['media_type']})")
        
        # Create response with variations
        response_data = {
            "run_id": run.run_id,
            "status": run.status,
            "success": True,
            "critique_report": critique_report,
            "variations": variations if variations else None,
            "retry_count": run.retry_count,
            "completed_at": run.completed_at or run.updated_at
        }
        
        return FinalResponse(**response_data)
    
    except RunNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error in /result endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/media/{path:path}")
async def serve_media(path: str):
    """
    Serve generated media files (images/videos).
    
    Args:
        path: Relative path to the media file (e.g., "ads/{run_id}/var_1.png")
    
    Returns:
        FileResponse with the media file
    """
    try:
        app_logger.info(f"Media request received: {path}")
        
        # Remove leading slash if present
        path = path.lstrip('/')
        
        # Construct full path
        storage_dir = settings.storage_dir
        file_path = storage_dir / path
        
        app_logger.info(f"Storage dir: {storage_dir}, Requested path: {path}, Full path: {file_path}")
        app_logger.info(f"File exists: {file_path.exists()}, Is file: {file_path.is_file() if file_path.exists() else False}")
        
        # Security: Ensure path is within storage directory
        try:
            resolved_path = file_path.resolve()
            resolved_storage = storage_dir.resolve()
            resolved_path.relative_to(resolved_storage)
        except ValueError:
            app_logger.error(f"Path traversal attempt: {path}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            app_logger.warning(f"File not found: {file_path}")
            # Try alternative: check if it's a directory issue
            if file_path.is_dir():
                raise HTTPException(status_code=404, detail=f"Path is a directory, not a file: {path}")
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        
        # Determine media type
        ext = file_path.suffix.lower()
        media_type = None
        if ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            media_type = f"image/{ext[1:]}" if ext != ".jpg" else "image/jpeg"
        elif ext in [".mp4", ".webm", ".mov"]:
            media_type = f"video/{ext[1:]}" if ext != ".mov" else "video/quicktime"
        else:
            media_type = "application/octet-stream"
        
        app_logger.info(f"Serving media file: {file_path} (type: {media_type})")
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_path.name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error serving media file: {e}")
        import traceback
        app_logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
