#!/usr/bin/env python3
"""
Test Diagnostics Tool for Second Certainty

This script helps identify which specific tests are failing
and provides actionable fixes.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command_detailed(command, description):
    """Run a command and return detailed results."""
    print(f"\n{'='*60}")
    print(f"[DIAGNOSTIC] {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        print(f"Exit Code: {result.returncode}")
        
        if result.stdout:
            print("\n[STDOUT]")
            print(result.stdout)
        
        if result.stderr:
            print("\n[STDERR]") 
            print(result.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] Command took too long")
        return False, "", "Command timeout"
    except Exception as e:
        print(f"[ERROR] {e}")
        return False, "", str(e)


def test_individual_modules():
    """Test each module individually to identify problems."""
    test_modules = [
        ("tests/test_authentication.py", "Authentication Tests"),
        ("tests/test_tax_calculations.py", "Tax Calculation Tests"), 
        ("tests/test_api_endpoints.py", "API Endpoint Tests"),
        ("tests/test_business_logic.py", "Business Logic Tests"),
        ("tests/test_data_validation.py", "Data Validation Tests"),
        ("tests/test_error_handling.py", "Error Handling Tests"),
        ("tests/test_security.py", "Security Tests"),
        ("tests/test_performance.py", "Performance Tests"),
        ("tests/test_admin_functionality.py", "Admin Functionality Tests"),
    ]
    
    results = {}
    
    for test_file, description in test_modules:
        if not Path(test_file).exists():
            print(f"[SKIP] {test_file} - File not found")
            results[test_file] = "MISSING"
            continue
        
        success, stdout, stderr = run_command_detailed(
            f"python -m pytest {test_file} -v --tb=short",
            f"Testing {description}"
        )
        
        if success:
            results[test_file] = "PASS"
            print(f"[PASS] {description}")
        else:
            results[test_file] = "FAIL"
            print(f"[FAIL] {description}")
    
    return results


def test_basic_imports():
    """Test if basic application imports work."""
    imports_to_test = [
        ("from app.main import app", "Main Application"),
        ("from app.core.config import settings", "Configuration"),
        ("from app.core.auth import authenticate_user", "Authentication"),
        ("from app.core.tax_calculator import TaxCalculator", "Tax Calculator"),
        ("from app.models.tax_models import UserProfile", "Database Models"),
    ]
    
    for import_statement, description in imports_to_test:
        success, stdout, stderr = run_command_detailed(
            f'python -c "{import_statement}; print(\'SUCCESS: {description}\')"',
            f"Testing {description} Import"
        )
        
        if not success:
            print(f"[IMPORT ERROR] {description}")
            return False
    
    print("[IMPORT SUCCESS] All basic imports work")
    return True


def check_database_connection():
    """Test database connection."""
    success, stdout, stderr = run_command_detailed(
        'python -c "from app.core.config import get_db; db = next(get_db()); print(\'Database connection successful\')"',
        "Testing Database Connection"
    )
    return success


def run_simple_test():
    """Run a single simple test to check basic functionality."""
    success, stdout, stderr = run_command_detailed(
        "python -m pytest tests/test_authentication.py::TestAuthentication::test_user_registration_success -v",
        "Running Single Simple Test"
    )
    return success


def main():
    """Main diagnostic function."""
    print("🔍 Second Certainty Test Diagnostics")
    print("="*60)
    
    # Set test environment
    os.environ["TESTING"] = "true"
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test_second_certainty.db")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
    
    # Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("[ERROR] Please run this from the project root directory")
        return
    
    # Step 1: Test basic imports
    print("\n🧪 STEP 1: Testing Basic Imports")
    if not test_basic_imports():
        print("\n❌ RESULT: Import errors detected!")
        print("FIX: Check your Python environment and dependencies")
        return
    
    # Step 2: Test database connection
    print("\n🧪 STEP 2: Testing Database Connection") 
    if not check_database_connection():
        print("\n❌ RESULT: Database connection failed!")
        print("FIX: Check your DATABASE_URL environment variable")
        return
    
    # Step 3: Run a simple test
    print("\n🧪 STEP 3: Testing Simple Functionality")
    if not run_simple_test():
        print("\n❌ RESULT: Basic test failed!")
        print("FIX: There are fundamental issues with test setup")
        return
    
    # Step 4: Test all modules individually
    print("\n🧪 STEP 4: Testing Individual Modules")
    results = test_individual_modules()
    
    # Summary
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r == "PASS")
    failed = sum(1 for r in results.values() if r == "FAIL") 
    missing = sum(1 for r in results.values() if r == "MISSING")
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Missing: {missing}")
    
    if failed > 0:
        print(f"\n🔧 FAILING TESTS:")
        for test_file, result in results.items():
            if result == "FAIL":
                print(f"   • {test_file}")
    
    if missing > 0:
        print(f"\n📁 MISSING TEST FILES:")
        for test_file, result in results.items():
            if result == "MISSING":
                print(f"   • {test_file}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if failed == 0 and missing == 0:
        print("   🎉 All individual tests pass!")
        print("   🔍 The issue might be with running all tests together")
        print("   📝 Try: python -m pytest tests/ -x --tb=short")
        print("   📊 Coverage should work once full test suite passes")
    elif failed <= 2:
        print("   🔧 Fix the failing tests shown above")
        print("   📝 Run them individually with: python -m pytest <test_file> -v")
        print("   🔄 After fixing, coverage analysis should work")
    else:
        print("   ⚠️  Multiple test failures indicate fundamental issues")
        print("   🔍 Check database setup, environment variables, and dependencies")
        print("   📞 Consider reviewing test configuration in conftest.py")
    
    print(f"\n🎯 NEXT STEPS:")
    print("   1. Fix failing tests one by one")
    print("   2. Run: python -m pytest tests/ -x")
    print("   3. Once tests pass, coverage analysis will work")
    print("   4. Coverage is just a metric - working tests are the priority!")


if __name__ == "__main__":
    main()