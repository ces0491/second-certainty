"""
Second Certainty Test Runner
Run this script to execute all tests and verify the system is working correctly.
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def run_command(command, description, timeout=60):
    """Run a command and return success status."""
    print(f"\n🔍 {description}")
    print(f"Running: {command}")
    print("-" * 50)

    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        print(f"✅ Success: {description}")
        if result.stdout.strip():
            print(f"Output:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Exit code: {e.returncode}")
        if e.stderr.strip():
            print(f"Error output:\n{e.stderr}")
        if e.stdout.strip():
            print(f"Standard output:\n{e.stdout}")
        return False
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout: {description} took longer than {timeout} seconds")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ Missing {description}: {filepath}")
        return False

def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 10):
        print(f"❌ Python 3.10+ required. Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def main():
    """Run all verification checks."""
    print("🧪 Second Certainty Test Suite Runner (Updated)")
    print("=" * 60)
    
    start_time = time.time()
    
    # Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("❌ Please run this script from the project root directory")
        print("Current directory:", os.getcwd())
        sys.exit(1)
    
    print(f"📂 Working directory: {os.getcwd()}")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check for required files
    print("\n📁 Checking for required files:")
    required_files = [
        ("app/models/tax_models.py", "Main tax models"),
        ("app/core/config.py", "Configuration"),
        ("app/core/auth.py", "Authentication core"),
        ("app/core/tax_calculator.py", "Tax calculator core"),
        ("app/utils/tax_utils.py", "Tax utilities"),
        ("tests/conftest.py", "Test configuration"),
        ("requirements.txt", "Dependencies file"),
    ]
    
    all_required_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_required_exist = False
    
    if not all_required_exist:
        print("❌ Some required files are missing. Please check your setup.")
        return False
    
    # Check for redundant files that should be removed
    print("\n🗑️  Checking for files that should be removed:")
    redundant_files = [
        "app/models/user.py",
        "app/models/income.py", 
        "app/models/expense.py",
        "app/models/provisional_tax.py",
        "app/core/database.py",
        "app/api/dependencies/auth.py",
        "scripts/init_db.py"
    ]
    
    for file_path in redundant_files:
        if Path(file_path).exists():
            print(f"⚠️  Found redundant file: {file_path} (should be removed)")
        else:
            print(f"✅ Redundant file properly removed: {file_path}")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command("pip install -r requirements.txt", "Installing requirements", timeout=120):
        print("⚠️  Dependency installation failed, but continuing with tests...")
    
    # Run linting (but don't fail on this)
    print("\n🔍 Running code quality checks...")
    run_command(
        "python -m flake8 app --max-line-length=120 --extend-ignore=E203,W503 --exit-zero", 
        "Code linting (flake8) - non-blocking"
    )
    
    # Set up test environment
    print("\n🏗️  Setting up test environment...")
    os.environ["TESTING"] = "true"
    
    # Run individual test modules
    test_modules = [
        ("tests/test_utils/test_tax_utils.py", "Tax utilities tests"),
        ("tests/test_core/test_tax_calculator.py", "Tax calculator core tests"),
        ("tests/test_core/test_data_scraper.py", "Data scraper tests"),
        ("tests/test_api/test_auth.py", "Authentication API tests"),
        ("tests/test_api/test_tax_calculator.py", "Tax calculator API tests"),
        ("tests/test_api/test_admin.py", "Admin API tests"),
    ]
    
    print("\n🧪 Running individual test modules...")
    test_results = []
    
    for test_file, description in test_modules:
        if Path(test_file).exists():
            success = run_command(
                f"python -m pytest {test_file} -v --tb=short", 
                description,
                timeout=90
            )
            test_results.append((test_file, success))
        else:
            print(f"⚠️  Test file not found: {test_file}")
            test_results.append((test_file, False))
    
    # Run full test suite
    print("\n🧪 Running complete test suite...")
    all_tests_success = run_command(
        "python -m pytest tests/ -v --tb=short --durations=10", 
        "Complete test suite",
        timeout=180
    )
    
    # Run with coverage if pytest-cov is available
    print("\n📊 Running tests with coverage...")
    coverage_success = run_command(
        "python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html", 
        "Test coverage analysis",
        timeout=180
    )
    
    # Quick smoke test of the application
    print("\n🚀 Testing application startup...")
    startup_success = run_command(
        "python -c \"from app.main import app; print('✅ App imports successfully')\"",
        "Application import test",
        timeout=30
    )
    
    # Database initialization test
    print("\n💾 Testing database initialization...")
    db_test_success = run_command(
        "python -c \"from app.core.config import get_db; next(get_db()); print('✅ Database connection works')\"",
        "Database connection test",
        timeout=30
    )
    
    # Calculate runtime
    end_time = time.time()
    runtime = end_time - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"⏱️  Total runtime: {runtime:.1f} seconds")
    print(f"🏗️  Setup checks: {'✅ PASS' if all_required_exist else '❌ FAIL'}")
    print(f"🚀 Application startup: {'✅ PASS' if startup_success else '❌ FAIL'}")
    print(f"💾 Database connection: {'✅ PASS' if db_test_success else '❌ FAIL'}")
    
    print("\n📋 Individual test modules:")
    passed_modules = 0
    for test_file, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {Path(test_file).name}")
        if success:
            passed_modules += 1
    
    print(f"\n🧪 Complete test suite: {'✅ PASS' if all_tests_success else '❌ FAIL'}")
    if coverage_success:
        print(f"📊 Coverage analysis: ✅ COMPLETED (see htmlcov/index.html)")
    
    # Overall status
    overall_success = (
        all_required_exist and 
        startup_success and 
        db_test_success and 
        all_tests_success and
        passed_modules >= len(test_modules) * 0.8  # 80% of modules must pass
    )
    
    print(f"\n🎯 OVERALL STATUS: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
    
    if overall_success:
        print("\n🎉 Congratulations! All tests passed successfully.")
        print("\n📋 Next steps:")
        print("   • Run the application: uvicorn app.main:app --reload")
        print("   • Check API docs: http://localhost:8000/api/docs")
        print("   • Initialize data: python scripts/seed_data.py")
        print("   • View coverage: open htmlcov/index.html")
    else:
        print("\n⚠️  Some tests failed or require attention.")
        print("\n🔧 Common solutions:")
        print("   • Ensure all dependencies are installed: pip install -r requirements.txt")
        print("   • Check that redundant files are removed")
        print("   • Verify environment variables in .env file")
        print("   • Ensure database is properly configured")
        print("   • Check specific test failures above for details")
    
    print("\n💡 For detailed output, check individual test runs above.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)