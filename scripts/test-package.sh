#!/bin/bash

# Test python-proptest package after building

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

echo "🧪 Testing python-proptest Package"
echo "============================="
echo ""

# Check if dist directory exists
if [ ! -d "dist" ] || [ ! "$(ls -A dist)" ]; then
    print_error "No built packages found in dist/. Run ./scripts/build-package.sh first."
    exit 1
fi

# Create temporary test directory
TEST_DIR=".test-package"
if [ -d "$TEST_DIR" ]; then
    rm -rf "$TEST_DIR"
fi

mkdir "$TEST_DIR"
cd "$TEST_DIR"

print_status "Created temporary test environment"

# Create virtual environment
print_status "Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip >/dev/null 2>&1

# Install the package from dist
print_status "Installing package from dist..."
pip install ../dist/*.whl >/dev/null 2>&1

print_success "Package installed successfully"

# Test 1: Basic import
print_status "Test 1: Basic import test..."
if python -c "
from python_proptest import Gen, PropertyTestError, run_for_all
print('✅ Basic imports successful')
"; then
    print_success "Basic import test passed"
else
    print_error "Basic import test failed"
    exit 1
fi

# Test 2: Generator creation
print_status "Test 2: Generator creation test..."
if python -c "
from python_proptest import Gen
# Test that generators can be created
int_gen = Gen.int()
str_gen = Gen.str()
dict_gen = Gen.dict(int_gen, str_gen)
print('✅ Generator creation successful')
"; then
    print_success "Generator creation test passed"
else
    print_error "Generator creation test failed"
    exit 1
fi

# Test 3: Property testing
print_status "Test 3: Property testing test..."
if python -c "
from python_proptest import Gen, for_all

@for_all(Gen.int(), Gen.int())
def test_addition_commutative(x, y):
    assert x + y == y + x

# This should not raise an exception
print('✅ Property testing successful')
"; then
    print_success "Property testing test passed"
else
    print_error "Property testing test failed"
    exit 1
fi

# Test 4: Package info
print_status "Test 4: Package information..."
if python -c "
import python_proptest
print(f'✅ Package version: {python_proptest.__version__ if hasattr(python_proptest, \"__version__\") else \"Unknown\"}')
print(f'✅ Package location: {python_proptest.__file__}')
"; then
    print_success "Package information test passed"
else
    print_warning "Package information test had issues (this is okay)"
fi

# Test 5: Unittest integration
print_status "Test 5: Unittest integration test..."
if python -c "
import unittest
from python_proptest import Gen, for_all

class TestIntegration(unittest.TestCase):
    @for_all(Gen.int())
    def test_positive_property(self, x):
        self.assertIsInstance(x, int)

# This should not raise an exception
print('✅ Unittest integration successful')
"; then
    print_success "Unittest integration test passed"
else
    print_error "Unittest integration test failed"
    exit 1
fi

# Cleanup
deactivate
cd ..
rm -rf "$TEST_DIR"

echo ""
echo "============================="
print_success "All package tests passed! 🎉"
echo ""
echo "Package is ready for PyPI upload!"
echo ""
echo "Next steps:"
echo "  1. Upload to TestPyPI: ./scripts/upload-testpypi.sh"
echo "  2. Test from TestPyPI: pip install --index-url https://test.pypi.org/simple/ proptest"
echo "  3. Upload to PyPI: ./scripts/upload-pypi.sh"
