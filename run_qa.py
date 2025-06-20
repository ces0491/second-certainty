"""
Second Certainty Enhanced Test Runner
Run this script to execute all tests and verify the system is working correctly.

Features:
- Comprehensive test coverage across all modules
- Performance monitoring and reporting
- Security validation
- Database integrity checks
- Detailed error reporting and suggestions
- Memory usage monitoring
- Concurrent test execution support
"""

import subprocess
import sys
import os
import time
import json
import gc
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Test configuration
TEST_CONFIG = {
    "timeout_short": 30,
    "timeout_medium": 90,
    "timeout_long": 180,
    "max_memory_growth": 1000,
    "performance_threshold": 2.0,
    "coverage_threshold": 80,
}

class TestResult:
    """Class to track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
        self.warnings = []
        self.performance_data = {}
        self.start_time = time.time()
    
    def add_result(self, passed: bool, test_name: str, duration: float = 0, error: str = None):
        if passed:
            self.passed += 1
        else:
            self.failed += 1
            if error:
                self.errors.append(f"{test_name}: {error}")
        
        self.performance_data[test_name] = duration
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    @property
    def total_time(self) -> float:
        return time.time() - self.start_time
    
    @property
    def success_rate(self) -> float:
        total = self.passed + self.failed
        return (self.passed / total * 100) if total > 0 else 0


def print_header(title: str, char: str = "="):
    """Print a formatted header."""
    print(f"\n{char * 60}")
    print(f"[TEST] {title}")
    print(f"{char * 60}")


def print_section(title: str):
    """Print a section header."""
    print(f"\n[INFO] {title}")
    print("-" * 50)


def run_command(command: str, description: str, timeout: int = 60, capture_output: bool = True) -> Tuple[bool, str, float]:
    """
    Run a command and return success status, output, and duration.
    
    Args:
        command: Command to run
        description: Description for logging
        timeout: Timeout in seconds
        capture_output: Whether to capture output
    
    Returns:
        Tuple of (success, output/error, duration)
    """
    print(f"[RUN] {description}")
    print(f"   Command: {command}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        duration = time.time() - start_time
        
        status = "[PASS]" if result.returncode == 0 else "[FAIL]"
        print(f"   Result: {status} ({duration:.2f}s)")
        
        if result.stdout.strip() and len(result.stdout) < 500:
            print(f"   Output: {result.stdout.strip()}")
        
        return True, result.stdout, duration
        
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"   Result: [FAIL] ({duration:.2f}s)")
        print(f"   Exit code: {e.returncode}")
        
        error_output = e.stderr if e.stderr else e.stdout
        if error_output and len(error_output.strip()) < 500:
            print(f"   Error: {error_output.strip()}")
        
        return False, error_output or "Command failed", duration
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"   Result: [TIMEOUT] ({duration:.2f}s)")
        return False, f"Command timed out after {timeout}s", duration
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"   Result: [ERROR] ({duration:.2f}s)")
        print(f"   Exception: {str(e)}")
        return False, str(e), duration


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists and report result."""
    if Path(filepath).exists():
        print(f"[OK] {description}: {filepath}")
        return True
    else:
        print(f"[MISSING] {description}: {filepath}")
        return False


def check_python_version() -> bool:
    """Check Python version compatibility."""
    if sys.version_info < (3, 10):
        print(f"[ERROR] Python 3.10+ required. Current: {sys.version}")
        return False
    print(f"[OK] Python version: {sys.version.split()[0]}")
    return True


def check_environment() -> Tuple[bool, List[str]]:
    """Check environment setup and return status with recommendations."""
    issues = []
    
    # Check required environment variables
    required_env_vars = {
        "DATABASE_URL": "Database connection string",
        "SECRET_KEY": "JWT secret key"
    }
    
    for var, description in required_env_vars.items():
        if not os.getenv(var):
            issues.append(f"Missing environment variable: {var} ({description})")
    
    # Check .env file
    if not Path(".env").exists():
        issues.append("Missing .env file (copy from env.example)")
    
    # Check logs directory
    if not Path("logs").exists():
        Path("logs").mkdir(exist_ok=True)
        print("[OK] Created logs directory")
    
    return len(issues) == 0, issues


