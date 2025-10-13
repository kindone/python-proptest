# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in PyPropTest, please report it responsibly:

### How to Report

1. **Do not** create a public GitHub issue for security vulnerabilities
2. Email the maintainers at: [INSERT SECURITY EMAIL]
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- We will acknowledge receipt of your report within 48 hours
- We will provide regular updates on our progress
- We will work with you to understand and resolve the issue
- We will credit you in our security advisories (unless you prefer to remain anonymous)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 1 week
- **Resolution**: Within 30 days (depending on complexity)

## Security Best Practices

When using PyPropTest:

1. **Keep dependencies updated**: Regularly update PyPropTest and its dependencies
2. **Use specific versions**: Pin to specific versions in production
3. **Review generated data**: Be cautious with generated data in security-sensitive contexts
4. **Validate inputs**: Always validate inputs from property-based tests before using in production

## Security Considerations

### Property-Based Testing Security

Property-based testing generates random data, which can include:

- **Sensitive data**: Generated strings might contain sensitive information
- **Large inputs**: Generators might produce very large data structures
- **Special characters**: String generators might produce control characters or Unicode

### Recommendations

1. **Sanitize generated data**: Don't use generated data directly in security-sensitive operations
2. **Limit input size**: Use appropriate generator constraints (min_length, max_length, etc.)
3. **Filter sensitive patterns**: Use `.filter()` to exclude sensitive patterns
4. **Test in isolation**: Run property-based tests in isolated environments

### Example: Safe String Generation

```python
from pyproptest import for_all, Gen

# Safe: Generate only printable ASCII characters
safe_string_gen = Gen.str().filter(
    lambda s: s.isprintable() and s.isascii()
)

# Safe: Limit string length
limited_string_gen = Gen.str(min_length=1, max_length=100)

@for_all(safe_string_gen)
def test_safe_operation(s: str):
    # Safe to use 's' in your test
    assert len(s) > 0
```

## Security Tools

We use several tools to maintain security:

- **Bandit**: Static analysis for common security issues
- **Safety**: Check for known security vulnerabilities in dependencies
- **Dependabot**: Automatic dependency updates
- **Code scanning**: GitHub's automated security scanning

## Disclosure Policy

- We follow responsible disclosure practices
- Security vulnerabilities will be disclosed after fixes are available
- We will provide advance notice to users before public disclosure
- Security advisories will be published on GitHub and PyPI

## Contact

For security-related questions or concerns, please contact:

- **Security Email**: [INSERT SECURITY EMAIL]
- **GitHub Security Advisories**: Use GitHub's private vulnerability reporting feature

Thank you for helping keep PyPropTest secure!
