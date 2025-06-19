# !/usr/bin/env python3
"""
Test runner script for Second Certainty Tax Tool.
Run this after applying the fixes to verify everything works correctly.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n🔍 {description}")
    print(f"Running: {command}")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {description}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Error: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ Missing {description}: {filepath}")
        return False

def main():
    """Run all verification checks."""
    print("🧪 Second Certainty Test Suite Runner")
    print("=" * 50)

    #Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    #Check for redundant files that should be removed
    redundant_files = [
        "app/models/user.py",
        "app/models/income.py",
        "app/models/expense.py",
        "app/models/provisional_tax.py",
        "app/core/database.py",
        "scripts/init_db.py"
    ]

    print("\n📁 Checking for redundant files (these should be removed):")
    for file_path in redundant_files:
        if Path(file_path).exists():
            print(f"⚠️  Found redundant file: {file_path} (should be removed)")
        else:
            print(f"✅ Redundant file removed: {file_path}")

    #Check for required files
    print("\n📁 Checking for required files:")
    required_files = [
        ("app/models/tax_models.py", "Main tax models"),
        ("app/core/config.py", "Configuration"),
        ("app/utils/tax_utils.py", "Tax utilities"),
        ("tests/conftest.py", "Test configuration"),
    ]

    all_required_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_required_exist = False

    if not all_required_exist:
        print("❌ Some required files are missing. Please check your setup.")
        return False

    #Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False

    #Run linting
    print("\n🔍 Running code quality checks...")
    run_command("python -m flake8 app --max-line-length=120 --extend-ignore=E203,W503", "Code linting (flake8)")

    #Run specific test files
    test_files = [
        ("tests/test_utils/test_tax_utils.py", "Tax utilities tests"),
        ("tests/test_core/test_tax_calculator.py", "Tax calculator core tests"),
        ("tests/test_core/test_data_scraper.py", "Data scraper tests"),
        ("tests/test_api/test_tax_calculator.py", "Tax calculator API tests"),
    ]

    print("\n🧪 Running individual test files...")
    test_results = []
    for test_file, description in test_files:
        if Path(test_file).exists():
            success = run_command(f"python -m pytest {test_file} -v", description)
            test_results.append((test_file, success))
        else:
            print(f"⚠️  Test file not found: {test_file}")
            test_results.append((test_file, False))

    #Run all tests
    print("\n🧪 Running complete test suite...")
    all_tests_success = run_command("python -m pytest tests/ -v --tb=short", "All tests")

    #Summary
    print("\n📊 Test Results Summary:")
    print("=" * 50)

    for test_file, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_file}")

    overall_status = "✅ PASS" if all_tests_success else "❌ FAIL"
    print(f"{overall_status} Complete test suite")

    if all_tests_success:
        print("\n🎉 All tests passed! Your cleanup was successful.")
        print("\nNext steps:")
        print("- Run the application: uvicorn app.main:app --reload")
        print("- Check the API docs: http://localhost:8000/api/docs")
        print("- Run the seed script: python scripts/seed_data.py")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        print("\nCommon issues:")
        print("- Ensure all redundant files are removed")
        print("- Check that tax_utils.py has been updated")
        print("- Verify test files have been replaced with fixed versions")
        print("- Make sure database is properly configured")

    return all_tests_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