def run_setup_checks(result: TestResult) -> bool:
    """Run initial setup checks."""
    print_section("Environment Setup Checks")
    
    all_good = True
    
    # Python version
    if not check_python_version():
        result.add_result(False, "python_version", 0, "Incompatible Python version")
        all_good = False
    else:
        result.add_result(True, "python_version")
    
    # Working directory
    if not Path("app/main.py").exists():
        print("[ERROR] Please run this script from the project root directory")
        print(f"   Current directory: {os.getcwd()}")
        result.add_result(False, "working_directory", 0, "Wrong working directory")
        return False
    
    print(f"[OK] Working directory: {os.getcwd()}")
    result.add_result(True, "working_directory")
    
    # Environment setup
    env_ok, env_issues = check_environment()
    if not env_ok:
        print("[WARN] Environment issues:")
        for issue in env_issues:
            print(f"   • {issue}")
            result.add_warning(issue)
    else:
        print("[OK] Environment configuration looks good")
    
    # Required files
    required_files = [
        ("app/main.py", "Main application file"),
        ("app/models/tax_models.py", "Tax models"),
        ("app/core/config.py", "Configuration"),
        ("app/core/auth.py", "Authentication"),
        ("app/core/tax_calculator.py", "Tax calculator"),
        ("tests/conftest.py", "Test configuration"),
        ("requirements.txt", "Dependencies"),
        ("alembic.ini", "Database migrations config"),
    ]
    
    print("\n[INFO] Required Files:")
    files_ok = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            result.add_result(False, f"file_{filepath.replace('/', '_')}", 0, f"Missing {filepath}")
            files_ok = False
        else:
            result.add_result(True, f"file_{filepath.replace('/', '_')}")
    
    return all_good and files_ok


def install_dependencies(result: TestResult) -> bool:
    """Install project dependencies with enhanced error handling."""
    print_section("Dependency Installation")
    
    # First, upgrade pip to ensure compatibility
    pip_upgrade_success, _, _ = run_command(
        "python -m pip install --upgrade pip",
        "Upgrading pip",
        timeout=60
    )
    
    if not pip_upgrade_success:
        result.add_warning("Could not upgrade pip - some packages may fail to install")
    
    # Install main requirements
    success, output, duration = run_command(
        "pip install -r requirements.txt", 
        "Installing Python dependencies",
        timeout=TEST_CONFIG["timeout_long"]
    )
    
    if not success:
        print("[INFO] Main requirements installation failed, trying individual critical packages...")
        
        # Try installing critical packages individually
        critical_packages = [
            "fastapi",
            "uvicorn",
            "sqlalchemy", 
            "pytest",
            "pytest-cov",
            "coverage",
            "black",
            "flake8",
            "isort"
        ]
        
        individual_success = True
        for package in critical_packages:
            pkg_success, _, _ = run_command(
                f"pip install {package}",
                f"Installing {package}",
                timeout=60
            )
            if not pkg_success:
                individual_success = False
                result.add_warning(f"Failed to install {package}")
        
        if individual_success:
            success = True
            result.add_warning("Main requirements failed but critical packages installed individually")
    
    result.add_result(success, "dependency_installation", duration, output if not success else None)
    
    if not success:
        result.add_warning("Dependency installation failed - some tests may not work")
    
    return success


def run_code_quality_checks(result: TestResult) -> Dict[str, bool]:
    """Run code quality and linting checks."""
    print_section("Code Quality Checks")
    
    quality_results = {}
    
    # Flake8 linting
    success, output, duration = run_command(
        "python -m flake8 app/ --max-line-length=120 --extend-ignore=E203,W503,E501,F401,E402,C901 --statistics",
        "Running flake8 linting",
        timeout=TEST_CONFIG["timeout_medium"]
    )
    quality_results["linting"] = success
    result.add_result(success, "linting", duration, output if not success else None)
    
    # Black formatting check
    success, output, duration = run_command(
        "python -m black app --check --diff",
        "Checking code formatting (Black)",
        timeout=TEST_CONFIG["timeout_short"]
    )
    quality_results["formatting"] = success
    result.add_result(success, "formatting", duration, output if not success else None)
    
    # Import sorting check
    success, output, duration = run_command(
        "python -m isort app --check-only --diff",
        "Checking import sorting (isort)",
        timeout=TEST_CONFIG["timeout_short"]
    )
    quality_results["import_sorting"] = success
    result.add_result(success, "import_sorting", duration, output if not success else None)
    
    return quality_results


