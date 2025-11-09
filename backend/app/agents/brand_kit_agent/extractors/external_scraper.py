"""
External scraper for brand information.
Scrapes brand website if URL is provided (optional).
"""
import re
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse
import httpx

from app.services.logger import app_logger


class ExternalScraper:
    """Scrape brand information from external sources."""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize external scraper.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.logger = app_logger
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def scrape_website(
        self,
        url: str
    ) -> Dict:
        """
        Scrape brand information from website.
        
        Args:
            url: Website URL
        
        Returns:
            Dictionary with scraped information:
            - colors: List of HEX colors found
            - logo_url: Logo image URL if found
            - brand_name: Brand name if found
            - description: Meta description
            - social_links: Social media links
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme:
                url = f"https://{url}"
            
            self.logger.info(f"Scraping website: {url}")
            
            # Fetch page
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.get(url, follow_redirects=True)
                response.raise_for_status()
                html_content = response.text
            
            # Extract information
            colors = self._extract_colors_from_html(html_content)
            logo_url = self._extract_logo_url(html_content, url)
            brand_name = self._extract_brand_name(html_content)
            description = self._extract_meta_description(html_content)
            social_links = self._extract_social_links(html_content)
            
            return {
                "url": url,
                "colors": colors,
                "logo_url": logo_url,
                "brand_name": brand_name,
                "description": description,
                "social_links": social_links,
                "success": True
            }
            
        except httpx.TimeoutException:
            self.logger.warning(f"Timeout while scraping {url}")
            return {"url": url, "success": False, "error": "Request timeout"}
        except httpx.HTTPError as e:
            self.logger.warning(f"HTTP error while scraping {url}: {e}")
            return {"url": url, "success": False, "error": str(e)}
        except Exception as e:
            self.logger.error(f"Error scraping website {url}: {e}")
            return {"url": url, "success": False, "error": str(e)}
    
    def _extract_colors_from_html(self, html: str) -> List[str]:
        """
        Extract color codes from HTML (CSS, inline styles, etc.).
        
        Args:
            html: HTML content
        
        Returns:
            List of HEX color codes
        """
        colors = set()
        
        # Extract HEX colors (#RRGGBB or #RGB)
        hex_pattern = r'#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})\b'
        hex_matches = re.findall(hex_pattern, html)
        for match in hex_matches:
            if len(match) == 3:
                # Expand #RGB to #RRGGBB
                hex_color = f"#{match[0]}{match[0]}{match[1]}{match[1]}{match[2]}{match[2]}"
            else:
                hex_color = f"#{match}"
            colors.add(hex_color.upper())
        
        # Extract RGB colors
        rgb_pattern = r'rgb\((\d+),\s*(\d+),\s*(\d+)\)'
        rgb_matches = re.findall(rgb_pattern, html)
        for r, g, b in rgb_matches:
            hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}".upper()
            colors.add(hex_color)
        
        return list(colors)[:10]  # Limit to 10 colors
    
    def _extract_logo_url(self, html: str, base_url: str) -> Optional[str]:
        """
        Extract logo image URL from HTML.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative paths
        
        Returns:
            Logo URL or None
        """
        # Common logo selectors
        logo_patterns = [
            r'<img[^>]*class=["\'][^"\']*logo[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
            r'<img[^>]*src=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*logo[^"\']*["\']',
            r'<img[^>]*alt=["\'][^"\']*logo[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
        ]
        
        for pattern in logo_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                logo_path = matches[0]
                # Resolve relative URL
                if logo_path.startswith('http'):
                    return logo_path
                else:
                    return urljoin(base_url, logo_path)
        
        return None
    
    def _extract_brand_name(self, html: str) -> Optional[str]:
        """
        Extract brand name from HTML.
        
        Args:
            html: HTML content
        
        Returns:
            Brand name or None
        """
        # Try meta tags
        meta_pattern = r'<meta[^>]*property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)["\']'
        match = re.search(meta_pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try title tag
        title_pattern = r'<title[^>]*>([^<]+)</title>'
        match = re.search(title_pattern, html, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Clean up title (remove common suffixes)
            title = re.sub(r'\s*[-|]\s*.*$', '', title)
            return title
        
        return None
    
    def _extract_meta_description(self, html: str) -> Optional[str]:
        """
        Extract meta description from HTML.
        
        Args:
            html: HTML content
        
        Returns:
            Meta description or None
        """
        pattern = r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']'
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_social_links(self, html: str) -> Dict[str, str]:
        """
        Extract social media links from HTML.
        
        Args:
            html: HTML content
        
        Returns:
            Dictionary with social platform -> URL mapping
        """
        social_links = {}
        
        # Common social media patterns
        social_patterns = {
            'facebook': r'https?://(?:www\.)?(?:facebook|fb)\.com/[^\s"\'<>]+',
            'twitter': r'https?://(?:www\.)?(?:twitter|x)\.com/[^\s"\'<>]+',
            'instagram': r'https?://(?:www\.)?instagram\.com/[^\s"\'<>]+',
            'linkedin': r'https?://(?:www\.)?linkedin\.com/[^\s"\'<>]+',
            'youtube': r'https?://(?:www\.)?youtube\.com/[^\s"\'<>]+',
        }
        
        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                social_links[platform] = matches[0]
        
        return social_links


# Global external scraper instance
external_scraper = ExternalScraper()
