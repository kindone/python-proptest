# Contributing to python-proptest

Thank you for your interest in contributing to python-proptest! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Setting up the Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/python-proptest.git
   cd python-proptest
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install the package in development mode with all dependencies:
   ```bash
   make install
   ```

## Available Commands

The project includes a comprehensive Makefile with useful development commands:

```bash
# Show all available commands
make help

# Quick Commands
make quick-check    # Run quick pre-commit checks (fast)
make pre-commit     # Run full pre-commit checks
make all-checks     # Run all CI checks

# Individual Checks
make install        # Install dependencies
make test           # Run all tests (unittest + pytest)
make lint           # Run flake8 linting
make format         # Format code with black and isort
make type-check     # Run mypy type checking
make security       # Run security analysis

# Python Version Testing
make test-python38  # Test Python 3.8 compatibility
make test-all-python # Test all available Python versions

# PyPI Publishing
make bump-version   # Bump version (patch/minor/major)
make build-package  # Build package for PyPI distribution
make test-package   # Test built package locally
make upload-testpypi # Upload to TestPyPI
make upload-pypi    # Upload to production PyPI

# Utilities
make clean          # Clean up generated files
make clean-whitespace # Clean trailing whitespaces from all files
```

## Development Workflow

### Running Tests

```bash
# Run all tests (unittest + pytest with coverage)
make test

# Run quick pre-commit checks (fast)
make quick-check

# Run full pre-commit checks
make pre-commit

# Run all CI checks
make all-checks
```

### Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Format code with black and isort
make format

# Run linting checks
make lint

# Run type checking
make type-check

# Run security analysis
make security

# Run all quality checks at once
make all-checks
```

### Python Version Testing

```bash
# Test Python 3.8 compatibility
make test-python38

# Test all available Python versions
make test-all-python
```

### Building Documentation

```bash
# Build documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-generator` for new features
- `fix/shrinking-bug` for bug fixes
- `docs/update-readme` for documentation updates
- `refactor/cleanup-generators` for refactoring

### Commit Messages

Follow conventional commit format:
- `feat: add new generator for custom types`
- `fix: resolve shrinking issue with nested lists`
- `docs: update installation instructions`
- `test: add property tests for edge cases`
- `refactor: simplify generator interface`

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Run pre-commit checks: `make pre-commit`
5. Ensure all tests pass: `make all-checks`
6. Update documentation if needed
7. Submit a pull request

### Pre-commit Workflow

Before committing, run the pre-commit checks to ensure code quality:

```bash
# Quick check (fast, for frequent commits)
make quick-check

# Full check (comprehensive, before pushing)
make pre-commit

# All CI checks (before submitting PR)
make all-checks
```

## Code Style

### Python Style

- Follow PEP 8
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep functions small and focused
- Use meaningful variable names

### Property-Based Testing Style

- Write clear, focused properties
- Use descriptive test names
- Include docstrings explaining what the property tests
- Prefer simple properties over complex ones
- Use appropriate generators for the domain

### Example

```python
from python_proptest import for_all, Gen

class TestStringOperations:
    @for_all(Gen.str(), Gen.str())
    def test_string_concatenation_length(self, s1: str, s2: str):
        """Test that string concatenation preserves length property."""
        result = s1 + s2
        assert len(result) == len(s1) + len(s2)
        assert result.startswith(s1)
        assert result.endswith(s2)
```

## Testing Guidelines

### Writing Property-Based Tests

1. **Focus on invariants**: Test properties that should always hold
2. **Use appropriate generators**: Choose generators that match your function's domain
3. **Keep properties simple**: One property should test one invariant
4. **Include edge cases**: Use `Gen.just()` or `Gen.element_of()` for specific values
5. **Document complex properties**: Explain what the property tests

### Test Organization

- Group related tests in classes
- Use descriptive test method names
- Include docstrings for complex tests
- Place examples in `tests/examples/`

## Documentation

### Code Documentation

- Write docstrings for all public APIs
- Use Google-style docstrings
- Include type information
- Provide usage examples

### User Documentation

- Update README.md for significant changes
- Add examples to documentation
- Keep documentation in sync with code changes

## Release Process

Releases can be managed through GitHub Actions or manually using the Makefile commands:

### Automated Release (Recommended)
1. Update version in `pyproject.toml`
2. Create a git tag: `git tag v0.1.1`
3. Push the tag: `git push origin v0.1.1`
4. GitHub Actions will automatically build and publish to PyPI

### Manual Release
```bash
# Bump version (patch/minor/major)
make bump-version

# Build package for PyPI distribution
make build-package

# Test built package locally
make test-package

# Upload to TestPyPI for testing
make upload-testpypi

# Upload to production PyPI
make upload-pypi
```

## Getting Help

- Check existing issues and discussions
- Join our community discussions
- Create an issue for bugs or feature requests
- Ask questions in discussions

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to create a welcoming environment for all contributors.

## License

By contributing to python-proptest, you agree that your contributions will be licensed under the MIT License.
