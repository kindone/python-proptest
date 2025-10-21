# Documentation Deployment

This document explains how the documentation is deployed to GitHub Pages.

## Local Development

To work on documentation locally:

```bash
# Set up documentation environment
./scripts/setup-docs.sh

# Build documentation
make docs-build

# Serve documentation locally
make docs-serve
# Open http://127.0.0.1:8000/python-proptest/ in your browser
```

## GitHub Pages Deployment

The documentation is automatically deployed to GitHub Pages using GitHub Actions when changes are pushed to the `main` branch.

### Deployment Process

1. **Trigger**: Push to `main` branch
2. **Build**: Install dependencies and build documentation with `mkdocs build`
3. **Deploy**: Use `mkdocs gh-deploy --force` to deploy to GitHub Pages
4. **Result**: Documentation available at https://kindone.github.io/python-proptest/

### Key Configuration

- **Theme**: Material theme with proper navigation
- **Site URL**: https://kindone.github.io/python-proptest/
- **Repository**: kindone/python-proptest
- **Branch**: gh-pages (automatically created)

### Troubleshooting

If the documentation appears as a single page without navigation:

1. **Check theme installation**: Ensure `mkdocs-material` is installed
2. **Verify navigation**: Check that `nav` section in `mkdocs.yml` is correct
3. **Clear cache**: GitHub Pages may cache old versions
4. **Check deployment**: Ensure `mkdocs gh-deploy` is used, not manual file copying

### Manual Deployment

If you need to deploy manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Deploy to GitHub Pages
mkdocs gh-deploy --force
```

### Files

- `.github/workflows/docs.yml` - GitHub Actions workflow
- `mkdocs.yml` - MkDocs configuration
- `docs/` - Documentation source files
- `site/` - Built documentation (generated, not committed)
