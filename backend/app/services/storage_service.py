"""
Storage service for handling file operations.
Manages file uploads, storage, and retrieval for ads, brand assets, and reports.
"""
import os
import shutil
from pathlib import Path
from typing import Optional, List, BinaryIO
from datetime import datetime

from app.config import settings


class StorageService:
    """Service for managing file storage operations."""
    
    def __init__(self):
        """Initialize storage service with base directory."""
        self.base_dir = settings.storage_dir
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary storage directories if they don't exist."""
        directories = [
            self.base_dir / "ads",
            self.base_dir / "brand_assets",
            self.base_dir / "reports",
            self.base_dir / "uploads",  # Temporary upload directory
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_file(
        self,
        file_content: bytes,
        filename: str,
        subdirectory: str = "uploads",
        create_unique: bool = True
    ) -> Path:
        """
        Save a file to storage.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            subdirectory: Subdirectory within storage (ads, brand_assets, reports, uploads)
            create_unique: If True, append timestamp to filename to make it unique
        
        Returns:
            Path to saved file
        """
        # Get target directory
        target_dir = self.base_dir / subdirectory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unique filename if needed
        if create_unique:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{timestamp}{ext}"
        else:
            unique_filename = filename
        
        # Save file
        file_path = target_dir / unique_filename
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return file_path
    
    def save_uploaded_file(
        self,
        uploaded_file: BinaryIO,
        filename: str,
        subdirectory: str = "uploads"
    ) -> Path:
        """
        Save an uploaded file (from FastAPI UploadFile).
        
        Args:
            uploaded_file: File-like object from FastAPI
            filename: Original filename
            subdirectory: Subdirectory within storage
        
        Returns:
            Path to saved file
        """
        # Read file content
        file_content = uploaded_file.read()
        return self.save_file(file_content, filename, subdirectory)
    
    def get_file_path(self, filename: str, subdirectory: str) -> Optional[Path]:
        """
        Get path to a stored file.
        
        Args:
            filename: Name of the file
            subdirectory: Subdirectory within storage
        
        Returns:
            Path to file if exists, None otherwise
        """
        file_path = self.base_dir / subdirectory / filename
        if file_path.exists():
            return file_path
        return None
    
    def read_file(self, file_path: Path) -> Optional[bytes]:
        """
        Read file content.
        
        Args:
            file_path: Path to file
        
        Returns:
            File content as bytes, None if file doesn't exist
        """
        if not file_path.exists():
            return None
        
        with open(file_path, "rb") as f:
            return f.read()
    
    def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to file to delete
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def list_files(self, subdirectory: str, pattern: Optional[str] = None) -> List[Path]:
        """
        List files in a subdirectory.
        
        Args:
            subdirectory: Subdirectory within storage
            pattern: Optional glob pattern to filter files
        
        Returns:
            List of file paths
        """
        target_dir = self.base_dir / subdirectory
        if not target_dir.exists():
            return []
        
        if pattern:
            return list(target_dir.glob(pattern))
        else:
            return [f for f in target_dir.iterdir() if f.is_file()]
    
    def get_storage_path(self, subdirectory: str) -> Path:
        """
        Get the full path to a subdirectory.
        
        Args:
            subdirectory: Subdirectory name
        
        Returns:
            Path to subdirectory
        """
        return self.base_dir / subdirectory
    
    def save_ad_variation(
        self,
        file_content: bytes,
        run_id: str,
        variation_id: str,
        extension: str = ".jpg"
    ) -> Path:
        """
        Save an ad variation file.
        
        Args:
            file_content: Image/video content as bytes
            run_id: Run ID
            variation_id: Variation ID
            extension: File extension (.jpg, .mp4, etc.)
        
        Returns:
            Path to saved file
        """
        # Create run-specific directory
        run_dir = self.base_dir / "ads" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        filename = f"variation_{variation_id}{extension}"
        file_path = run_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return file_path
    
    def save_brand_asset(
        self,
        file_content: bytes,
        filename: str,
        asset_type: str = "logo"
    ) -> Path:
        """
        Save a brand asset (logo, product image, etc.).
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            asset_type: Type of asset (logo, product, etc.)
        
        Returns:
            Path to saved file
        """
        asset_dir = self.base_dir / "brand_assets" / asset_type
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        
        file_path = asset_dir / unique_filename
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return file_path
    
    def save_report(
        self,
        report_content: str,
        run_id: str,
        report_type: str = "critique"
    ) -> Path:
        """
        Save a report (JSON or text).
        
        Args:
            report_content: Report content as string
            run_id: Run ID
            report_type: Type of report (critique, final, etc.)
        
        Returns:
            Path to saved file
        """
        report_dir = self.base_dir / "reports" / run_id
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_report_{timestamp}.json"
        file_path = report_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return file_path


# Global storage service instance
storage_service = StorageService()
