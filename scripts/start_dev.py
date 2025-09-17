#!/usr/bin/env python3
"""
Development startup script for QR Code Ordering System
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main startup function"""
    print("🏪 QR Code Ordering System - Development Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("⚠️  .env file not found. Creating from template...")
        if Path(".env.example").exists():
            run_command("cp .env.example .env", "Creating .env file")
            print("📝 Please edit .env file with your Supabase credentials")
        else:
            print("❌ .env.example not found")
            sys.exit(1)
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        sys.exit(1)
    
    # Run tests
    if not run_command("python -m pytest tests/ -v", "Running tests"):
        print("⚠️  Tests failed, but continuing...")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your Supabase credentials")
    print("2. Run FastAPI backend: python main.py")
    print("3. Run Reflex dashboard: reflex run")
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Dashboard: http://localhost:3000")

if __name__ == "__main__":
    main()