#!/bin/bash

# Version bumping script for PyPropTest

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

# Function to get current version
get_current_version() {
    grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'
}

# Function to update version in pyproject.toml
update_version() {
    local new_version=$1
    sed -i '' "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
}

# Function to bump version
bump_version() {
    local current_version=$1
    local bump_type=$2
    
    # Split version into parts
    IFS='.' read -ra VERSION_PARTS <<< "$current_version"
    local major=${VERSION_PARTS[0]}
    local minor=${VERSION_PARTS[1]}
    local patch=${VERSION_PARTS[2]}
    
    case $bump_type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            print_error "Invalid bump type: $bump_type. Use major, minor, or patch."
            exit 1
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

# Main script
echo "📈 PyPropTest Version Bumper"
echo "============================"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Get current version
current_version=$(get_current_version)
print_status "Current version: $current_version"

# Get bump type from command line or prompt
if [ $# -eq 1 ]; then
    bump_type=$1
else
    echo ""
    echo "Available bump types:"
    echo "  patch  - Bug fixes (0.1.0 -> 0.1.1)"
    echo "  minor  - New features (0.1.0 -> 0.2.0)"
    echo "  major  - Breaking changes (0.1.0 -> 1.0.0)"
    echo ""
    read -p "Enter bump type (patch/minor/major): " bump_type
fi

# Validate bump type
if [[ ! "$bump_type" =~ ^(patch|minor|major)$ ]]; then
    print_error "Invalid bump type: $bump_type. Use patch, minor, or major."
    exit 1
fi

# Calculate new version
new_version=$(bump_version "$current_version" "$bump_type")
print_status "New version: $new_version"

# Confirm the change
echo ""
read -p "Update version from $current_version to $new_version? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Version bump cancelled"
    exit 1
fi

# Update version in pyproject.toml
print_status "Updating version in pyproject.toml..."
update_version "$new_version"
print_success "Version updated to $new_version"

# Show git status
echo ""
print_status "Git status:"
git status --porcelain

# Ask if user wants to commit and tag
echo ""
read -p "Create git commit and tag for version $new_version? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Commit changes
    print_status "Creating git commit..."
    git add pyproject.toml
    git commit -m "Bump version to $new_version"
    print_success "Git commit created"
    
    # Create tag
    print_status "Creating git tag..."
    git tag -a "v$new_version" -m "Release version $new_version"
    print_success "Git tag v$new_version created"
    
    echo ""
    print_success "Version bump complete! 🎉"
    echo ""
    echo "Next steps:"
    echo "  1. Push changes: git push origin main"
    echo "  2. Push tags: git push origin v$new_version"
    echo "  3. Build package: make build-package"
    echo "  4. Upload to PyPI: make upload-pypi"
    echo ""
    echo "Or use GitHub Actions for automated release!"
else
    echo ""
    print_success "Version updated to $new_version"
    echo ""
    echo "Manual steps:"
    echo "  1. Review changes: git diff"
    echo "  2. Commit when ready: git add pyproject.toml && git commit -m 'Bump version to $new_version'"
    echo "  3. Create tag: git tag -a v$new_version -m 'Release version $new_version'"
fi
