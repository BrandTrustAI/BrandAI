"""
Custom exceptions for BrandAI application.
"""
from typing import Optional


class BrandAIException(Exception):
    """Base exception for BrandAI."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(BrandAIException):
    """Validation error."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class RunNotFoundError(BrandAIException):
    """Run not found error."""
    
    def __init__(self, run_id: str):
        super().__init__(f"Run with ID '{run_id}' not found", status_code=404)


class WorkflowError(BrandAIException):
    """Workflow execution error."""
    
    def __init__(self, message: str):
        super().__init__(f"Workflow error: {message}", status_code=500)


class FileUploadError(BrandAIException):
    """File upload error."""
    
    def __init__(self, message: str):
        super().__init__(f"File upload error: {message}", status_code=400)


class ConfigurationError(BrandAIException):
    """Configuration error."""
    
    def __init__(self, message: str):
        super().__init__(f"Configuration error: {message}", status_code=500)