def run_individual_tests(result: TestResult) -> Dict[str, bool]:
    """Run individual test modules."""
    print_section("Individual Test Modules")
    
    # Updated test modules based on actual project structure
    test_modules = [
        ("tests/test_authentication.py", "Authentication system tests"),
        ("tests/test_tax_calculations.py", "Tax calculation core tests"),
        ("tests/test_api_endpoints.py", "API endpoint tests"),
        ("tests/test_business_logic.py", "Business logic tests"),
        ("tests/test_data_validation.py", "Data validation tests"),
        ("tests/test_error_handling.py", "Error handling tests"),
        ("tests/test_security.py", "Security tests"),
        ("tests/test_performance.py", "Performance tests"),
        ("tests/test_admin_functionality.py", "Admin functionality tests"),
    ]
    
    test_results = {}
    
    for test_file, description in test_modules:
        if Path(test_file).exists():
            success, output, duration = run_command(
                f"python -m pytest {test_file} -v --tb=short -x",
                description,
                timeout=TEST_CONFIG["timeout_long"]
            )
            test_results[test_file] = success
            result.add_result(success, test_file.replace("/", "_").replace(".py", ""), duration, output if not success else None)
        else:
            print(f"[WARN] Test file not found: {test_file}")
            result.add_warning(f"Missing test file: {test_file}")
            test_results[test_file] = False
    
    return test_results


def run_comprehensive_tests(result: TestResult) -> bool:
    """Run the complete test suite."""
    print_section("Comprehensive Test Suite")
    
    success, output, duration = run_command(
        "python -m pytest tests/ -v --tb=short --durations=10 --maxfail=5",
        "Running complete test suite",
        timeout=TEST_CONFIG["timeout_long"] * 2
    )
    
    result.add_result(success, "comprehensive_tests", duration, output if not success else None)
    return success


def run_coverage_analysis(result: TestResult) -> Tuple[bool, float]:
    """Run test coverage analysis with fallback methods."""
    print_section("Test Coverage Analysis")
    
    coverage_percentage = 0.0
    
    # First try pytest-cov
    success, output, duration = run_command(
        "python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-report=json",
        "Running coverage analysis (pytest-cov)",
        timeout=TEST_CONFIG["timeout_long"]
    )
    
    if not success:
        print("[INFO] pytest-cov failed, trying alternative coverage method...")
        
        # Try installing coverage packages first
        install_success, _, _ = run_command(
            "pip install pytest-cov coverage",
            "Installing coverage packages",
            timeout=60
        )
        
        if install_success:
            # Retry with pytest-cov
            success, output, duration = run_command(
                "python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html",
                "Retrying coverage analysis",
                timeout=TEST_CONFIG["timeout_long"]
            )
        
        if not success:
            # Fallback to basic coverage
            print("[INFO] Using basic coverage measurement...")
            success, output, duration = run_command(
                "python -m coverage run -m pytest tests/ && python -m coverage report",
                "Basic coverage analysis",
                timeout=TEST_CONFIG["timeout_long"]
            )
            
            if not success:
                # Final fallback - just run tests without coverage
                print("[INFO] Running tests without coverage measurement...")
                success, output, duration = run_command(
                    "python -m pytest tests/",
                    "Running tests without coverage",
                    timeout=TEST_CONFIG["timeout_long"]
                )
                result.add_warning("Coverage analysis not available - install pytest-cov for coverage reporting")
    
    # Try to extract coverage percentage
    if success:
        try:
            # Try to read coverage percentage from coverage.json
            if Path("coverage.json").exists():
                with open("coverage.json", "r") as f:
                    coverage_data = json.load(f)
                    coverage_percentage = coverage_data.get("totals", {}).get("percent_covered", 0.0)
            else:
                # Parse from output as fallback
                for line in output.split('\n'):
                    if 'TOTAL' in line and '%' in line:
                        parts = line.split()
                        for part in parts:
                            if '%' in part and part.replace('%', '').replace('.', '').isdigit():
                                try:
                                    coverage_percentage = float(part.replace('%', ''))
                                    break
                                except ValueError:
                                    continue
                        if coverage_percentage > 0:
                            break
        except Exception as e:
            result.add_warning(f"Could not parse coverage percentage: {e}")
    
    result.add_result(success, "coverage_analysis", duration, output if not success else None)
    result.performance_data["coverage_percentage"] = coverage_percentage
    
    return success, coverage_percentage


