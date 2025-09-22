#!/usr/bin/env python3
"""
Integration Test Runner for Mini Agent

This script runs integration tests with real LLM API calls.
It handles environment setup and provides different test execution modes.

Usage:
    python run_integration_tests.py --help
    python run_integration_tests.py --check-env
    python run_integration_tests.py --run-all
    python run_integration_tests.py --run-basic
    python run_integration_tests.py --run-performance
"""

import argparse
import asyncio
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


def check_environment() -> Dict[str, bool]:
    """Check if environment is properly configured for integration tests."""
    checks = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "dotenv_available": DOTENV_AVAILABLE,
        "pytest_available": True,
        "internet_connection": True  # We'll assume this for now
    }

    # Check pytest availability
    try:
        subprocess.run(["python", "-m", "pytest", "--version"],
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        checks["pytest_available"] = False

    return checks


def print_environment_status():
    """Print current environment status."""
    checks = check_environment()

    print("🔧 Environment Configuration")
    print("=" * 50)

    for check_name, status in checks.items():
        icon = "✅" if status else "❌"
        display_name = check_name.replace("_", " ").title()
        print(f"{icon} {display_name}: {'OK' if status else 'MISSING'}")

    print()

    if not checks["OPENAI_API_KEY"]:
        print("📝 To fix OPENAI_API_KEY:")
        print("   1. Create a .env file in the project root")
        print("   2. Add: OPENAI_API_KEY=your_actual_api_key_here")
        print("   3. Get an API key from: https://platform.openai.com/api-keys")
        print()

    if not checks["dotenv_available"]:
        print("📝 To install python-dotenv:")
        print("   pip install python-dotenv")
        print()

    ready_for_tests = all(checks.values())

    if ready_for_tests:
        print("🚀 Environment is ready for integration tests!")
    else:
        print("⚠️  Environment needs configuration before running tests.")

    return ready_for_tests


def run_pytest_command(args: List[str]) -> int:
    """Run pytest with the given arguments."""
    cmd = ["python", "-m", "pytest"] + args
    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def run_basic_tests() -> int:
    """Run basic integration tests (fast, essential functionality)."""
    print("🧪 Running Basic Integration Tests")
    print("=" * 50)

    args = [
        "tests/integration/test_real_llm_integration.py::TestRealLLMIntegration::test_basic_llm_call",
        "tests/integration/test_real_llm_integration.py::TestRealLLMIntegration::test_complex_reasoning",
        "-v",
        "-m", "real_api",
        "--tb=short"
    ]

    return run_pytest_command(args)


def run_comprehensive_tests() -> int:
    """Run all integration tests except performance tests."""
    print("🔬 Running Comprehensive Integration Tests")
    print("=" * 50)

    args = [
        "tests/integration/test_real_llm_integration.py",
        "-v",
        "-m", "real_api and not slow",
        "--tb=short"
    ]

    return run_pytest_command(args)


def run_performance_tests() -> int:
    """Run performance-focused tests (slow)."""
    print("⚡ Running Performance Tests")
    print("=" * 50)

    args = [
        "tests/integration/test_real_llm_integration.py::TestRealPerformanceMetrics",
        "-v",
        "-m", "real_api and slow",
        "--tb=short",
        "-s"  # Show print output for timing info
    ]

    return run_pytest_command(args)


def run_all_tests() -> int:
    """Run all integration tests including performance tests."""
    print("🚀 Running All Integration Tests")
    print("=" * 50)

    args = [
        "tests/integration/test_real_llm_integration.py",
        "-v",
        "-m", "real_api",
        "--tb=short"
    ]

    return run_pytest_command(args)


def run_mock_integration_tests() -> int:
    """Run the original mock-based integration tests."""
    print("🎭 Running Mock Integration Tests")
    print("=" * 50)

    args = [
        "tests/integration/",
        "-v",
        "-m", "integration and not real_api",
        "--tb=short"
    ]

    return run_pytest_command(args)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Integration Test Runner for Mini Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_integration_tests.py --check-env     # Check environment setup
  python run_integration_tests.py --run-basic     # Run basic real API tests
  python run_integration_tests.py --run-all       # Run all real API tests
  python run_integration_tests.py --run-mock      # Run mock integration tests
  python run_integration_tests.py --run-perf      # Run performance tests only

Test Markers:
  real_api  - Tests that make real API calls
  slow      - Tests that take longer to run
  unit      - Unit tests (not integration)
        """
    )

    parser.add_argument("--check-env", action="store_true",
                       help="Check environment configuration")
    parser.add_argument("--run-basic", action="store_true",
                       help="Run basic integration tests (fast)")
    parser.add_argument("--run-all", action="store_true",
                       help="Run all real API integration tests")
    parser.add_argument("--run-comprehensive", action="store_true",
                       help="Run comprehensive tests (exclude performance)")
    parser.add_argument("--run-perf", action="store_true",
                       help="Run performance tests only")
    parser.add_argument("--run-mock", action="store_true",
                       help="Run mock-based integration tests")

    args = parser.parse_args()

    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        return 0

    # Check environment first
    if args.check_env:
        print_environment_status()
        return 0

    # For any test runs, check environment first
    if any([args.run_basic, args.run_all, args.run_comprehensive, args.run_perf]):
        print("🔍 Checking Environment...")
        ready = print_environment_status()
        print()

        if not ready:
            print("❌ Environment not ready. Use --check-env for details.")
            return 1

    # Run requested tests
    exit_code = 0

    if args.run_mock:
        exit_code = run_mock_integration_tests()
    elif args.run_basic:
        exit_code = run_basic_tests()
    elif args.run_comprehensive:
        exit_code = run_comprehensive_tests()
    elif args.run_perf:
        exit_code = run_performance_tests()
    elif args.run_all:
        exit_code = run_all_tests()

    # Print summary
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())