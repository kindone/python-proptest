#!/bin/bash

# Script to clean trailing whitespaces from documentation and code files

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}🔍 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }

echo "🧹 Cleaning Trailing Whitespaces"
echo "================================"
echo ""

# Clean markdown files
print_status "Cleaning trailing whitespaces in .md files..."
find . -name "*.md" -exec sed -i '' 's/[[:space:]]*$//' {} \;
print_success "Markdown files cleaned"

# Clean Python files
print_status "Cleaning trailing whitespaces in .py files..."
find . -name "*.py" -exec sed -i '' 's/[[:space:]]*$//' {} \;
print_success "Python files cleaned"

# Clean shell scripts
print_status "Cleaning trailing whitespaces in .sh files..."
find . -name "*.sh" -exec sed -i '' 's/[[:space:]]*$//' {} \;
print_success "Shell scripts cleaned"

# Clean YAML files
print_status "Cleaning trailing whitespaces in .yml and .yaml files..."
find . -name "*.yml" -exec sed -i '' 's/[[:space:]]*$//' {} \;
find . -name "*.yaml" -exec sed -i '' 's/[[:space:]]*$//' {} \;
print_success "YAML files cleaned"

# Clean TOML files
print_status "Cleaning trailing whitespaces in .toml files..."
find . -name "*.toml" -exec sed -i '' 's/[[:space:]]*$//' {} \;
print_success "TOML files cleaned"

echo ""
print_success "All trailing whitespaces have been cleaned! 🎉"
echo ""
echo "Files cleaned:"
echo "  📄 Markdown files (.md)"
echo "  🐍 Python files (.py)"
echo "  🔧 Shell scripts (.sh)"
echo "  ⚙️  YAML files (.yml, .yaml)"
echo "  📋 TOML files (.toml)"