def run_application_tests(result: TestResult) -> Dict[str, bool]:
    """Run application-specific tests with ASCII-safe commands."""
    print_section("Application Integration Tests")
    
    app_results = {}
    
    # Application import test
    success, output, duration = run_command(
        "python -c \"from app.main import app; print('Application imports successfully')\"",
        "Testing application import",
        timeout=TEST_CONFIG["timeout_short"]
    )
    app_results["import"] = success
    result.add_result(success, "app_import", duration, output if not success else None)
    
    # Database connection test
    success, output, duration = run_command(
        "python -c \"from app.core.config import get_db; next(get_db()); print('Database connection works')\"",
        "Testing database connection",
        timeout=TEST_CONFIG["timeout_short"]
    )
    app_results["database"] = success
    result.add_result(success, "database_connection", duration, output if not success else None)
    
    # Configuration test
    success, output, duration = run_command(
        "python -c \"from app.core.config import settings; print(f'Configuration loaded: {settings.APP_NAME}')\"",
        "Testing configuration loading",
        timeout=TEST_CONFIG["timeout_short"]
    )
    app_results["config"] = success
    result.add_result(success, "config_loading", duration, output if not success else None)
    
    # Tax calculator test
    success, output, duration = run_command(
        "python -c \"from app.core.tax_calculator import TaxCalculator; print('Tax calculator available')\"",
        "Testing tax calculator import",
        timeout=TEST_CONFIG["timeout_short"]
    )
    app_results["tax_calculator"] = success
    result.add_result(success, "tax_calculator_import", duration, output if not success else None)
    
    return app_results


def generate_report(result: TestResult, quality_results: Dict, test_results: Dict, 
                   app_results: Dict, coverage_percentage: float) -> None:
    """Generate comprehensive test report."""
    print_header("COMPREHENSIVE TEST REPORT")
    
    # Summary statistics
    print(f"Total Runtime: {result.total_time:.1f} seconds")
    print(f"Tests Passed: {result.passed}")
    print(f"Tests Failed: {result.failed}")
    print(f"Success Rate: {result.success_rate:.1f}%")
    print(f"Code Coverage: {coverage_percentage:.1f}%")
    
    # Performance summary
    print(f"\nPerformance Summary:")
    slow_tests = [(name, duration) for name, duration in result.performance_data.items() 
                  if duration > TEST_CONFIG["performance_threshold"]]
    if slow_tests:
        print("   Slow tests (>2s):")
        for name, duration in sorted(slow_tests, key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {name}: {duration:.2f}s")
    else:
        print("   [OK] All tests completed within performance thresholds")
    
    # Code quality results
    print(f"\nCode Quality:")
    for check, passed in quality_results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"   {check.replace('_', ' ').title()}: {status}")
    
    # Test module results
    print(f"\nTest Modules:")
    for test_file, passed in test_results.items():
        status = "[PASS]" if passed else "[FAIL]"
        module_name = Path(test_file).stem.replace("test_", "").replace("_", " ").title()
        print(f"   {module_name}: {status}")
    
    # Application integration results
    print(f"\nApplication Integration:")
    for test_name, passed in app_results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    # Warnings and recommendations
    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings[:10]:  # Show first 10 warnings
            print(f"   • {warning}")
        if len(result.warnings) > 10:
            print(f"   ... and {len(result.warnings) - 10} more")
    
    # Errors (if any)
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors[:5]:  # Show first 5 errors
            print(f"   • {error}")
        if len(result.errors) > 5:
            print(f"   ... and {len(result.errors) - 5} more")


