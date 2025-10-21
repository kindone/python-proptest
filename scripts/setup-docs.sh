#!/bin/bash
# Setup script for documentation development

set -e

echo "📚 Setting up documentation environment..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo "💡 To activate the virtual environment, run: source venv/bin/activate"
fi

# Install documentation dependencies
echo "📦 Installing documentation dependencies..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    pip install -e ".[docs]"
else
    source venv/bin/activate && pip install -e ".[docs]"
fi

# Test mkdocs installation
echo "🧪 Testing MkDocs installation..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    python -m mkdocs --version
else
    source venv/bin/activate && python -m mkdocs --version
fi

echo "✅ Documentation environment setup complete!"
echo ""
echo "📖 Available commands:"
echo "  make docs-build     # Build documentation"
echo "  make docs-serve     # Serve documentation locally"
echo "  make docs-deploy    # Deploy to GitHub Pages"
echo ""
echo "🌐 To serve documentation locally:"
echo "  make docs-serve"
echo "  # Then open http://127.0.0.1:8000/python-proptest/ in your browser"
