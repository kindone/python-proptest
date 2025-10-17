#!/bin/bash

# Upload PyPropTest package to production PyPI

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

echo "🚀 Uploading PyPropTest to PyPI"
echo "==============================="
echo ""

# Check if dist directory exists
if [ ! -d "dist" ] || [ ! "$(ls -A dist)" ]; then
    print_error "No built packages found in dist/. Run ./scripts/build-package.sh first."
    exit 1
fi

# Check if twine is installed
print_status "Checking upload tools..."
if ! command -v twine >/dev/null 2>&1; then
    print_warning "Twine not found. Installing..."
    pip install twine
fi

# Final confirmation
print_warning "⚠️  WARNING: This will upload to PRODUCTION PyPI!"
echo ""
echo "Make sure you have:"
echo "  ✅ Tested the package locally"
echo "  ✅ Tested installation from TestPyPI"
echo "  ✅ Verified all functionality works"
echo "  ✅ Updated version number if needed"
echo "  ✅ Updated changelog/release notes"
echo ""
read -p "Are you sure you want to upload to production PyPI? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Upload cancelled"
    exit 1
fi

# Check for API token
if [ -z "$PYPI_API_TOKEN" ]; then
    print_warning "PYPI_API_TOKEN environment variable not set."
    echo ""
    echo "To upload to PyPI, you need to:"
    echo "1. Create a PyPI account at https://pypi.org/account/register/"
    echo "2. Create an API token at https://pypi.org/manage/account/token/"
    echo "3. Set the environment variable:"
    echo "   export PYPI_API_TOKEN='pypi-your-token-here'"
    echo ""
    echo "Or you can enter your credentials when prompted."
    echo ""
    read -p "Do you want to continue with manual authentication? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Upload cancelled"
        exit 1
    fi
fi

# Upload to PyPI
print_status "Uploading to PyPI..."
if [ -n "$PYPI_API_TOKEN" ]; then
    # Use API token
    twine upload --username __token__ --password "$PYPI_API_TOKEN" dist/*
else
    # Manual authentication
    twine upload dist/*
fi

print_success "Package uploaded to PyPI successfully! 🎉"
echo ""
echo "PyPI URL: https://pypi.org/project/pyproptest/"
echo ""
echo "Installation command:"
echo "  pip install pyproptest"
echo ""
echo "🎉 Congratulations! PyPropTest is now available on PyPI!"
echo ""
echo "Next steps:"
echo "  1. Verify the package page: https://pypi.org/project/pyproptest/"
echo "  2. Test installation: pip install pyproptest"
echo "  3. Update documentation with installation instructions"
echo "  4. Create a GitHub release"
echo "  5. Announce the release!"
