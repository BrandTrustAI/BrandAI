"""
Test script for Phase 6: Refinement Agent
Tests the refinement agent with critique feedback.
"""
import sys
import os
from pathlib import Path
from typing import Dict

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

os.environ.setdefault("APP_ENV", "development")

from app.agents.refinement_agent.agent import refinement_agent
from app.agents.critique_agent.agent import critique_agent
from app.agents.brand_kit_agent.agent import BrandKitAgent
from app.services.logger import app_logger


def create_mock_critique_feedback(ad_path: str, overall_score: float = 0.5) -> Dict:
    """Create mock critique feedback for testing."""
    return {
        "run_id": "test_run_123",
        "total_variations": 1,
        "passed_variations": 0 if overall_score < 0.7 else 1,
        "failed_variations": 1 if overall_score < 0.7 else 0,
        "all_variations": [
            {
                "variation_id": "var_1",
                "file_path": ad_path,
                "overall_score": overall_score,
                "passed": overall_score >= 0.7,
                "rank": 1,
                "scorecard": [
                    {
                        "dimension": "brand_alignment",
                        "score": 0.5,
                        "feedback": "Logo detected but colors not well represented",
                        "issues": ["Brand colors not well represented"]
                    },
                    {
                        "dimension": "visual_quality",
                        "score": 0.6,
                        "feedback": "Image is sharp but has some artifacts",
                        "issues": ["Visual artifacts present"]
                    },
                    {
                        "dimension": "message_clarity",
                        "score": 0.7,
                        "feedback": "Product is visible and message is clear",
                        "issues": []
                    },
                    {
                        "dimension": "safety_ethics",
                        "score": 1.0,
                        "feedback": "No harmful content detected",
                        "issues": []
                    }
                ]
            }
        ]
    }


def test_refinement_agent():
    """Test the refinement agent."""
    
    print("=" * 70)
    print("Phase 6: Refinement Agent - Test")
    print("=" * 70)
    print()
    
    # Test directory
    test_dir = Path("/Users/udaygattu/Documents/Hackathon/BrandAI-fork/data/storage/test_generation")
    images_dir = test_dir / "images"
    
    if not images_dir.exists():
        print(f"❌ Test directory not found: {images_dir}")
        return
    
    # Find test images
    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
    
    if not image_files:
        print(f"❌ No test images found in {images_dir}")
        return
    
    test_image = image_files[0]
    print(f"📸 Using test image: {test_image.name}")
    print()
    
    # Test 1: Get real critique feedback
    print("-" * 70)
    print("TEST 1: Get Real Critique Feedback")
    print("-" * 70)
    print()
    
    try:
        # Create a simple brand kit
        brand_kit = {
            "brand_name": "Nike",
            "colors": {
                "color_palette": ["#000000", "#FFFFFF", "#FF0000"],
                "primary_color": "#000000"
            }
        }
        
        # Run critique agent
        critique_result = critique_agent.execute(
            ad_paths=[str(test_image)],
            brand_kit=brand_kit,
            media_type="image",
            user_prompt="Nike shoe advertisement"
        )
        
        if not critique_result.get("success"):
            print(f"❌ Critique failed: {critique_result.get('error', 'Unknown error')}")
            return
        
        # Extract critique report from data
        data = critique_result.get("data", {})
        critique_report = data.get("critique_report")
        
        if not critique_report:
            print("❌ No critique report generated")
            print(f"   Debug - critique_result keys: {critique_result.keys()}")
            print(f"   Debug - data keys: {data.keys() if data else 'No data'}")
            return
        
        # Convert to dict for refinement agent
        if hasattr(critique_report, 'model_dump'):
            critique_feedback = critique_report.model_dump()
        elif hasattr(critique_report, 'dict'):
            critique_feedback = critique_report.dict()
        else:
            critique_feedback = critique_report
        
        print(f"✅ Critique completed!")
        print(f"   Overall Score: {critique_feedback['all_variations'][0]['overall_score']:.2f}")
        print()
        
    except Exception as e:
        print(f"❌ Error getting critique feedback: {e}")
        import traceback
        traceback.print_exc()
        # Use mock feedback instead
        print("Using mock critique feedback instead...")
        critique_feedback = create_mock_critique_feedback(str(test_image), overall_score=0.55)
        print()
    
    # Test 2: Test Refinement Agent
    print("-" * 70)
    print("TEST 2: Refinement Agent")
    print("-" * 70)
    print()
    
    try:
        original_prompt = "Nike shoe advertisement"
        
        refinement_result = refinement_agent.execute(
            ad_path=str(test_image),
            critique_feedback=critique_feedback,
            original_prompt=original_prompt,
            brand_kit=brand_kit,
            media_type="image",
            run_id="test_run_123"
        )
        
        print(f"✅ Refinement completed!")
        print(f"   Success: {refinement_result.get('success', False)}")
        print(f"   Strategy: {refinement_result.get('strategy', 'unknown')}")
        print(f"   Message: {refinement_result.get('message', 'N/A')}")
        
        if refinement_result.get("refined_ad_path"):
            print(f"   Refined Ad Path: {refinement_result.get('refined_ad_path')}")
        
        if refinement_result.get("refined_prompt"):
            print(f"   Refined Prompt: {refinement_result.get('refined_prompt')}")
        
        metadata = refinement_result.get("metadata", {})
        if metadata:
            print(f"   Metadata: {metadata}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error in refinement agent: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Test different scenarios
    print("-" * 70)
    print("TEST 3: Different Refinement Scenarios")
    print("-" * 70)
    print()
    
    scenarios = [
        ("High Score (Approve)", 0.85),
        ("Medium Score (Enhance)", 0.55),
        ("Low Score (Regenerate)", 0.45),
        ("Very Low Score (Reject)", 0.25)
    ]
    
    for scenario_name, score in scenarios:
        print(f"📋 Scenario: {scenario_name} (Score: {score:.2f})")
        
        mock_feedback = create_mock_critique_feedback(str(test_image), overall_score=score)
        
        try:
            result = refinement_agent.execute(
                ad_path=str(test_image),
                critique_feedback=mock_feedback,
                original_prompt=original_prompt,
                brand_kit=brand_kit,
                media_type="image"
            )
            
            print(f"   Strategy: {result.get('strategy', 'unknown')}")
            print(f"   Success: {result.get('success', False)}")
            print()
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    print("=" * 70)
    print("Phase 6 Refinement Agent Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_refinement_agent()

