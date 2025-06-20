#!/usr/bin/env python3
"""
Quick Test Setup Script for Second Certainty

This script prepares your environment for running tests.
Run this before running the main test suite.

Usage:
    python quick_test_setup.py
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create a .env file for testing if it doesn't exist."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file for testing...")
    
    env_content = """# Test Environment Configuration for Second Certainty
# This file is created automatically for testing

# Database Configuration
DATABASE_URL=sqlite:///./test_second_certainty.db

# Security Configuration  
SECRET_KEY=test-secret-key-for-testing-only-change-for-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application Configuration
APP_NAME=Second Certainty Test
APP_VERSION=1.0.0-test
API_PREFIX=/api
DEBUG=true
ENVIRONMENT=testing

# SARS Configuration
SARS_WEBSITE_URL=https://www.sars.gov.za

# CORS Configuration
CORS_ORIGINS=http://localhost:3000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Rate Limiting (disabled for testing)
ENABLE_RATE_LIMITING=false
DEFAULT_RATE_LIMIT=1000
AUTH_RATE_LIMIT=100

# File Upload Configuration
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads
ALLOWED_FILE_TYPES=.pdf,.jpg,.jpeg,.png

# Scraping Configuration
SCRAPING_TIMEOUT=30
SCRAPING_RETRIES=3
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def create_directories():
    """Create necessary directories for testing."""
    directories = [
        "logs",
        "uploads", 
        "test_uploads",
        "htmlcov"
    ]
    
    print("📁 Creating necessary directories...")
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Created {directory}/")
            except Exception as e:
                print(f"   ❌ Failed to create {directory}/: {e}")
                return False
        else:
            print(f"   ✅ {directory}/ already exists")
    
    return True


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 10):
        print(f"❌ Python 3.10+ required. Current: {sys.version}")
        print("   Please upgrade Python or use a virtual environment with Python 3.10+")
        return False
    
    print(f"✅ Python version OK: {sys.version.split()[0]}")
    return True


def check_virtual_environment():
    """Check if running in a virtual environment."""
    print("🏠 Checking virtual environment...")
    
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if in_venv:
        print(f"✅ Running in virtual environment: {sys.prefix}")
        return True
    else:
        print("⚠️  Not running in virtual environment")
        print("   It's recommended to use a virtual environment for testing")
        print("   Create one with: python -m venv venv")
        print("   Activate with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)")
        return True  # Don't fail, just warn


def install_basic_dependencies():
    """Install basic testing dependencies."""
    print("📦 Installing basic test dependencies...")
    
    basic_deps = [
        "pytest>=7.4.4",
        "pytest-cov>=4.0.0",
        "coverage>=7.4.0",
    ]
    
    import subprocess
    
    for dep in basic_deps:
        try:
            print(f"   Installing {dep}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"   ✅ {dep} installed")
            else:
                print(f"   ❌ Failed to install {dep}")
                print(f"   Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ❌ Timeout installing {dep}")
            return False
        except Exception as e:
            print(f"   ❌ Error installing {dep}: {e}")
            return False
    
    return True


def verify_project_structure():
    """Verify that we're in the right directory with correct project structure."""
    print("📋 Verifying project structure...")
    
    required_files = [
        "app/main.py",
        "app/core/config.py", 
        "tests/conftest.py",
        "requirements.txt"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path}")
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   • {file_path}")
        print("\nMake sure you're running this script from the project root directory.")
        return False
    
    print("✅ Project structure looks good")
    return True


def main():
    """Main setup function."""
    print("🚀 Second Certainty - Quick Test Setup")
    print("=" * 50)
    
    # Check if we're in the right place
    if not verify_project_structure():
        print("\n❌ Setup failed: Invalid project structure")
        print("Please run this script from the Second Certainty project root directory.")
        return False
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Incompatible Python version")
        return False
    
    # Check virtual environment (warning only)
    check_virtual_environment()
    
    # Create necessary directories
    if not create_directories():
        print("\n❌ Setup failed: Could not create directories")
        return False
    
    # Create .env file
    if not create_env_file():
        print("\n❌ Setup failed: Could not create .env file")
        return False
    
    # Install basic dependencies
    if not install_basic_dependencies():
        print("\n❌ Setup failed: Could not install basic dependencies")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Install all dependencies: pip install -r requirements.txt")
    print("2. Run the test suite: python run_qa.py")
    print("3. Or run specific tests: pytest tests/")
    print("\nHappy testing! 🧪")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)