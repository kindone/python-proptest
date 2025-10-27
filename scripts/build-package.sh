#!/bin/bash

# Build python-proptest package for PyPI distribution

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

echo "📦 Building python-proptest Package"
echo "=============================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if build tools are installed
print_status "Checking build tools..."
if ! command -v python -m build >/dev/null 2>&1; then
    print_warning "Build tools not found. Installing..."
    pip install build
fi

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/
print_success "Previous builds cleaned"

# Run pre-build checks
print_status "Running pre-build checks..."
if ! make quick-check >/dev/null 2>&1; then
    print_error "Pre-build checks failed. Please fix issues before building."
    exit 1
fi
print_success "Pre-build checks passed"

# Build the package
print_status "Building package..."
python -m build

# Check build results
if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
    print_success "Package built successfully!"
    echo ""
    echo "Build artifacts:"
    ls -la dist/
    echo ""

    # Show package info
    print_status "Package information:"
    python -m build --wheel --sdist --outdir dist/ >/dev/null 2>&1 || true

    if [ -f "dist/python-proptest-*.whl" ]; then
        echo "Wheel: $(ls dist/*.whl)"
    fi

    if [ -f "dist/python-proptest-*.tar.gz" ]; then
        echo "Source: $(ls dist/*.tar.gz)"
    fi

    echo ""
    print_success "Package is ready for upload to PyPI! 🎉"
    echo ""
    echo "Next steps:"
    echo "  1. Test the package: ./scripts/test-package.sh"
    echo "  2. Upload to TestPyPI: ./scripts/upload-testpypi.sh"
    echo "  3. Upload to PyPI: ./scripts/upload-pypi.sh"

else
    print_error "Build failed - no artifacts found in dist/"
    exit 1
fi
