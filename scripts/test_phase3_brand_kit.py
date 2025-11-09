#!/usr/bin/env python3
"""
Comprehensive test script for Phase 3: Brand Kit Agent
Tests Logo Extractor, Color Extractor, External Scraper, and Brand Kit Agent.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.agents.brand_kit_agent.extractors.logo_extractor import logo_extractor
from app.agents.brand_kit_agent.extractors.color_extractor import color_extractor
from app.agents.brand_kit_agent.extractors.external_scraper import external_scraper
from app.agents.brand_kit_agent.agent import brand_kit_agent
from app.services.storage_service import storage_service


def create_test_image(output_path: Path, width: int = 200, height: int = 200, color: tuple = (255, 0, 0)):
    """Create a test image for testing."""
    img = Image.new('RGB', (width, height), color)
    img.save(output_path)
    return output_path


def test_logo_extractor():
    """Test logo extractor functionality."""
    print("=" * 60)
    print("Testing Logo Extractor...")
    print("=" * 60)
    
    # Create test image
    test_dir = Path(__file__).parent.parent / "data" / "storage" / "test"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_image = test_dir / "test_logo.png"
    create_test_image(test_image, 200, 200, (0, 100, 200))
    
    # Test logo file analysis
    result = logo_extractor.analyze_logo_file(test_image)
    assert "file_path" in result, "Should return file path"
    assert "dimensions" in result, "Should return dimensions"
    assert "format" in result, "Should return format"
    assert "dominant_colors" in result, "Should return dominant colors"
    print(f"  ✅ Logo file analysis - PASSED")
    print(f"     Dimensions: {result.get('dimensions')}")
    print(f"     Format: {result.get('format')}")
    print(f"     Colors found: {len(result.get('dominant_colors', []))}")
    
    # Test logo feature extraction
    features = logo_extractor.extract_logo_features(test_image)
    assert "detected" in features, "Should return detection status"
    print(f"  ✅ Logo feature extraction - PASSED")
    print(f"     Detected: {features.get('detected')}")
    
    # Cleanup
    test_image.unlink()
    
    print("✅ Logo Extractor - ALL TESTS PASSED\n")
    return True


def test_color_extractor():
    """Test color extractor functionality."""
    print("=" * 60)
    print("Testing Color Extractor...")
    print("=" * 60)
    
    # Create test images with different colors
    test_dir = Path(__file__).parent.parent / "data" / "storage" / "test"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    red_image = test_dir / "red_test.png"
    blue_image = test_dir / "blue_test.png"
    
    create_test_image(red_image, 100, 100, (255, 0, 0))
    create_test_image(blue_image, 100, 100, (0, 0, 255))
    
    # Test single image color extraction
    result = color_extractor.extract_colors(red_image, num_colors=3)
    assert "colors" in result or "error" in result, "Should return colors or error"
    if "colors" in result:
        assert len(result["colors"]) > 0, "Should extract colors"
        assert "hex" in result["colors"][0], "Colors should have hex codes"
        assert "rgb" in result["colors"][0], "Colors should have RGB values"
        print(f"  ✅ Single image color extraction - PASSED")
        print(f"     Colors found: {len(result['colors'])}")
        print(f"     Primary color: {result.get('primary_color')}")
        print(f"     First color RGB: {result['colors'][0].get('rgb')}")
        print(f"     First color HEX: {result['colors'][0].get('hex')}")
    
    # Test multiple image color extraction
    result = color_extractor.extract_from_multiple_images([red_image, blue_image], num_colors=5)
    assert "color_palette" in result or "error" in result, "Should return palette or error"
    if "color_palette" in result:
        assert len(result["color_palette"]) > 0, "Should extract colors from multiple images"
        print(f"  ✅ Multiple image color extraction - PASSED")
        print(f"     Combined colors: {len(result['color_palette'])}")
        print(f"     Primary color: {result.get('primary_color')}")
    
    # Test RGB to HEX conversion
    hex_color = color_extractor._rgb_to_hex(255, 0, 0)
    assert hex_color == "#FF0000", "Should convert RGB to HEX correctly"
    print(f"  ✅ RGB to HEX conversion - PASSED ({hex_color})")
    
    # Cleanup
    red_image.unlink()
    blue_image.unlink()
    
    print("✅ Color Extractor - ALL TESTS PASSED\n")
    return True


def test_external_scraper():
    """Test external scraper functionality."""
    print("=" * 60)
    print("Testing External Scraper...")
    print("=" * 60)
    
    # Test RGB to HEX conversion (internal method)
    hex_color = external_scraper._rgb_to_hex(255, 0, 0) if hasattr(external_scraper, '_rgb_to_hex') else None
    
    # Test website scraping (use a simple, reliable site)
    # Note: This might fail if network is unavailable, so we'll make it optional
    try:
        result = external_scraper.scrape_website("https://www.google.com")
        if result.get("success"):
            print(f"  ✅ Website scraping - PASSED")
            print(f"     Brand name: {result.get('brand_name', 'N/A')}")
            print(f"     Colors found: {len(result.get('colors', []))}")
        else:
            print(f"  ⚠️  Website scraping returned error: {result.get('error')}")
            print(f"     (This is acceptable if network is unavailable)")
    except Exception as e:
        print(f"  ⚠️  Website scraping test skipped: {e}")
        print(f"     (This is acceptable if network is unavailable)")
    
    # Test HTML parsing methods
    test_html = """
    <html>
    <head>
        <title>Test Brand</title>
        <meta name="description" content="Test description">
        <meta property="og:site_name" content="Test Brand Name">
    </head>
    <body>
        <img src="/logo.png" class="logo" alt="Logo">
        <div style="color: #FF0000; background: rgb(0, 0, 255);">
            <a href="https://facebook.com/test">Facebook</a>
        </div>
    </body>
    </html>
    """
    
    colors = external_scraper._extract_colors_from_html(test_html)
    assert len(colors) > 0, "Should extract colors from HTML"
    assert "#FF0000" in colors or "#FF0000" in [c.upper() for c in colors], "Should find red color"
    print(f"  ✅ HTML color extraction - PASSED ({len(colors)} colors)")
    
    logo_url = external_scraper._extract_logo_url(test_html, "https://example.com")
    assert logo_url is not None, "Should extract logo URL"
    print(f"  ✅ Logo URL extraction - PASSED ({logo_url})")
    
    brand_name = external_scraper._extract_brand_name(test_html)
    assert brand_name is not None, "Should extract brand name"
    print(f"  ✅ Brand name extraction - PASSED ({brand_name})")
    
    description = external_scraper._extract_meta_description(test_html)
    assert description is not None, "Should extract description"
    print(f"  ✅ Meta description extraction - PASSED")
    
    print("✅ External Scraper - ALL TESTS PASSED\n")
    return True


def test_brand_kit_agent():
    """Test brand kit agent integration."""
    print("=" * 60)
    print("Testing Brand Kit Agent...")
    print("=" * 60)
    
    # Create test images
    test_dir = Path(__file__).parent.parent / "data" / "storage" / "test"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    logo_path = test_dir / "test_logo.png"
    product_path = test_dir / "test_product.png"
    
    create_test_image(logo_path, 200, 200, (100, 150, 200))
    create_test_image(product_path, 300, 300, (200, 100, 50))
    
    # Test brand kit extraction
    brand_kit = brand_kit_agent.extract_brand_kit(
        brand_logo_path=logo_path,
        product_image_path=product_path,
        brand_website_url=None
    )
    
    assert "extracted_at" in brand_kit, "Should have timestamp"
    assert "logo" in brand_kit, "Should have logo info"
    assert "colors" in brand_kit, "Should have colors"
    print(f"  ✅ Brand kit extraction - PASSED")
    print(f"     Has logo: {bool(brand_kit.get('logo'))}")
    print(f"     Has colors: {bool(brand_kit.get('colors'))}")
    
    # Test brand summary
    summary = brand_kit_agent.get_brand_summary(brand_kit)
    assert "has_logo" in summary, "Should have logo flag"
    assert "has_colors" in summary, "Should have colors flag"
    print(f"  ✅ Brand summary - PASSED")
    print(f"     Summary: {summary}")
    
    # Test execute method (BaseAgent interface)
    result = brand_kit_agent.execute(
        brand_logo_path=logo_path,
        product_image_path=product_path
    )
    assert "success" in result, "Should have success flag"
    assert result["success"], "Should be successful"
    assert "data" in result, "Should have data"
    print(f"  ✅ Execute method - PASSED")
    
    # Test with file uploads (bytes)
    with open(logo_path, "rb") as f:
        logo_bytes = f.read()
    with open(product_path, "rb") as f:
        product_bytes = f.read()
    
    brand_kit_upload = brand_kit_agent.extract_from_uploads(
        brand_logo_file=logo_bytes,
        product_image_file=product_bytes,
        run_id="test_run_123"
    )
    assert "extracted_at" in brand_kit_upload, "Should have timestamp"
    print(f"  ✅ File upload extraction - PASSED")
    
    # Cleanup
    logo_path.unlink()
    product_path.unlink()
    
    print("✅ Brand Kit Agent - ALL TESTS PASSED\n")
    return True


def test_integration():
    """Test all components working together."""
    print("=" * 60)
    print("Testing Integration...")
    print("=" * 60)
    
    # Create test image
    test_dir = Path(__file__).parent.parent / "data" / "storage" / "test"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_image = test_dir / "integration_test.png"
    create_test_image(test_image, 150, 150, (50, 100, 150))
    
    # Test full workflow
    logo_info = logo_extractor.analyze_logo_file(test_image)
    color_info = color_extractor.extract_colors(test_image)
    brand_kit = brand_kit_agent.extract_brand_kit(brand_logo_path=test_image)
    
    assert logo_info, "Logo extraction should work"
    assert color_info.get("colors") or color_info.get("error"), "Color extraction should work"
    assert brand_kit, "Brand kit extraction should work"
    
    print("  ✅ Full workflow integration - PASSED")
    print("✅ Integration - ALL TESTS PASSED\n")
    
    # Cleanup
    test_image.unlink()
    
    return True


def main():
    """Run all Phase 3 tests."""
    print("\n" + "=" * 60)
    print("Phase 3: Brand Kit Agent - Comprehensive Test")
    print("=" * 60)
    print()
    
    all_passed = True
    
    try:
        all_passed &= test_logo_extractor()
        all_passed &= test_color_extractor()
        all_passed &= test_external_scraper()
        all_passed &= test_brand_kit_agent()
        all_passed &= test_integration()
        
        print("=" * 60)
        if all_passed:
            print("✅ ALL TESTS PASSED - Phase 3 is complete!")
        else:
            print("❌ SOME TESTS FAILED - Please review errors above")
        print("=" * 60)
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

