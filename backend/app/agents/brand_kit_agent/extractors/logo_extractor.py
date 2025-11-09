"""
Logo extraction from brand assets.
Detects and analyzes logos from uploaded images.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from PIL import Image

from app.services.logger import app_logger


class LogoExtractor:
    """Extract logo information from brand assets."""
    
    def __init__(self):
        """Initialize logo extractor."""
        self.logger = app_logger
    
    def extract_logo_features(
        self,
        image_path: Path,
        min_area: int = 1000
    ) -> Dict:
        """
        Extract logo features from an image.
        
        Args:
            image_path: Path to image file
            min_area: Minimum area for logo detection (pixels)
        
        Returns:
            Dictionary with logo features:
            - detected: bool
            - bounding_box: (x, y, width, height) or None
            - dominant_colors: List of color tuples
            - aspect_ratio: float
            - area: int
            - center: (x, y)
        """
        try:
            # Read image
            image = cv2.imread(str(image_path))
            if image is None:
                self.logger.warning(f"Could not read image: {image_path}")
                return {"detected": False, "error": "Could not read image"}
            
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Try to detect logo using contour detection
            logo_info = self._detect_logo_contour(gray, min_area)
            
            if logo_info["detected"]:
                # Extract logo region
                x, y, w, h = logo_info["bounding_box"]
                logo_region = image_rgb[y:y+h, x:x+w]
                
                # Extract dominant colors from logo region
                dominant_colors = self._extract_dominant_colors(logo_region)
                
                logo_info.update({
                    "dominant_colors": dominant_colors,
                    "aspect_ratio": w / h if h > 0 else 0,
                    "area": w * h,
                    "center": (x + w // 2, y + h // 2)
                })
            
            return logo_info
            
        except Exception as e:
            self.logger.error(f"Error extracting logo features: {e}")
            return {"detected": False, "error": str(e)}
    
    def _detect_logo_contour(
        self,
        gray_image: np.ndarray,
        min_area: int
    ) -> Dict:
        """
        Detect logo using contour detection.
        
        Args:
            gray_image: Grayscale image
            min_area: Minimum contour area
        
        Returns:
            Dictionary with detection results
        """
        # Apply threshold
        _, thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area
        large_contours = [c for c in contours if cv2.contourArea(c) >= min_area]
        
        if not large_contours:
            return {"detected": False}
        
        # Get largest contour (likely the logo)
        largest_contour = max(large_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        return {
            "detected": True,
            "bounding_box": (x, y, w, h),
            "contour_area": cv2.contourArea(largest_contour)
        }
    
    def _extract_dominant_colors(
        self,
        image_region: np.ndarray,
        k: int = 5
    ) -> List[Tuple[int, int, int]]:
        """
        Extract dominant colors from image region using K-means.
        
        Args:
            image_region: Image region as numpy array
            k: Number of colors to extract
        
        Returns:
            List of RGB color tuples
        """
        try:
            # Reshape image to 2D array of pixels
            pixels = image_region.reshape(-1, 3)
            
            # Convert to float32
            pixels = np.float32(pixels)
            
            # Apply K-means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert centers to uint8
            centers = np.uint8(centers)
            
            # Get color frequencies
            unique, counts = np.unique(labels.flatten(), return_counts=True)
            
            # Sort by frequency
            color_freq = list(zip(centers, counts))
            color_freq.sort(key=lambda x: x[1], reverse=True)
            
            # Extract top colors
            dominant_colors = [tuple(color.tolist()) for color, _ in color_freq]
            
            return dominant_colors
            
        except Exception as e:
            self.logger.warning(f"Error extracting dominant colors: {e}")
            return []
    
    def analyze_logo_file(
        self,
        logo_path: Path
    ) -> Dict:
        """
        Analyze a logo file directly.
        
        Args:
            logo_path: Path to logo file
        
        Returns:
            Dictionary with logo analysis:
            - file_path: str
            - dimensions: (width, height)
            - format: str
            - file_size: int
            - dominant_colors: List of RGB tuples
            - is_transparent: bool
        """
        try:
            with Image.open(logo_path) as img:
                width, height = img.size
                format_type = img.format
                mode = img.mode
                
                # Check for transparency
                is_transparent = mode in ('RGBA', 'LA') or 'transparency' in img.info
                
                # Convert to RGB if needed
                if mode != 'RGB':
                    img_rgb = img.convert('RGB')
                else:
                    img_rgb = img
                
                # Extract dominant colors
                img_array = np.array(img_rgb)
                dominant_colors = self._extract_dominant_colors(img_array)
                
                return {
                    "file_path": str(logo_path),
                    "dimensions": (width, height),
                    "format": format_type,
                    "file_size": logo_path.stat().st_size,
                    "dominant_colors": dominant_colors,
                    "is_transparent": is_transparent,
                    "aspect_ratio": width / height if height > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing logo file: {e}")
            return {"error": str(e)}


# Global logo extractor instance
logo_extractor = LogoExtractor()
