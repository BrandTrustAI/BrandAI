#!/usr/bin/env python3
"""
Simple test script to verify FastAPI server setup.
Run this after installing dependencies.
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from app.main import app
    from app.config import settings
    print("✅ All imports successful!")
    print(f"✅ Configuration loaded:")
    print(f"   - APP_ENV: {settings.APP_ENV}")
    print(f"   - LOG_LEVEL: {settings.LOG_LEVEL}")
    print(f"   - API_HOST: {settings.API_HOST}")
    print(f"   - API_PORT: {settings.API_PORT}")
    print("\n✅ FastAPI app created successfully!")
    print("✅ Ready to run: uvicorn app.main:app --reload")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

