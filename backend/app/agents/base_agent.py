"""
Base agent class for all agents.
Provides common functionality and interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.services.logger import app_logger


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self):
        """Initialize base agent."""
        self.logger = app_logger
        self.name = self.__class__.__name__
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute agent task.
        
        This method should be implemented by subclasses.
        
        Returns:
            Dictionary with execution results
        """
        pass
    
    def log_start(self, task_name: str, **context):
        """Log task start."""
        self.logger.info(f"[{self.name}] Starting {task_name}", extra=context)
    
    def log_complete(self, task_name: str, **context):
        """Log task completion."""
        self.logger.info(f"[{self.name}] Completed {task_name}", extra=context)
    
    def log_error(self, task_name: str, error: Exception, **context):
        """Log task error."""
        self.logger.error(
            f"[{self.name}] Error in {task_name}: {error}",
            extra={**context, "error": str(error)}
        )
    
    def create_result(
        self,
        success: bool,
        data: Optional[Dict] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create standardized result dictionary.
        
        Args:
            success: Whether the operation was successful
            data: Result data
            error: Error message if failed
            metadata: Additional metadata
        
        Returns:
            Standardized result dictionary
        """
        result = {
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": self.name
        }
        
        if data:
            result["data"] = data
        
        if error:
            result["error"] = error
        
        if metadata:
            result["metadata"] = metadata
        
        return result
