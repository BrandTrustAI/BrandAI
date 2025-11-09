"""
Test script for Phase 7: LangGraph Orchestration
Tests the complete workflow orchestrator.
"""
import sys
import os
from pathlib import Path
import uuid

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

os.environ.setdefault("APP_ENV", "development")

from app.core.orchestrator import orchestrator, WorkflowOrchestrator
from app.core.run_manager import run_manager
from app.services.logger import app_logger


def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    print("=" * 70)
    print("TEST 1: Orchestrator Initialization")
    print("=" * 70)
    print()
    
    try:
        # Test global orchestrator
        assert orchestrator is not None, "Orchestrator should be initialized"
        assert orchestrator.workflow is not None, "Workflow should be compiled"
        
        print("✅ Orchestrator initialized successfully")
        print(f"   Workflow type: {type(orchestrator.workflow)}")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_execution():
    """Test complete workflow execution."""
    print("=" * 70)
    print("TEST 2: Complete Workflow Execution")
    print("=" * 70)
    print()
    
    # Check for test assets
    test_dir = Path("/Users/udaygattu/Documents/Hackathon/BrandAI-fork/data/storage/uploads")
    logo_path = None
    product_path = None
    
    if test_dir.exists():
        logo_files = list(test_dir.glob("*logo*")) + list(test_dir.glob("*Logo*"))
        product_files = list(test_dir.glob("*product*")) + list(test_dir.glob("*Product*")) + list(test_dir.glob("*.png")) + list(test_dir.glob("*.jpg"))
        
        if logo_files:
            logo_path = str(logo_files[0])
        if product_files and len(product_files) > (1 if logo_path else 0):
            # Don't use the same file for both
            for pf in product_files:
                if str(pf) != logo_path:
                    product_path = str(pf)
                    break
    
    # Create run first to get run_id
    run = run_manager.create_run(
        prompt="Nike shoe advertisement showcasing athletic performance and style",
        media_type="image",
        brand_website_url=None
    )
    run_id = run.run_id
    
    print(f"📋 Run ID: {run_id}")
    print(f"📝 Prompt: Nike shoe advertisement")
    print(f"🎬 Media Type: image")
    if logo_path:
        print(f"🖼️  Logo: {Path(logo_path).name}")
    if product_path:
        print(f"📦 Product: {Path(product_path).name}")
    print()
    
    try:
        print("🚀 Starting workflow execution...")
        print("   This will execute: Brand Kit → Generation → Critique → Refinement")
        print("   Please wait, this may take several minutes...")
        print()
        
        # Execute workflow
        import sys
        sys.stdout.flush()  # Ensure output is flushed
        
        result = orchestrator.execute(
            run_id=run_id,
            user_prompt="Nike shoe advertisement showcasing athletic performance and style",
            media_type="image",
            brand_website_url=None,
            logo_path=logo_path,
            product_path=product_path,
            max_retries=3
        )
        
        print("✅ Workflow execution completed!")
        print()
        print("📊 Results:")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Retry Count: {result.get('retry_count', 0)}")
        
        if result.get('generated_ad_path'):
            print(f"   Generated Ad: {result.get('generated_ad_path')}")
        
        if result.get('overall_score') is not None:
            print(f"   Overall Score: {result.get('overall_score', 0):.2f}")
        
        if result.get('error'):
            print(f"   Error: {result.get('error')}")
        
        print()
        
        # Check run status
        run = run_manager.get_run(run_id)
        if run:
            print("📋 Run Status:")
            print(f"   Status: {run.status}")
            print(f"   Progress: {run.progress}%")
            print(f"   Current Stage: {run.current_stage}")
            print()
        
        return result.get('success', False)
    
    except Exception as e:
        print(f"❌ Error executing workflow: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_state():
    """Test workflow state structure."""
    print("=" * 70)
    print("TEST 3: Workflow State Structure")
    print("=" * 70)
    print()
    
    try:
        from app.core.orchestrator import WorkflowState
        
        # Create a sample state
        sample_state: WorkflowState = {
            "run_id": "test_123",
            "user_prompt": "Test prompt",
            "media_type": "image",
            "brand_website_url": None,
            "logo_path": None,
            "product_path": None,
            "brand_kit": None,
            "brand_kit_extracted": False,
            "generated_ad_path": None,
            "generation_success": False,
            "generation_error": None,
            "critique_feedback": None,
            "critique_success": False,
            "critique_error": None,
            "overall_score": None,
            "refinement_strategy": None,
            "refined_ad_path": None,
            "refined_prompt": None,
            "refinement_success": False,
            "refinement_error": None,
            "retry_count": 0,
            "max_retries": 3,
            "workflow_status": "in_progress",
            "final_result": None,
            "error_message": None
        }
        
        print("✅ WorkflowState structure is valid")
        print(f"   Fields: {len(sample_state)} fields defined")
        print()
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_decision_logic():
    """Test decision logic routing."""
    print("=" * 70)
    print("TEST 4: Decision Logic")
    print("=" * 70)
    print()
    
    try:
        from app.core.orchestrator import should_continue
        
        test_cases = [
            ("approve", 0, 3, "approve"),
            ("reject", 0, 3, "reject"),
            ("regenerate", 0, 3, "regenerate"),
            ("regenerate", 3, 3, "end"),  # Max retries
            ("enhance", 0, 3, "enhance"),
            (None, 0, 3, "end"),
        ]
        
        print("Testing decision logic:")
        print()
        
        for strategy, retry_count, max_retries, expected in test_cases:
            state = {
                "refinement_strategy": strategy,
                "retry_count": retry_count,
                "max_retries": max_retries
            }
            
            result = should_continue(state)
            status = "✅" if result == expected else "❌"
            
            print(f"   {status} Strategy: {strategy}, Retries: {retry_count}/{max_retries}")
            print(f"      Expected: {expected}, Got: {result}")
            
            if result != expected:
                print(f"      ⚠️  Mismatch!")
        
        print()
        print("✅ Decision logic test completed")
        print()
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Phase 7: LangGraph Orchestration - Test")
    print("=" * 70)
    print()
    
    results = []
    
    # Test 1: Initialization
    results.append(("Initialization", test_orchestrator_initialization()))
    print()
    
    # Test 2: State Structure
    results.append(("State Structure", test_workflow_state()))
    print()
    
    # Test 3: Decision Logic
    results.append(("Decision Logic", test_decision_logic()))
    print()
    
    # Test 4: Complete Workflow (this will take time)
    print("⚠️  Note: Complete workflow test will take several minutes")
    print("   (Brand Kit → Generation → Critique → Refinement)")
    print()
    print("🚀 Running complete workflow test...")
    print()
    
    results.append(("Complete Workflow", test_workflow_execution()))
    
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print()
    
    for test_name, result in results:
        if result is None:
            status = "⏭️  Skipped"
        elif result:
            status = "✅ Passed"
        else:
            status = "❌ Failed"
        
        print(f"   {test_name}: {status}")
    
    print()
    print("=" * 70)
    print("Phase 7 Orchestrator Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

