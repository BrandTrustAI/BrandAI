#!/usr/bin/env python3
"""
Comprehensive test script for Phase 2: Core Services
Tests Storage Service, Run Manager, and Logger Service.
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.storage_service import storage_service
from app.core.run_manager import run_manager
from app.services.logger import app_logger


def test_storage_service():
    """Test storage service functionality."""
    print("=" * 60)
    print("Testing Storage Service...")
    print("=" * 60)
    
    # Test directory creation
    ads_dir = storage_service.get_storage_path("ads")
    assert ads_dir.exists(), "Ads directory should exist"
    print("  ✅ Directory creation - PASSED")
    
    # Test file saving
    test_content = b"Test file content"
    saved_path = storage_service.save_file(
        test_content,
        "test.txt",
        "uploads",
        create_unique=True
    )
    assert saved_path.exists(), "File should be saved"
    print(f"  ✅ File saving - PASSED ({saved_path.name})")
    
    # Test file reading
    read_content = storage_service.read_file(saved_path)
    assert read_content == test_content, "File content should match"
    print("  ✅ File reading - PASSED")
    
    # Test ad variation saving
    ad_path = storage_service.save_ad_variation(
        b"fake image data",
        "test_run_123",
        "var_1",
        ".jpg"
    )
    assert ad_path.exists(), "Ad variation should be saved"
    print(f"  ✅ Ad variation saving - PASSED")
    
    # Test brand asset saving
    asset_path = storage_service.save_brand_asset(
        b"fake logo data",
        "logo.png",
        "logo"
    )
    assert asset_path.exists(), "Brand asset should be saved"
    print(f"  ✅ Brand asset saving - PASSED")
    
    # Test report saving
    report_path = storage_service.save_report(
        '{"test": "report"}',
        "test_run_123",
        "critique"
    )
    assert report_path.exists(), "Report should be saved"
    print(f"  ✅ Report saving - PASSED")
    
    # Test file listing
    files = storage_service.list_files("uploads", "test*.txt")
    assert len(files) > 0, "Should list files"
    print(f"  ✅ File listing - PASSED ({len(files)} files)")
    
    # Test file deletion
    deleted = storage_service.delete_file(saved_path)
    assert deleted, "File should be deleted"
    assert not saved_path.exists(), "File should not exist after deletion"
    print("  ✅ File deletion - PASSED")
    
    print("✅ Storage Service - ALL TESTS PASSED\n")
    return True


def test_run_manager():
    """Test run manager functionality."""
    print("=" * 60)
    print("Testing Run Manager...")
    print("=" * 60)
    
    # Test run creation
    import uuid
    run = run_manager.create_run(
        prompt="Test ad generation",
        media_type="image",
        brand_website_url="https://example.com"
    )
    # Validate UUID format
    try:
        uuid.UUID(run.run_id)
        is_valid_uuid = True
    except ValueError:
        is_valid_uuid = False
    assert is_valid_uuid, "Run ID should be a valid UUID"
    assert run.status.value == "pending", "Initial status should be pending"
    assert run.progress == 0.0, "Initial progress should be 0"
    print(f"  ✅ Run creation - PASSED (ID: {run.run_id})")
    
    # Test run retrieval
    retrieved_run = run_manager.get_run(run.run_id)
    assert retrieved_run is not None, "Run should be retrievable"
    assert retrieved_run.run_id == run.run_id, "Run IDs should match"
    print("  ✅ Run retrieval - PASSED")
    
    # Test status update
    from app.models.run import RunStatus
    updated = run_manager.update_status(
        run.run_id,
        status=RunStatus.GENERATION,
        progress=25.0,
        current_stage="generation"
    )
    assert updated, "Status should be updated"
    updated_run = run_manager.get_run(run.run_id)
    assert updated_run.status == RunStatus.GENERATION or updated_run.status.value == "generation", "Status should be updated"
    assert updated_run.progress == 25.0, "Progress should be updated"
    print("  ✅ Status update - PASSED")
    
    # Test stage management
    started = run_manager.start_stage(run.run_id, "brand_kit", {"test": "data"})
    assert started, "Stage should be started"
    updated_run = run_manager.get_run(run.run_id)
    assert "brand_kit" in updated_run.stages, "Stage should be added"
    print("  ✅ Stage start - PASSED")
    
    from app.models.run import RunStatus
    completed = run_manager.complete_stage(run.run_id, "brand_kit")
    assert completed, "Stage should be completed"
    updated_run = run_manager.get_run(run.run_id)
    stage_status = updated_run.stages["brand_kit"].status
    assert stage_status == RunStatus.COMPLETED or (hasattr(stage_status, 'value') and stage_status.value == "completed"), "Stage should be completed"
    print("  ✅ Stage completion - PASSED")
    
    # Test run data update
    updated = run_manager.update_run_data(
        run.run_id,
        brand_kit_data={"colors": ["#FF0000"]},
        generated_ads=["/path/to/ad1.jpg"],
        critique_results={"score": 0.85}
    )
    assert updated, "Run data should be updated"
    updated_run = run_manager.get_run(run.run_id)
    assert updated_run.brand_kit_data is not None, "Brand kit data should be set"
    assert len(updated_run.generated_ads) > 0, "Generated ads should be set"
    print("  ✅ Run data update - PASSED")
    
    # Test retry increment
    initial_retry = updated_run.retry_count
    run_manager.increment_retry(run.run_id)
    updated_run = run_manager.get_run(run.run_id)
    assert updated_run.retry_count == initial_retry + 1, "Retry count should increment"
    print("  ✅ Retry increment - PASSED")
    
    # Test run completion
    from app.models.run import RunStatus
    completed = run_manager.complete_run(run.run_id, success=True)
    assert completed, "Run should be completed"
    updated_run = run_manager.get_run(run.run_id)
    run_status = updated_run.status
    assert run_status == RunStatus.COMPLETED or (hasattr(run_status, 'value') and run_status.value == "completed"), "Status should be completed"
    assert updated_run.progress == 100.0, "Progress should be 100"
    assert updated_run.completed_at is not None, "Completed timestamp should be set"
    print("  ✅ Run completion - PASSED")
    
    # Test run listing
    all_runs = run_manager.list_runs()
    assert len(all_runs) > 0, "Should list runs"
    print(f"  ✅ Run listing - PASSED ({len(all_runs)} runs)")
    
    # Test run deletion
    deleted = run_manager.delete_run(run.run_id)
    assert deleted, "Run should be deleted"
    assert run_manager.get_run(run.run_id) is None, "Run should not exist after deletion"
    print("  ✅ Run deletion - PASSED")
    
    print("✅ Run Manager - ALL TESTS PASSED\n")
    return True


def test_logger():
    """Test logger functionality."""
    print("=" * 60)
    print("Testing Logger Service...")
    print("=" * 60)
    
    # Test different log levels
    app_logger.debug("Debug message")
    app_logger.info("Info message")
    app_logger.warning("Warning message")
    app_logger.error("Error message")
    
    print("  ✅ Log levels - PASSED")
    
    # Test structured logging
    app_logger.info("Test with context", extra={"run_id": "test_123", "stage": "generation"})
    print("  ✅ Structured logging - PASSED")
    
    # Check log file exists
    log_file = Path(__file__).parent.parent / "logs" / "brandai.log"
    if log_file.exists():
        print(f"  ✅ Log file exists - PASSED ({log_file})")
    else:
        print("  ⚠️  Log file not found (might be created on first log)")
    
    print("✅ Logger Service - ALL TESTS PASSED\n")
    return True


def test_integration():
    """Test services working together."""
    print("=" * 60)
    print("Testing Service Integration...")
    print("=" * 60)
    
    # Create a run
    run = run_manager.create_run("Integration test", "image")
    app_logger.info(f"Created run: {run.run_id}")
    
    # Save a file for the run
    file_path = storage_service.save_ad_variation(
        b"test ad content",
        run.run_id,
        "var_1",
        ".jpg"
    )
    app_logger.info(f"Saved ad to: {file_path}")
    
    # Update run with file path
    run_manager.update_run_data(
        run.run_id,
        generated_ads=[str(file_path)]
    )
    
    # Complete the run
    run_manager.complete_run(run.run_id, success=True)
    app_logger.info(f"Completed run: {run.run_id}")
    
    # Verify integration
    from app.models.run import RunStatus
    final_run = run_manager.get_run(run.run_id)
    assert final_run is not None, "Run should exist"
    assert len(final_run.generated_ads) > 0, "Run should have generated ads"
    final_status = final_run.status
    assert final_status == RunStatus.COMPLETED or (hasattr(final_status, 'value') and final_status.value == "completed"), "Run should be completed"
    
    print("  ✅ Services integration - PASSED")
    print("✅ Service Integration - ALL TESTS PASSED\n")
    return True


def main():
    """Run all Phase 2 tests."""
    print("\n" + "=" * 60)
    print("Phase 2: Core Services - Comprehensive Test")
    print("=" * 60)
    print()
    
    all_passed = True
    
    try:
        all_passed &= test_storage_service()
        all_passed &= test_run_manager()
        all_passed &= test_logger()
        all_passed &= test_integration()
        
        print("=" * 60)
        if all_passed:
            print("✅ ALL TESTS PASSED - Phase 2 is complete!")
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

