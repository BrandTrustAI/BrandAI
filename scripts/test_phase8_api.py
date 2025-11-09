"""
Test script for Phase 8: API Endpoints
Tests all API endpoints.
"""
import sys
import os
import requests
import time
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

os.environ.setdefault("APP_ENV", "development")

print("=" * 70)
print("Phase 8: API Endpoints - Test")
print("=" * 70)
print()

# Test server URL
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

print(f"🌐 Testing API at: {BASE_URL}")
print(f"📚 API Docs: {BASE_URL}/docs")
print()

# Test 1: Health Check
print("-" * 70)
print("TEST 1: Health Check")
print("-" * 70)
print()

try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        print("✅ Health check passed")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        print(f"   Response: {response.text}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server. Is the server running?")
    print("   Start server with: python -m app.main")
    print()
    print("   Or use: ./scripts/run_backend.sh")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: Detailed Health Check
print("-" * 70)
print("TEST 2: Detailed Health Check")
print("-" * 70)
print()

try:
    response = requests.get(f"{BASE_URL}/health/detailed", timeout=5)
    if response.status_code == 200:
        print("✅ Detailed health check passed")
        data = response.json()
        print(f"   Status: {data.get('status')}")
        print(f"   Environment: {data.get('environment')}")
        print(f"   Config: {data.get('config')}")
    else:
        print(f"❌ Detailed health check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 3: Root Endpoint
print("-" * 70)
print("TEST 3: Root Endpoint")
print("-" * 70)
print()

try:
    response = requests.get(f"{API_BASE}/", timeout=5)
    if response.status_code == 200:
        print("✅ Root endpoint works")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ Root endpoint failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 4: POST /generate (with file uploads)
print("-" * 70)
print("TEST 4: POST /generate Endpoint")
print("-" * 70)
print()

# Check for test files
test_dir = Path("/Users/udaygattu/Documents/Hackathon/BrandAI-fork/data/storage/uploads")
logo_file = None
product_file = None

if test_dir.exists():
    logo_files = list(test_dir.glob("*logo*")) + list(test_dir.glob("*Logo*"))
    product_files = list(test_dir.glob("*product*")) + list(test_dir.glob("*Product*")) + list(test_dir.glob("*.png")) + list(test_dir.glob("*.jpg"))
    
    if logo_files:
        logo_file = logo_files[0]
        print(f"📁 Logo file: {logo_file.name}")
    if product_files:
        for pf in product_files:
            if pf != logo_file:
                product_file = pf
                print(f"📁 Product file: {product_file.name}")
                break

print()

try:
    # Prepare form data
    files = {}
    if logo_file:
        files["logo"] = (logo_file.name, open(logo_file, "rb"), "image/jpeg")
    if product_file:
        files["product"] = (product_file.name, open(product_file, "rb"), "image/png")
    
    data = {
        "prompt": "Nike shoe advertisement showcasing athletic performance and style",
        "media_type": "image",
        "brand_website_url": None
    }
    
    print("🚀 Sending POST /generate request...")
    print(f"   Prompt: {data['prompt']}")
    print(f"   Media Type: {data['media_type']}")
    print()
    
    response = requests.post(
        f"{API_BASE}/generate",
        data=data,
        files=files,
        timeout=60  # Increased timeout for file uploads
    )
    
    # Close file handles
    for file_tuple in files.values():
        if hasattr(file_tuple[1], 'close'):
            file_tuple[1].close()
    
    if response.status_code == 200:
        result = response.json()
        run_id = result.get("run_id")
        print("✅ Generation request accepted!")
        print(f"   Run ID: {run_id}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        print(f"   Estimated Time: {result.get('estimated_time')} seconds")
        print()
        
        # Test 5: GET /status/{run_id}
        print("-" * 70)
        print("TEST 5: GET /status/{run_id} Endpoint")
        print("-" * 70)
        print()
        
        print(f"📊 Checking status for run: {run_id}")
        print("   (This will take several minutes for the workflow to complete)")
        print()
        
        # Poll status a few times
        for i in range(5):
            time.sleep(5)  # Wait 5 seconds between checks
            
            try:
                status_response = requests.get(f"{API_BASE}/status/{run_id}", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Check {i+1}: Status = {status_data.get('status')}, Progress = {status_data.get('progress')}%")
                    
                    if status_data.get('status') == 'completed':
                        print()
                        print("✅ Workflow completed!")
                        
                        # Test 6: GET /result/{run_id}
                        print("-" * 70)
                        print("TEST 6: GET /result/{run_id} Endpoint")
                        print("-" * 70)
                        print()
                        
                        try:
                            result_response = requests.get(f"{API_BASE}/result/{run_id}", timeout=5)
                            if result_response.status_code == 200:
                                result_data = result_response.json()
                                print("✅ Result retrieved successfully!")
                                print(f"   Status: {result_data.get('status')}")
                                print(f"   Success: {result_data.get('success')}")
                                if result_data.get('critique_report'):
                                    print(f"   Critique Report: Available")
                                    report = result_data['critique_report']
                                    print(f"   Overall Score: {report.get('all_variations', [{}])[0].get('overall_score', 'N/A')}")
                            else:
                                print(f"❌ Result endpoint failed: {result_response.status_code}")
                        except Exception as e:
                            print(f"❌ Error getting result: {e}")
                        
                        break
                    elif status_data.get('status') == 'failed':
                        print()
                        print(f"❌ Workflow failed: {status_data.get('message')}")
                        break
                else:
                    print(f"   Check {i+1}: Status endpoint returned {status_response.status_code}")
            except Exception as e:
                print(f"   Check {i+1}: Error - {e}")
        
        print()
        print("💡 Note: Workflow may still be running. Check status later with:")
        print(f"   GET {API_BASE}/status/{run_id}")
        
    else:
        print(f"❌ Generation request failed: {response.status_code}")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("Phase 8 API Endpoints Test Complete!")
print("=" * 70)
print()
print("📚 API Documentation available at: http://localhost:8000/docs")

