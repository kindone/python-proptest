#!/usr/bin/env python3
"""
Pre-commit checks script for PyPropTest
Run this script before committing/pushing to ensure all CI checks pass
"""

import subprocess
import sys
import os
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_status(message):
    """Print a status message in blue"""
    print(f"{Colors.BLUE}🔍 {message}{Colors.NC}")


def print_success(message):
    """Print a success message in green"""
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")


def print_error(message):
    """Print an error message in red"""
    print(f"{Colors.RED}❌ {message}{Colors.NC}")


def print_warning(message):
    """Print a warning message in yellow"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")


def run_command(command, description, capture_output=True, allow_failure=False):
    """Run a command and return success status"""
    print_status(f"Running {description}...")

    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
        else:
            result = subprocess.run(command, shell=True, cwd=Path(__file__).parent.parent)

        if result.returncode == 0:
            print_success(f"{description} passed")
            return True
        else:
            if allow_failure:
                print_warning(f"{description} completed with warnings")
                return True
            else:
                print_error(f"{description} failed")
                if capture_output and result.stderr:
                    print(f"Error: {result.stderr}")
                return False
    except Exception as e:
        print_error(f"{description} failed with exception: {e}")
        return False


def check_required_tools():
    """Check if all required tools are available"""
    print_status("Checking required tools...")

    required_tools = [
        "python3", "pip", "flake8", "black", "isort", "mypy", "pytest"
    ]

    missing_tools = []
    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)

    if missing_tools:
        print_error(f"Missing required tools: {', '.join(missing_tools)}")
        print_warning("Please install missing tools and try again")
        return False

    print_success("All required tools are available")
    return True


def main():
    """Main execution function"""
    print("🚀 PyPropTest Pre-commit Checks")
    print("================================")
    print()

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print_error("Please run this script from the project root directory")
        sys.exit(1)

    # Check required tools
    if not check_required_tools():
        sys.exit(1)

    print()

    # Track failed checks
    failed_checks = []

    # Step 1: Install/update dependencies
    if not run_command(
        'pip install -e ".[dev]"',
        "Installing/updating dependencies",
        capture_output=True
    ):
        failed_checks.append("Dependencies")

    # Step 2: Critical flake8 checks
    if not run_command(
        "flake8 pyproptest --count --select=E9,F63,F7,F82 --show-source --statistics",
        "Critical flake8 checks"
    ):
        failed_checks.append("Critical flake8")

    # Step 3: Extended flake8 checks
    if not run_command(
        "flake8 pyproptest --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics",
        "Extended flake8 checks"
    ):
        failed_checks.append("Extended flake8")

    # Step 4: Black formatting check
    if not run_command(
        "black --check pyproptest/ tests/",
        "Black formatting check"
    ):
        print_warning("Code formatting issues found. Run 'black pyproptest/ tests/' to fix")
        failed_checks.append("Black formatting")

    # Step 5: Import sorting check
    if not run_command(
        "isort --check-only pyproptest/ tests/",
        "Import sorting check"
    ):
        print_warning("Import sorting issues found. Run 'isort pyproptest/ tests/' to fix")
        failed_checks.append("Import sorting")

    # Step 6: MyPy type checking
    if not run_command(
        "mypy pyproptest/",
        "MyPy type checking"
    ):
        failed_checks.append("MyPy type checking")

    # Step 7: Unittest tests
    if not run_command(
        "python -m unittest discover tests -v",
        "Unittest tests",
        capture_output=True
    ):
        failed_checks.append("Unittest tests")

    # Step 8: Pytest tests with coverage
    if not run_command(
        "pytest --cov=pyproptest --cov-report=term-missing -q",
        "Pytest tests with coverage",
        capture_output=True
    ):
        failed_checks.append("Pytest tests")

    # Step 9: Security analysis (optional)
    run_command(
        "bandit -r pyproptest/ -f json -o bandit-report.json",
        "Security analysis",
        allow_failure=True
    )

    print()
    print("================================")

    # Final results
    if not failed_checks:
        print_success("All checks passed! Ready to commit/push 🎉")
        print()
        print("Summary:")
        print("  ✅ Dependencies installed")
        print("  ✅ Flake8 linting passed")
        print("  ✅ Code formatting passed")
        print("  ✅ Import sorting passed")
        print("  ✅ Type checking passed")
        print("  ✅ Unittest tests passed")
        print("  ✅ Pytest tests passed")
        print("  ✅ Security analysis completed")
        sys.exit(0)
    else:
        print_error("Some checks failed:")
        for check in failed_checks:
            print(f"  ❌ {check}")
        print()
        print_warning("Please fix the issues above before committing/pushing")
        sys.exit(1)


if __name__ == "__main__":
    main()
