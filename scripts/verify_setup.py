#!/usr/bin/env python3
"""
Verification script to test the project setup
"""
import sys
import os
import traceback

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_fastapi_import():
    """Test FastAPI application import"""
    try:
        from main import app
        print("✅ FastAPI application imported successfully")
        return True
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        traceback.print_exc()
        return False

def test_reflex_import():
    """Test Reflex dashboard import"""
    try:
        import dashboard.dashboard
        print("✅ Reflex dashboard imported successfully")
        return True
    except Exception as e:
        print(f"❌ Reflex import failed: {e}")
        traceback.print_exc()
        return False

def test_supabase_import():
    """Test Supabase client import"""
    try:
        from app.database.supabase_client import supabase_client
        print("✅ Supabase client imported successfully")
        return True
    except Exception as e:
        print(f"❌ Supabase import failed: {e}")
        traceback.print_exc()
        return False

def test_config_import():
    """Test configuration import"""
    try:
        from app.core.config import settings
        print("✅ Configuration imported successfully")
        print(f"   App name: {settings.app_name}")
        print(f"   Debug mode: {settings.debug}")
        return True
    except Exception as e:
        print(f"❌ Configuration import failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all verification tests"""
    print("🔍 Verifying QR Code Ordering System Setup")
    print("=" * 50)
    
    tests = [
        test_config_import,
        test_supabase_import,
        test_fastapi_import,
        test_reflex_import,
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    if all(results):
        print("🎉 All verification tests passed!")
        print("\nNext steps:")
        print("1. Configure your .env file with Supabase credentials")
        print("2. Start FastAPI: python main.py")
        print("3. Start Reflex dashboard: reflex run")
        return 0
    else:
        print("❌ Some verification tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())