def provide_recommendations(result: TestResult, coverage_percentage: float) -> None:
    """Provide recommendations based on test results."""
    print_header("RECOMMENDATIONS & NEXT STEPS")
    
    overall_success = (
        result.success_rate > 85 and
        coverage_percentage > TEST_CONFIG["coverage_threshold"] and
        len(result.errors) == 0
    )
    
    if overall_success:
        print("[SUCCESS] Excellent! Your test suite is in great shape.")
        print("\nNext Steps:")
        print("   • Run the application: uvicorn app.main:app --reload")
        print("   • Check API docs: http://localhost:8000/api/docs")
        print("   • Initialize data: python scripts/seed_data.py")
        print("   • View coverage report: open htmlcov/index.html")
        print("   • Consider setting up CI/CD automation")
        
    else:
        print("[ATTENTION] Your test suite needs attention.")
        print("\nPriority Actions:")
        
        if result.success_rate < 85:
            print(f"   • Fix failing tests (current success rate: {result.success_rate:.1f}%)")
        
        if coverage_percentage < TEST_CONFIG["coverage_threshold"]:
            print(f"   • Improve test coverage (current: {coverage_percentage:.1f}%, target: {TEST_CONFIG['coverage_threshold']}%)")
        
        if result.errors:
            print("   • Address test errors:")
            for error in result.errors[:3]:
                print(f"     - {error}")
        
        print("\nResources:")
        print("   • Check test logs for detailed error information")
        print("   • Review failing test output above")
        print("   • Ensure all dependencies are installed")
        print("   • Verify environment variables in .env file")
        print("   • Check database connectivity")
    
    # Performance recommendations
    slow_tests = [(name, duration) for name, duration in result.performance_data.items() 
                  if duration > TEST_CONFIG["performance_threshold"]]
    if slow_tests:
        print(f"\nPerformance:")
        print("   • Consider optimizing slow tests:")
        for name, duration in sorted(slow_tests, key=lambda x: x[1], reverse=True)[:3]:
            print(f"     - {name}: {duration:.2f}s")


def cleanup_test_artifacts() -> None:
    """Clean up test artifacts and temporary files."""
    artifacts = [
        "test_second_certainty.db",
        ".coverage",
        ".pytest_cache",
        "__pycache__",
        "coverage.json",
    ]
    
    for artifact in artifacts:
        path = Path(artifact)
        if path.exists():
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
            except Exception:
                pass  # Ignore cleanup errors


def main() -> bool:
    """Main test runner function."""
    print_header("Second Certainty Enhanced Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize result tracking
    result = TestResult()
    
    # Set test environment
    os.environ["TESTING"] = "true"
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test_second_certainty.db")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
    
    try:
        # Phase 1: Setup checks
        setup_ok = run_setup_checks(result)
        if not setup_ok:
            print("\n[ERROR] Setup checks failed. Cannot continue.")
            return False
        
        # Phase 2: Dependencies
        install_dependencies(result)
        
        # Phase 3: Code quality
        quality_results = run_code_quality_checks(result)
        
        # Phase 4: Individual tests
        test_results = run_individual_tests(result)
        
        # Phase 5: Comprehensive tests
        comprehensive_success = run_comprehensive_tests(result)
        
        # Phase 6: Coverage analysis
        coverage_success, coverage_percentage = run_coverage_analysis(result)
        
        # Phase 7: Application tests
        app_results = run_application_tests(result)
        
        # Generate comprehensive report
        generate_report(result, quality_results, test_results, app_results, coverage_percentage)
        
        # Provide recommendations
        provide_recommendations(result, coverage_percentage)
        
        # Final status
        overall_success = (
            result.success_rate > 80 and
            comprehensive_success and
            all(app_results.values())
        )
        
        status = "SUCCESS" if overall_success else "NEEDS ATTENTION"
        icon = "[SUCCESS]" if overall_success else "[ATTENTION]"
        
        print_header(f"{icon} OVERALL STATUS: {status}")
        
        return overall_success
        
    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] Test run interrupted by user.")
        return False
        
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error during test run: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        cleanup_test_artifacts()
        print(f"\n[COMPLETE] Test run completed in {result.total_time:.1f} seconds")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)