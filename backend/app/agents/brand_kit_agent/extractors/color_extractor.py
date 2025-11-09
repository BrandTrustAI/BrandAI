"""
Color extraction from brand assets.
Extracts dominant colors and converts them to HEX codes.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter
from PIL import Image

from app.services.logger import app_logger


class ColorExtractor:
    """Extract color palette from brand assets."""
    
    def __init__(self):
        """Initialize color extractor."""
        self.logger = app_logger
    
    def extract_colors(
        self,
        image_path: Path,
        num_colors: int = 5,
        method: str = "kmeans"
    ) -> Dict:
        """
        Extract dominant colors from an image.
        
        Args:
            image_path: Path to image file
            num_colors: Number of colors to extract
            method: Extraction method ('kmeans' or 'histogram')
        
        Returns:
            Dictionary with color information:
            - colors: List of color dicts with hex, rgb, frequency
            - primary_color: Primary color (hex)
            - color_palette: List of hex codes
        """
        try:
            # Read image
            image = cv2.imread(str(image_path))
            if image is None:
                self.logger.warning(f"Could not read image: {image_path}")
                return {"error": "Could not read image"}
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            if method == "kmeans":
                colors = self._extract_kmeans(image_rgb, num_colors)
            else:
                colors = self._extract_histogram(image_rgb, num_colors)
            
            if not colors:
                return {"error": "No colors extracted"}
            
            # Sort by frequency
            colors.sort(key=lambda x: x.get("frequency", 0), reverse=True)
            
            # Extract primary color and palette
            primary_color = colors[0]["hex"] if colors else None
            color_palette = [c["hex"] for c in colors]
            
            return {
                "colors": colors,
                "primary_color": primary_color,
                "color_palette": color_palette,
                "num_colors": len(colors)
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting colors: {e}")
            return {"error": str(e)}
    
    def _extract_kmeans(
        self,
        image: np.ndarray,
        k: int
    ) -> List[Dict]:
        """
        Extract colors using K-means clustering.
        
        Args:
            image: Image as numpy array (RGB)
            k: Number of clusters
        
        Returns:
            List of color dictionaries
        """
        try:
            # Reshape image to 2D array of pixels
            pixels = image.reshape(-1, 3)
            
            # Convert to float32
            pixels = np.float32(pixels)
            
            # Apply K-means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(
                pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
            )
            
            # Convert centers to uint8
            centers = np.uint8(centers)
            
            # Calculate frequencies
            unique, counts = np.unique(labels, return_counts=True)
            total_pixels = len(labels)
            
            colors = []
            for i, center in enumerate(centers):
                r, g, b = center
                frequency = counts[i] / total_pixels if i < len(counts) else 0
                
                colors.append({
                    "rgb": (int(r), int(g), int(b)),
                    "hex": self._rgb_to_hex(r, g, b),
                    "frequency": float(frequency)
                })
            
            return colors
            
        except Exception as e:
            self.logger.error(f"Error in K-means extraction: {e}")
            return []
    
    def _extract_histogram(
        self,
        image: np.ndarray,
        num_colors: int
    ) -> List[Dict]:
        """
        Extract colors using histogram analysis.
        
        Args:
            image: Image as numpy array (RGB)
            num_colors: Number of colors to extract
        
        Returns:
            List of color dictionaries
        """
        try:
            # Flatten image
            pixels = image.reshape(-1, 3)
            
            # Quantize colors (reduce to 256 colors)
            quantized = (pixels // 32) * 32
            
            # Count color frequencies
            color_counts = Counter(map(tuple, quantized))
            
            # Get most common colors
            most_common = color_counts.most_common(num_colors)
            total_pixels = len(pixels)
            
            colors = []
            for (r, g, b), count in most_common:
                frequency = count / total_pixels
                colors.append({
                    "rgb": (int(r), int(g), int(b)),
                    "hex": self._rgb_to_hex(r, g, b),
                    "frequency": float(frequency)
                })
            
            return colors
            
        except Exception as e:
            self.logger.error(f"Error in histogram extraction: {e}")
            return []
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """
        Convert RGB to HEX color code.
        
        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        
        Returns:
            HEX color code (e.g., "#FF0000")
        """
        return f"#{r:02x}{g:02x}{b:02x}".upper()
    
    def extract_from_multiple_images(
        self,
        image_paths: List[Path],
        num_colors: int = 5
    ) -> Dict:
        """
        Extract colors from multiple images and combine.
        
        Args:
            image_paths: List of image paths
            num_colors: Number of colors per image
        
        Returns:
            Combined color palette
        """
        all_colors = []
        
        for image_path in image_paths:
            result = self.extract_colors(image_path, num_colors)
            if "colors" in result:
                all_colors.extend(result["colors"])
        
        if not all_colors:
            return {"error": "No colors extracted from images"}
        
        # Aggregate colors by frequency
        color_freq = {}
        for color_info in all_colors:
            hex_color = color_info["hex"]
            if hex_color in color_freq:
                color_freq[hex_color] += color_info["frequency"]
            else:
                color_freq[hex_color] = color_info["frequency"]
        
        # Sort by frequency
        sorted_colors = sorted(color_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Get top colors
        top_colors = sorted_colors[:num_colors]
        
        color_palette = [hex_color for hex_color, _ in top_colors]
        
        return {
            "color_palette": color_palette,
            "primary_color": color_palette[0] if color_palette else None,
            "num_colors": len(color_palette)
        }


# Global color extractor instance
color_extractor = ColorExtractor()
