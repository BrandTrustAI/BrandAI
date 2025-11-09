"""
Test Phase 7 Orchestrator with Video Generation
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

os.environ.setdefault("APP_ENV", "development")

from app.core.orchestrator import orchestrator
from app.core.run_manager import run_manager

print("=" * 70)
print("Phase 7: Video Generation Test")
print("=" * 70)
print()

# Create run
print("📋 Creating run...")
run = run_manager.create_run(
    prompt="Nike shoe advertisement video",
    media_type="video",
    brand_website_url=None
)
run_id = run.run_id
print(f"✅ Run created: {run_id}")
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
        print(f"🖼️  Logo found: {Path(logo_path).name}")
    if product_files:
        for pf in product_files:
            if str(pf) != logo_path:
                product_path = str(pf)
                print(f"📦 Product found: {Path(product_path).name}")
                break

print()
print("🚀 Starting VIDEO workflow execution...")
print("   Workflow: Brand Kit → Generation (VIDEO) → Critique → Refinement")
print("   This will take several minutes (video generation is slower)...")
print()
print("-" * 70)
print()

try:
    result = orchestrator.execute(
        run_id=run_id,
        user_prompt="Nike shoe advertisement video showcasing athletic performance and style",
        media_type="video",
        brand_website_url=None,
        logo_path=logo_path,
        product_path=product_path,
        max_retries=3
    )
    
    print()
    print("-" * 70)
    print("✅ Workflow execution completed!")
    print()
    print("📊 Results:")
    print(f"   Status: {result.get('status', 'N/A')}")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Retry Count: {result.get('retry_count', 0)}")
    
    if result.get('generated_ad_path'):
        print(f"   Generated Video: {result.get('generated_ad_path')}")
    
    if result.get('overall_score') is not None:
        print(f"   Overall Score: {result.get('overall_score', 0):.2f}")
    
    if result.get('error'):
        print(f"   Error: {result.get('error')}")
    
    print()
    print("=" * 70)

except Exception as e:
    print()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("=" * 70)

