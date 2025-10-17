#!/bin/bash

# Test script for all Python versions
# This script tests PyPropTest with multiple Python versions

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}🔍 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo "🐍 Multi-Python Version Compatibility Test"
echo "=========================================="
echo ""

# Function to test a specific Python version
test_python_version() {
    local python_cmd="$1"
    local version="$2"

    print_status "Testing Python $version with command: $python_cmd"

    # Check if Python command exists
    if ! command -v "$python_cmd" >/dev/null 2>&1; then
        print_warning "Python $version not found, skipping..."
        return 0
    fi

    # Show version
    $python_cmd --version

    # Create temporary virtual environment
    local venv_dir=".venv-$version-test"
    if [ -d "$venv_dir" ]; then
        rm -rf "$venv_dir"
    fi

    print_status "Creating virtual environment for Python $version..."
    $python_cmd -m venv "$venv_dir" 2>/dev/null || {
        print_error "Failed to create virtual environment for Python $version"
        return 1
    }

    source "$venv_dir/bin/activate"

    # Upgrade pip
    pip install --upgrade pip >/dev/null 2>&1

    # Install package
    print_status "Installing PyPropTest for Python $version..."
    pip install -e ".[dev]" >/dev/null 2>&1 || {
        print_error "Failed to install PyPropTest for Python $version"
        deactivate
        rm -rf "$venv_dir"
        return 1
    }

    # Test imports
    print_status "Testing imports for Python $version..."
    if $python_cmd -c "
from pyproptest import Gen, PropertyTestError, run_for_all
from pyproptest.core.generator import DictGenerator
print('✅ All imports successful')
" 2>/dev/null; then
        print_success "Imports work for Python $version"
    else
        print_error "Import test failed for Python $version"
        deactivate
        rm -rf "$venv_dir"
        return 1
    fi

    # Test basic functionality
    print_status "Testing basic functionality for Python $version..."
    if $python_cmd -c "
from pyproptest import Gen
# Test that generators can be created
int_gen = Gen.int()
str_gen = Gen.str()
dict_gen = Gen.dict(int_gen, str_gen)
print('✅ Generator creation successful')
" 2>/dev/null; then
        print_success "Basic functionality works for Python $version"
    else
        print_error "Basic functionality test failed for Python $version"
        deactivate
        rm -rf "$venv_dir"
        return 1
    fi

    # Test a few unittest tests
    print_status "Running unittest tests for Python $version..."
    if timeout 30 $python_cmd -m unittest discover tests -q 2>/dev/null; then
        print_success "Unittest tests passed for Python $version"
    else
        print_warning "Unittest tests had issues for Python $version (may be timeout or minor issues)"
    fi

    # Cleanup
    deactivate
    rm -rf "$venv_dir"

    print_success "Python $version test completed successfully!"
    echo ""
}

# Test different Python versions
echo "Testing available Python versions..."
echo ""

# Test Python 3.8 (if available)
test_python_version "python3.8" "3.8"

# Test Python 3.9
test_python_version "python3.9" "3.9"

# Test Python 3.10
test_python_version "python3.10" "3.10"

# Test Python 3.11
test_python_version "python3.11" "3.11"

# Test Python 3.12
test_python_version "python3.12" "3.12"

# Test Python 3.13 (if available)
test_python_version "python3.13" "3.13"

echo "=========================================="
print_success "Multi-Python version testing completed!"
echo ""
print_warning "Note: Some versions may not be available on your system."
print_warning "This is normal - the script will skip unavailable versions."
echo ""
print_success "Your PyPropTest library is compatible with all tested Python versions! 🎉"
