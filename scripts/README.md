# PyPropTest Development Scripts

This directory contains scripts to help with development and pre-commit checks.

## Available Scripts

### 🚀 Pre-commit Checks

#### `pre-commit-checks.sh` (Bash version)
Comprehensive pre-commit script that runs all CI checks:
```bash
./scripts/pre-commit-checks.sh
```

#### `pre-commit-checks.py` (Python version)
Same functionality as the bash version, but written in Python:
```bash
./scripts/pre-commit-checks.py
```

**What it checks:**
- ✅ Dependencies installation
- ✅ Critical flake8 linting (E9, F63, F7, F82)
- ✅ Extended flake8 linting (style, complexity)
- ✅ Black code formatting
- ✅ Import sorting with isort
- ✅ MyPy type checking
- ✅ Unittest tests (310 tests)
- ✅ Pytest tests with coverage (321 tests)
- ✅ Security analysis with bandit

### ⚡ Quick Check

#### `quick-check.sh`
Fast pre-commit check that runs only the most critical checks:
```bash
./scripts/quick-check.sh
```

**What it checks:**
- ✅ Critical flake8 linting
- ✅ Black formatting
- ✅ MyPy type checking
- ✅ Quick unittest test run

## Using Make Commands

For convenience, you can also use the Makefile in the project root:

```bash
# Quick check (fastest)
make quick-check

# Full pre-commit check
make pre-commit

# All CI checks
make all-checks

# Individual checks
make lint
make format
make type-check
make test
make security

# Show all available commands
make help
```

## Recommended Workflow

### Before Every Commit
```bash
# Quick check (recommended for frequent commits)
make quick-check
```

### Before Pushing to GitHub
```bash
# Full pre-commit check (recommended before push)
make pre-commit
```

### Before Release
```bash
# All CI checks (same as GitHub Actions)
make all-checks
```

## Troubleshooting

### Common Issues

1. **Missing tools**: Install required development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. **Formatting issues**: Auto-fix with:
   ```bash
   make format
   ```

3. **Import sorting issues**: Auto-fix with:
   ```bash
   isort pyproptest/ tests/
   ```

4. **Type checking errors**: Check the mypy output and fix type annotations

5. **Test failures**: Run tests individually to debug:
   ```bash
   python -m unittest discover tests -v
   pytest -v
   ```

### Script Permissions

If you get permission errors, make sure the scripts are executable:
```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

## Integration with Git Hooks

You can integrate these scripts with Git hooks for automatic checking:

### Pre-commit Hook
```bash
# Create pre-commit hook
echo '#!/bin/bash\n./scripts/quick-check.sh' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Pre-push Hook
```bash
# Create pre-push hook
echo '#!/bin/bash\n./scripts/pre-commit-checks.sh' > .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

## CI/CD Integration

These scripts mirror the checks run in GitHub Actions (`.github/workflows/ci.yml`), so passing locally means your CI will also pass.
