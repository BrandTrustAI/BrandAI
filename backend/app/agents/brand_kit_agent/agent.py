"""
Brand Kit Extraction Agent.
Orchestrates logo, color, and external scraping to extract brand information.
"""
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timezone

from app.agents.base_agent import BaseAgent
from app.agents.brand_kit_agent.extractors.logo_extractor import logo_extractor
from app.agents.brand_kit_agent.extractors.color_extractor import color_extractor
from app.agents.brand_kit_agent.extractors.external_scraper import external_scraper
from app.services.logger import app_logger
from app.services.storage_service import storage_service


class BrandKitAgent(BaseAgent):
    """Agent for extracting brand kit information."""
    
    def __init__(self):
        """Initialize brand kit agent."""
        super().__init__()
        self.logger = app_logger
        self.logo_extractor = logo_extractor
        self.color_extractor = color_extractor
        self.external_scraper = external_scraper
    
    def execute(
        self,
        brand_logo_path: Optional[Path] = None,
        product_image_path: Optional[Path] = None,
        brand_website_url: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Execute brand kit extraction (implements BaseAgent interface).
        
        Args:
            brand_logo_path: Path to brand logo image
            product_image_path: Path to product image
            brand_website_url: Optional brand website URL
            **kwargs: Additional arguments
        
        Returns:
            Standardized result dictionary
        """
        self.log_start("brand_kit_extraction", **kwargs)
        
        try:
            brand_kit = self.extract_brand_kit(
                brand_logo_path=brand_logo_path,
                product_image_path=product_image_path,
                brand_website_url=brand_website_url
            )
            
            summary = self.get_brand_summary(brand_kit)
            
            self.log_complete("brand_kit_extraction", **summary)
            
            return self.create_result(
                success=True,
                data=brand_kit,
                metadata=summary
            )
            
        except Exception as e:
            self.log_error("brand_kit_extraction", e, **kwargs)
            return self.create_result(
                success=False,
                error=str(e)
            )
    
    def extract_brand_kit(
        self,
        brand_logo_path: Optional[Path] = None,
        product_image_path: Optional[Path] = None,
        brand_website_url: Optional[str] = None
    ) -> Dict:
        """
        Extract complete brand kit information.
        
        Args:
            brand_logo_path: Path to brand logo image
            product_image_path: Path to product image
            brand_website_url: Optional brand website URL
        
        Returns:
            Dictionary with brand kit information:
            - logo: Logo information
            - colors: Color palette
            - website: Website information (if URL provided)
            - extracted_at: Timestamp
        """
        self.logger.info("Starting brand kit extraction")
        
        brand_kit = {
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "logo": {},
            "colors": {},
            "website": {}
        }
        
        # Extract logo information
        if brand_logo_path and brand_logo_path.exists():
            self.logger.info(f"Extracting logo from: {brand_logo_path}")
            logo_info = self.logo_extractor.analyze_logo_file(brand_logo_path)
            brand_kit["logo"] = logo_info
        
        # Extract colors from logo and product image
        color_sources = []
        if brand_logo_path and brand_logo_path.exists():
            color_sources.append(brand_logo_path)
        if product_image_path and product_image_path.exists():
            color_sources.append(product_image_path)
        
        if color_sources:
            self.logger.info(f"Extracting colors from {len(color_sources)} image(s)")
            if len(color_sources) == 1:
                color_info = self.color_extractor.extract_colors(color_sources[0])
            else:
                color_info = self.color_extractor.extract_from_multiple_images(color_sources)
            
            if "error" not in color_info:
                brand_kit["colors"] = color_info
        
        # Scrape website if URL provided
        if brand_website_url:
            self.logger.info(f"Scraping website: {brand_website_url}")
            website_info = self.external_scraper.scrape_website(brand_website_url)
            brand_kit["website"] = website_info
            
            # Merge website colors with extracted colors
            if website_info.get("success") and website_info.get("colors"):
                website_colors = website_info["colors"]
                if "color_palette" in brand_kit["colors"]:
                    # Combine colors, avoiding duplicates
                    existing = set(brand_kit["colors"]["color_palette"])
                    new_colors = [c for c in website_colors if c not in existing]
                    brand_kit["colors"]["color_palette"].extend(new_colors[:5])
                else:
                    brand_kit["colors"]["color_palette"] = website_colors[:5]
                    brand_kit["colors"]["primary_color"] = website_colors[0] if website_colors else None
        
        self.logger.info("Brand kit extraction completed")
        return brand_kit
    
    def extract_from_uploads(
        self,
        brand_logo_file: Optional[bytes] = None,
        product_image_file: Optional[bytes] = None,
        brand_website_url: Optional[str] = None,
        run_id: str = None
    ) -> Dict:
        """
        Extract brand kit from uploaded files.
        
        Args:
            brand_logo_file: Brand logo file content as bytes
            product_image_file: Product image file content as bytes
            brand_website_url: Optional brand website URL
            run_id: Run ID for organizing files
        
        Returns:
            Brand kit dictionary
        """
        logo_path = None
        product_path = None
        
        try:
            # Save uploaded files temporarily
            if brand_logo_file:
                logo_path = storage_service.save_brand_asset(
                    brand_logo_file,
                    "logo_upload.png",
                    "logo"
                )
                self.logger.info(f"Saved logo to: {logo_path}")
            
            if product_image_file:
                product_path = storage_service.save_brand_asset(
                    product_image_file,
                    "product_upload.jpg",
                    "product"
                )
                self.logger.info(f"Saved product image to: {product_path}")
            
            # Extract brand kit
            brand_kit = self.extract_brand_kit(
                brand_logo_path=logo_path,
                product_image_path=product_path,
                brand_website_url=brand_website_url
            )
            
            return brand_kit
            
        except Exception as e:
            self.logger.error(f"Error extracting brand kit from uploads: {e}")
            return {
                "error": str(e),
                "extracted_at": datetime.now(timezone.utc).isoformat()
            }
    
    def get_brand_summary(self, brand_kit: Dict) -> Dict:
        """
        Get a summary of brand kit information.
        
        Args:
            brand_kit: Brand kit dictionary
        
        Returns:
            Summary dictionary
        """
        summary = {
            "has_logo": bool(brand_kit.get("logo")),
            "has_colors": bool(brand_kit.get("colors")),
            "has_website": bool(brand_kit.get("website", {}).get("success")),
            "primary_color": None,
            "color_count": 0
        }
        
        if brand_kit.get("colors"):
            summary["primary_color"] = brand_kit["colors"].get("primary_color")
            summary["color_count"] = len(brand_kit["colors"].get("color_palette", []))
        
        return summary


# Global brand kit agent instance
brand_kit_agent = BrandKitAgent()
