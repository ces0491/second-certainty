#!/usr/bin/env python3
"""
Dependency Setup Script for Second Certainty

This script ensures all required dependencies are properly installed
before running the test suite or the application.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[OK] {description} completed successfully")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False, e.stderr or ""


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 10):
        print(f"[ERROR] Python 3.10+ required. Current: {sys.version}")
        return False
    print(f"[OK] Python version: {sys.version.split()[0]}")
    return True


def check_virtual_environment():
    """Check if running in virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("[OK] Running in virtual environment")
        return True
    else:
        print("[WARN] Not running in virtual environment")
        print("      Consider creating one: python -m venv venv")
        print("      Then activate it: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Linux/Mac)")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("Second Certainty - Dependency Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check virtual environment
    check_virtual_environment()
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("[ERROR] requirements.txt not found. Please run this script from the project root.")
        sys.exit(1)
    
    print("\n[INFO] Installing dependencies...")
    
    # Upgrade pip first
    success, _ = run_command(
        "python -m pip install --upgrade pip",
        "Upgrading pip"
    )
    
    if not success:
        print("[WARN] Could not upgrade pip, continuing anyway...")
    
    # Install main requirements
    success, output = run_command(
        "pip install -r requirements.txt",
        "Installing main requirements"
    )
    
    if not success:
        print("\n[INFO] Main installation failed, trying critical packages individually...")
        
        # Critical packages for the application to work
        critical_packages = [
            "fastapi>=0.110.0",
            "uvicorn[standard]>=0.29.0", 
            "sqlalchemy>=2.0.40",
            "pydantic[email]>=2.6.0",
            "pydantic-settings>=2.2.1",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-dotenv>=1.0.1",
            "alembic>=1.13.1",
        ]
        
        # Testing and development packages
        dev_packages = [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.0.0",
            "coverage>=7.4.0",
            "black>=24.2.0",
            "flake8>=7.0.0",
            "isort>=5.13.2",
        ]
        
        all_packages = critical_packages + dev_packages
        
        failed_packages = []
        for package in all_packages:
            success, _ = run_command(
                f"pip install {package}",
                f"Installing {package}"
            )
            if not success:
                failed_packages.append(package)
        
        if failed_packages:
            print(f"\n[ERROR] Failed to install: {', '.join(failed_packages)}")
            print("You may need to install these manually or check for compatibility issues.")
        else:
            print("\n[OK] All critical packages installed successfully!")
    
    # Verify key imports work
    print("\n[INFO] Verifying installations...")
    
    test_imports = [
        ("fastapi", "FastAPI framework"),
        ("sqlalchemy", "Database ORM"),
        ("pytest", "Testing framework"),
        ("black", "Code formatter"),
    ]
    
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"[OK] {description} ({module}) - Available")
        except ImportError:
            print(f"[ERROR] {description} ({module}) - Not available")
    
    # Check for coverage specifically
    try:
        import coverage
        print("[OK] Coverage package - Available")
    except ImportError:
        print("[ERROR] Coverage package - Not available")
        print("      Try: pip install coverage pytest-cov")
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Run tests: python test_runner.py")
    print("2. Start application: uvicorn app.main:app --reload")
    print("3. Initialize data: python scripts/seed_data.py")
    print("=" * 60)


if __name__ == "__main__":
    main()