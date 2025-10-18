#!/bin/bash

# Upload python-proptest package to TestPyPI

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

echo "🚀 Uploading python-proptest to TestPyPI"
echo "==================================="
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

# Check for API token
if [ -z "$TESTPYPI_API_TOKEN" ]; then
    print_warning "TESTPYPI_API_TOKEN environment variable not set."
    echo ""
    echo "To upload to TestPyPI, you need to:"
    echo "1. Create a TestPyPI account at https://test.pypi.org/account/register/"
    echo "2. Create an API token at https://test.pypi.org/manage/account/token/"
    echo "3. Set the environment variable:"
    echo "   export TESTPYPI_API_TOKEN='pypi-your-token-here'"
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

# Upload to TestPyPI
print_status "Uploading to TestPyPI..."
if [ -n "$TESTPYPI_API_TOKEN" ]; then
    # Use API token
    twine upload --repository testpypi --username __token__ --password "$TESTPYPI_API_TOKEN" dist/*
else
    # Manual authentication
    twine upload --repository testpypi dist/*
fi

print_success "Package uploaded to TestPyPI successfully! 🎉"
echo ""
echo "TestPyPI URL: https://test.pypi.org/project/proptest/"
echo ""
echo "To test the installation from TestPyPI:"
echo "  pip install --index-url https://test.pypi.org/simple/ proptest"
echo ""
echo "Or create a test script:"
echo "  python -c \"import proptest; print('Installation successful!')\""
echo ""
print_warning "Remember: TestPyPI packages are temporary and will be deleted after 30 days."
echo ""
echo "Next steps:"
echo "  1. Test installation from TestPyPI"
echo "  2. If everything works, upload to production PyPI: ./scripts/upload-pypi.sh"
