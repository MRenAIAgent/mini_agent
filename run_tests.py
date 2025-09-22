#!/usr/bin/env python3
"""Test runner script for mini_agent project."""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional


def setup_environment():
    """Setup the test environment."""
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Create logs directory if it doesn't exist
    logs_dir = project_root / "tests" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Set environment variables for testing
    os.environ["TESTING"] = "1"
    os.environ["PYTHONPATH"] = str(project_root)


def run_pytest(
    test_path: Optional[str] = None,
    markers: Optional[List[str]] = None,
    verbose: bool = True,
    coverage: bool = False,
    parallel: bool = False,
    extra_args: Optional[List[str]] = None
) -> int:
    """Run pytest with specified options."""

    cmd = ["python", "-m", "pytest"]

    # Add test path
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")

    # Add markers
    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])

    # Add verbosity
    if verbose:
        cmd.append("-v")

    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])

    # Add parallel execution
    if parallel:
        try:
            import pytest_xdist
            cmd.extend(["-n", "auto"])
        except ImportError:
            print("Warning: pytest-xdist not installed, running sequentially")

    # Add extra arguments
    if extra_args:
        cmd.extend(extra_args)

    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def run_unit_tests(verbose: bool = True, coverage: bool = False) -> int:
    """Run unit tests only."""
    print("Running unit tests...")
    return run_pytest(
        test_path="tests/unit/",
        markers=["unit"],
        verbose=verbose,
        coverage=coverage
    )


def run_integration_tests(verbose: bool = True) -> int:
    """Run integration tests only."""
    print("Running integration tests...")
    return run_pytest(
        test_path="tests/integration/",
        markers=["integration"],
        verbose=verbose
    )


def run_smoke_tests(verbose: bool = True) -> int:
    """Run smoke tests for quick validation."""
    print("Running smoke tests...")
    return run_pytest(
        markers=["smoke"],
        verbose=verbose
    )


def run_all_tests(verbose: bool = True, coverage: bool = False, parallel: bool = False) -> int:
    """Run all tests."""
    print("Running all tests...")
    return run_pytest(
        verbose=verbose,
        coverage=coverage,
        parallel=parallel
    )


def check_test_dependencies():
    """Check if test dependencies are available."""
    dependencies = {
        "pytest": "pytest",
        "pytest-asyncio": "pytest_asyncio",
        "pytest-cov": "pytest_cov",
        "pytest-xdist": "pytest_xdist",
        "pytest-timeout": "pytest_timeout"
    }

    missing = []
    for name, module in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {name} is available")
        except ImportError:
            missing.append(name)
            print(f"✗ {name} is missing")

    if missing:
        print(f"\nTo install missing dependencies, run:")
        print(f"pip install {' '.join(missing)}")
        return False

    return True


def lint_code() -> int:
    """Run code linting."""
    linters = [
        (["python", "-m", "flake8", "."], "flake8"),
        (["python", "-m", "black", "--check", "."], "black"),
        (["python", "-m", "isort", "--check-only", "."], "isort"),
        (["python", "-m", "mypy", "."], "mypy")
    ]

    results = []
    for cmd, name in linters:
        print(f"\nRunning {name}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ {name} passed")
            else:
                print(f"✗ {name} failed")
                print(result.stdout)
                print(result.stderr)
            results.append(result.returncode)
        except FileNotFoundError:
            print(f"⚠ {name} not installed, skipping")
            results.append(0)  # Don't fail if linter not installed

    return max(results) if results else 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test runner for mini_agent")

    parser.add_argument(
        "command",
        choices=["unit", "integration", "smoke", "all", "deps", "lint"],
        help="Test command to run"
    )

    parser.add_argument(
        "--path",
        type=str,
        help="Specific test path to run"
    )

    parser.add_argument(
        "--markers",
        nargs="*",
        help="Pytest markers to filter tests"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Run tests in quiet mode"
    )

    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )

    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )

    parser.add_argument(
        "--extra-args",
        nargs="*",
        help="Extra arguments to pass to pytest"
    )

    args = parser.parse_args()

    setup_environment()

    verbose = not args.quiet

    # Execute the requested command
    if args.command == "deps":
        if check_test_dependencies():
            print("\nAll test dependencies are available!")
            return 0
        else:
            return 1

    elif args.command == "lint":
        return lint_code()

    elif args.command == "unit":
        return run_unit_tests(verbose=verbose, coverage=args.coverage)

    elif args.command == "integration":
        return run_integration_tests(verbose=verbose)

    elif args.command == "smoke":
        return run_smoke_tests(verbose=verbose)

    elif args.command == "all":
        return run_all_tests(
            verbose=verbose,
            coverage=args.coverage,
            parallel=args.parallel
        )

    elif args.path or args.markers:
        return run_pytest(
            test_path=args.path,
            markers=args.markers,
            verbose=verbose,
            coverage=args.coverage,
            parallel=args.parallel,
            extra_args=args.extra_args
        )

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())