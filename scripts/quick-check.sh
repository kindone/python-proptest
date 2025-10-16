#!/bin/bash

# Quick pre-commit check script for PyPropTest
# Faster version that runs only the most critical checks

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

echo "⚡ PyPropTest Quick Check"
echo "========================"

# Critical flake8 checks
print_status "Critical flake8 checks..."
if flake8 pyproptest --count --select=E9,F63,F7,F82 --show-source --statistics; then
    print_success "Critical flake8 passed"
else
    print_error "Critical flake8 failed"
    exit 1
fi

# Black formatting
print_status "Black formatting check..."
if black --check pyproptest/ tests/; then
    print_success "Formatting passed"
else
    print_error "Formatting issues found - run 'black pyproptest/ tests/' to fix"
    exit 1
fi

# MyPy type checking
print_status "MyPy type checking..."
if mypy pyproptest/; then
    print_success "Type checking passed"
else
    print_error "Type checking failed"
    exit 1
fi

# Quick test run
print_status "Quick test run..."
if python -m unittest discover tests -q; then
    print_success "Tests passed"
else
    print_error "Tests failed"
    exit 1
fi

print_success "Quick check passed! 🎉"
