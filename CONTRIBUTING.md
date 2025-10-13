# Contributing to PyPropTest

Thank you for your interest in contributing to PyPropTest! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Setting up the Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/pyproptest.git
   cd pyproptest
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install the package in development mode with all dependencies:
   ```bash
   pip install -e ".[dev,docs]"
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=pyproptest --cov-report=html

# Run specific test file
pytest tests/test_generators.py

# Run tests with verbose output
pytest -v
```

### Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Format code with black
black pyproptest/ tests/

# Sort imports with isort
isort pyproptest/ tests/

# Lint with flake8
flake8 pyproptest/ tests/

# Type check with mypy
mypy pyproptest/

# Security check with bandit
bandit -r pyproptest/

# Check for known security vulnerabilities
safety check
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
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request

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
from pyproptest import for_all, integers, text

class TestStringOperations:
    @for_all(text(), text())
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

Releases are managed through GitHub Actions:

1. Update version in `pyproject.toml`
2. Create a git tag: `git tag v0.1.1`
3. Push the tag: `git push origin v0.1.1`
4. GitHub Actions will automatically build and publish to PyPI

## Getting Help

- Check existing issues and discussions
- Join our community discussions
- Create an issue for bugs or feature requests
- Ask questions in discussions

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to create a welcoming environment for all contributors.

## License

By contributing to PyPropTest, you agree that your contributions will be licensed under the BSD-3-Clause License.
