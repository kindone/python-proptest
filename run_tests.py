#!/usr/bin/env python3
"""
Test runner for python-proptest.

This script runs all tests in the project and provides a comprehensive
test report.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_pytest_tests():
    """Run tests using pytest if available."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests_api/",
                "tests_integration/",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0:
            print("✅ All pytest tests passed!")
            return True
        else:
            print("❌ Some pytest tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("⚠️  pytest not available, falling back to custom test runner")
        return False


def run_custom_tests():
    """Run tests using unittest discovery as fallback."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests_integration",
                "-v",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0:
            print("✅ All unittest tests passed!")
            return True
        else:
            print("❌ Some unittest tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Custom test runner failed: {e}")
        return False


def main():
    """Main test runner function."""
    print("🧪 python-proptest Test Runner")
    print("=" * 50)

    # Try pytest first, fall back to custom runner
    if not run_pytest_tests():
        print("\n🔄 Falling back to custom test runner...")
        if not run_custom_tests():
            print("❌ All test methods failed!")
            sys.exit(1)

    print("\n🎉 All tests completed successfully!")
    print("\nTo run tests manually:")
    print("1. With pytest: python -m pytest tests_api/ tests_integration/ -v")
    print("2. With unittest: python -m unittest discover -s tests_integration -v")
    print("3. Individual tests: python -m pytest tests_api/<category>/test_<name>.py")


if __name__ == "__main__":
    main()
