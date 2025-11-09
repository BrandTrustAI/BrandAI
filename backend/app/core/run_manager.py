"""
Run manager for tracking ad generation workflow runs.
Uses in-memory storage for run status tracking.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict
from threading import Lock

from app.models.run import RunModel, RunStatus, RunStage


class RunManager:
    """
    In-memory run manager for tracking workflow runs.
    
    Thread-safe implementation for concurrent access.
    """
    
    def __init__(self):
        """Initialize run manager with empty storage."""
        self._runs: Dict[str, RunModel] = {}
        self._lock = Lock()
    
    def create_run(
        self,
        prompt: str,
        media_type: str,
        brand_website_url: Optional[str] = None
    ) -> RunModel:
        """
        Create a new run.
        
        Args:
            prompt: User-provided prompt
            media_type: Media type ('image' or 'video')
            brand_website_url: Optional brand website URL
        
        Returns:
            Created RunModel instance
        """
        run_id = self._generate_run_id()
        
        run = RunModel(
            run_id=run_id,
            prompt=prompt,
            media_type=media_type,
            brand_website_url=brand_website_url,
            status=RunStatus.PENDING,
            progress=0.0
        )
        
        with self._lock:
            self._runs[run_id] = run
        
        return run
    
    def get_run(self, run_id: str) -> Optional[RunModel]:
        """
        Get a run by ID.
        
        Args:
            run_id: Run ID
        
        Returns:
            RunModel if found, None otherwise
        """
        with self._lock:
            return self._runs.get(run_id)
    
    def update_status(
        self,
        run_id: str,
        status: RunStatus,
        progress: Optional[float] = None,
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update run status.
        
        Args:
            run_id: Run ID
            status: New status
            progress: Progress percentage (0-100)
            current_stage: Current stage name
            error_message: Error message if failed
        
        Returns:
            True if updated, False if run not found
        """
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return False
            
            run.status = status
            run.updated_at = datetime.now(timezone.utc)
            
            if progress is not None:
                run.progress = max(0.0, min(100.0, progress))
            
            if current_stage is not None:
                run.current_stage = current_stage
            
            if error_message is not None:
                run.error_message = error_message
            
            return True
    
    def start_stage(
        self,
        run_id: str,
        stage_name: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Start a workflow stage.
        
        Args:
            run_id: Run ID
            stage_name: Name of the stage
            metadata: Optional stage metadata
        
        Returns:
            True if started, False if run not found
        """
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return False
            
            stage = RunStage(
                stage_name=stage_name,
                status=RunStatus.PENDING,
                started_at=datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            
            run.stages[stage_name] = stage
            run.current_stage = stage_name
            run.updated_at = datetime.now(timezone.utc)
            
            return True
    
    def complete_stage(
        self,
        run_id: str,
        stage_name: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Complete a workflow stage.
        
        Args:
            run_id: Run ID
            stage_name: Name of the stage
            metadata: Optional stage metadata
        
        Returns:
            True if completed, False if run not found
        """
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return False
            
            if stage_name in run.stages:
                stage = run.stages[stage_name]
                stage.status = RunStatus.COMPLETED
                stage.completed_at = datetime.now(timezone.utc)
                if metadata:
                    stage.metadata.update(metadata)
            
            run.updated_at = datetime.now(timezone.utc)
            
            return True
    
    def fail_stage(
        self,
        run_id: str,
        stage_name: str,
        error: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Mark a workflow stage as failed.
        
        Args:
            run_id: Run ID
            stage_name: Name of the stage
            error: Error message
            metadata: Optional stage metadata
        
        Returns:
            True if failed, False if run not found
        """
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return False
            
            if stage_name in run.stages:
                stage = run.stages[stage_name]
                stage.status = RunStatus.FAILED
                stage.completed_at = datetime.now(timezone.utc)
                stage.error = error
                if metadata:
                    stage.metadata.update(metadata)
            
            run.status = RunStatus.FAILED
            run.error_message = error
            run.updated_at = datetime.now(timezone.utc)
            
            return True
    
    def update_run_data(
        self,
        run_id: str,
        brand_kit_data: Optional[Dict] = None,
        generated_ads: Optional[list] = None,
        critique_results: Optional[Dict] = None,
        final_ad_path: Optional[str] = None
    ) -> bool:
        """
        Update run data (results).
        
        Args:
            run_id: Run ID
            brand_kit_data: Extracted brand kit data
            generated_ads: List of generated ad paths
            critique_results: Critique evaluation results
            final_ad_path: Path to final selected ad
        
        Returns:
            True if updated, False if run not found
        """
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return False
            
            if brand_kit_data is not None:
                run.brand_kit_data = brand_kit_data
            
            if generated_ads is not None:
                run.generated_ads = generated_ads
            
            if critique_results is not None:
                run.critique_results = critique_results
            
            if final_ad_path is not None:
                run.final_ad_path = final_ad_path
            
            run.updated_at = datetime.now(timezone.utc)
            
            return True
    
    def increment_retry(self, run_id: str) -> bool:
        """
        Increment retry count for a run.
        
        Args:
            run_id: Run ID
        
        Returns:
            True if incremented, False if run not found
        """
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return False
            
            run.retry_count += 1
            run.updated_at = datetime.now(timezone.utc)
            
            return True
    
    def complete_run(self, run_id: str, success: bool = True) -> bool:
        """
        Mark a run as completed.
        
        Args:
            run_id: Run ID
            success: Whether the run was successful
        
        Returns:
            True if completed, False if run not found
        """
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return False
            
            run.status = RunStatus.COMPLETED if success else RunStatus.FAILED
            run.progress = 100.0
            run.completed_at = datetime.now(timezone.utc)
            run.updated_at = datetime.now(timezone.utc)
            
            return True
    
    def delete_run(self, run_id: str) -> bool:
        """
        Delete a run from memory.
        
        Args:
            run_id: Run ID
        
        Returns:
            True if deleted, False if run not found
        """
        with self._lock:
            if run_id in self._runs:
                del self._runs[run_id]
                return True
            return False
    
    def list_runs(self, status: Optional[RunStatus] = None) -> list[RunModel]:
        """
        List all runs, optionally filtered by status.
        
        Args:
            status: Optional status filter
        
        Returns:
            List of RunModel instances
        """
        with self._lock:
            runs = list(self._runs.values())
            if status:
                runs = [r for r in runs if r.status == status]
            return runs
    
    def _generate_run_id(self) -> str:
        """
        Generate a unique run ID using UUID.
        
        Returns:
            Unique run ID string (UUID format)
        """
        return str(uuid.uuid4())


# Global run manager instance
run_manager = RunManager()
