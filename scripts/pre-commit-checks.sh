#!/bin/bash

# Pre-commit checks script for PyPropTest
# Run this script before committing/pushing to ensure all CI checks pass

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔍 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run a check and handle errors
run_check() {
    local check_name="$1"
    local command="$2"
    
    print_status "Running $check_name..."
    
    if eval "$command"; then
        print_success "$check_name passed"
        return 0
    else
        print_error "$check_name failed"
        return 1
    fi
}

# Main execution
main() {
    echo "🚀 PyPropTest Pre-commit Checks"
    echo "================================"
    echo ""
    
    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Check if required tools are installed
    print_status "Checking required tools..."
    
    local missing_tools=()
    
    if ! command_exists python3; then
        missing_tools+=("python3")
    fi
    
    if ! command_exists pip; then
        missing_tools+=("pip")
    fi
    
    if ! command_exists flake8; then
        missing_tools+=("flake8")
    fi
    
    if ! command_exists black; then
        missing_tools+=("black")
    fi
    
    if ! command_exists isort; then
        missing_tools+=("isort")
    fi
    
    if ! command_exists mypy; then
        missing_tools+=("mypy")
    fi
    
    if ! command_exists pytest; then
        missing_tools+=("pytest")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_warning "Please install missing tools and try again"
        exit 1
    fi
    
    print_success "All required tools are available"
    echo ""
    
    # Track overall success
    local failed_checks=()
    
    # Step 1: Install/update dependencies
    print_status "Installing/updating dependencies..."
    if pip install -e ".[dev]" >/dev/null 2>&1; then
        print_success "Dependencies installed/updated"
    else
        print_error "Failed to install dependencies"
        failed_checks+=("Dependencies")
    fi
    echo ""
    
    # Step 2: Critical flake8 checks
    if ! run_check "Critical flake8 checks" "flake8 pyproptest --count --select=E9,F63,F7,F82 --show-source --statistics"; then
        failed_checks+=("Critical flake8")
    fi
    
    # Step 3: Extended flake8 checks
    if ! run_check "Extended flake8 checks" "flake8 pyproptest --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics"; then
        failed_checks+=("Extended flake8")
    fi
    
    # Step 4: Black formatting check
    if ! run_check "Black formatting check" "black --check pyproptest/ tests/"; then
        print_warning "Code formatting issues found. Run 'black pyproptest/ tests/' to fix"
        failed_checks+=("Black formatting")
    fi
    
    # Step 5: Import sorting check
    if ! run_check "Import sorting check" "isort --check-only pyproptest/ tests/"; then
        print_warning "Import sorting issues found. Run 'isort pyproptest/ tests/' to fix"
        failed_checks+=("Import sorting")
    fi
    
    # Step 6: MyPy type checking
    if ! run_check "MyPy type checking" "mypy pyproptest/"; then
        failed_checks+=("MyPy type checking")
    fi
    
    # Step 7: Unittest tests
    if ! run_check "Unittest tests" "python -m unittest discover tests -v >/dev/null 2>&1"; then
        failed_checks+=("Unittest tests")
    fi
    
    # Step 8: Pytest tests with coverage
    if ! run_check "Pytest tests with coverage" "pytest --cov=pyproptest --cov-report=term-missing -q >/dev/null 2>&1"; then
        failed_checks+=("Pytest tests")
    fi
    
    # Step 9: Security analysis (optional - don't fail on warnings)
    print_status "Running security analysis..."
    if bandit -r pyproptest/ -f json -o bandit-report.json >/dev/null 2>&1; then
        print_success "Security analysis completed"
    else
        print_warning "Security analysis found issues (check bandit-report.json)"
    fi
    
    echo ""
    echo "================================"
    
    # Final results
    if [ ${#failed_checks[@]} -eq 0 ]; then
        print_success "All checks passed! Ready to commit/push 🎉"
        echo ""
        echo "Summary:"
        echo "  ✅ Dependencies installed"
        echo "  ✅ Flake8 linting passed"
        echo "  ✅ Code formatting passed"
        echo "  ✅ Import sorting passed"
        echo "  ✅ Type checking passed"
        echo "  ✅ Unittest tests passed"
        echo "  ✅ Pytest tests passed"
        echo "  ✅ Security analysis completed"
        exit 0
    else
        print_error "Some checks failed:"
        for check in "${failed_checks[@]}"; do
            echo "  ❌ $check"
        done
        echo ""
        print_warning "Please fix the issues above before committing/pushing"
        exit 1
    fi
}

# Run main function
main "$@"
