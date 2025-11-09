"""
Utility functions for refinement agent.
Image enhancement functions using OpenCV.
"""
from pathlib import Path
from typing import Dict, Optional
import cv2
import numpy as np

from app.services.logger import app_logger


class ImageEnhancer:
    """Enhance images using OpenCV for simple quality improvements."""
    
    def __init__(self):
        """Initialize image enhancer."""
        self.logger = app_logger
    
    def enhance_image(
        self,
        image_path: Path,
        output_path: Path,
        enhancements: Dict[str, bool]
    ) -> Dict:
        """
        Apply enhancements to image.
        
        Args:
            image_path: Path to input image
            output_path: Path to save enhanced image
            enhancements: Dictionary of enhancement flags:
                - sharpen: Apply sharpening (for blur)
                - denoise: Apply denoising (for noise)
                - contrast: Improve contrast
                - brightness: Adjust brightness
        
        Returns:
            Dictionary with enhancement results
        """
        self.logger.info(f"Enhancing image: {image_path}")
        
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                return {
                    "success": False,
                    "error": f"Failed to load image: {image_path}"
                }
            
            original = image.copy()
            
            # Apply enhancements
            if enhancements.get("sharpen", False):
                image = self._sharpen_image(image)
            
            if enhancements.get("denoise", False):
                image = self._denoise_image(image)
            
            if enhancements.get("contrast", False):
                image = self._improve_contrast(image)
            
            if enhancements.get("brightness", False):
                image = self._adjust_brightness(image)
            
            # Save enhanced image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), image)
            
            return {
                "success": True,
                "input_path": str(image_path),
                "output_path": str(output_path),
                "enhancements_applied": [k for k, v in enhancements.items() if v]
            }
        except Exception as e:
            self.logger.error(f"Error enhancing image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """Apply sharpening filter to image."""
        # Create sharpening kernel
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        
        # Apply kernel
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # Blend with original (70% sharpened, 30% original)
        result = cv2.addWeighted(image, 0.3, sharpened, 0.7, 0)
        
        return result
    
    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """Apply denoising to image."""
        # Use Non-local Means Denoising
        # For color images, use cv2.fastNlMeansDenoisingColored
        denoised = cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h=10,  # Filter strength
            hColor=10,  # Color filter strength
            templateWindowSize=7,
            searchWindowSize=21
        )
        
        return denoised
    
    def _improve_contrast(self, image: np.ndarray) -> np.ndarray:
        """Improve image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # Merge channels and convert back
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        result = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        return result
    
    def _adjust_brightness(self, image: np.ndarray, factor: float = 1.1) -> np.ndarray:
        """Adjust image brightness."""
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Adjust V channel (brightness)
        v = cv2.multiply(v, factor)
        v = np.clip(v, 0, 255).astype(np.uint8)
        
        # Merge and convert back
        hsv_enhanced = cv2.merge([h, s, v])
        result = cv2.cvtColor(hsv_enhanced, cv2.COLOR_HSV2BGR)
        
        return result


# Global image enhancer instance
image_enhancer = ImageEnhancer()
