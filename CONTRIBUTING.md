# Contributing to ML Fitness Tools

Thank you for your interest in contributing to ML Fitness Tools! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Initial Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ml-fitness-tools.git
   cd ml-fitness-tools
   ```

3. Install development dependencies:
   ```bash
   make install-dev
   # or
   pip install -r requirements-dev.txt
   pre-commit install
   ```

## Development Workflow

### Before You Start

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. Make sure tests pass:
   ```bash
   make test
   ```

### Making Changes

1. **Write your code** following the existing style
2. **Add tests** for new functionality
3. **Update documentation** if needed
4. **Run checks locally**:
   ```bash
   make ci  # Runs all CI checks
   ```

### Code Quality Standards

We use several tools to maintain code quality:

- **Black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **Ruff**: Fast Python linter
- **Bandit**: Security linting
- **pytest**: Testing

Run them individually:
```bash
make format    # Auto-format code
make lint      # Check code quality
make security  # Security checks
make test      # Run tests
```

### Commit Guidelines

We use pre-commit hooks that automatically run before each commit:

- Code formatting (Black, isort)
- Linting (Ruff)
- Security checks (Bandit)
- Tests (pytest)

If pre-commit hooks fail, fix the issues and commit again.

**Commit message format:**
```
Type: Brief description (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.

- Bullet points for multiple changes
- Reference issues with #issue-number
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

**Examples:**
```
feat: Add recovery prediction endpoint

fix: Correct RPE calculation for high intensity
```

## Submitting a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub:
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template

3. **PR Requirements:**
   - All CI checks must pass
   - At least 80% code coverage for new code
   - Tests demonstrate the change works
   - Documentation updated if needed
   - No merge conflicts with main

### CI/CD Checks

When you submit a PR, GitHub Actions automatically runs:

1. **Tests** (Python 3.10, 3.11, 3.12)
2. **Code Quality Checks** (Ruff, Black, isort)
3. **Security Scanning** (Bandit, Safety)
4. **API Validation** (Syntax check, startup test)

All checks must pass before merging.

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names

**Example:**
```python
def test_rpe_calculation_with_high_intensity():
    """Test that RPE calculation works correctly at high intensity"""
    result = calculate_rpe_metrics(weight=100, reps=5, rpe=9.5)
    assert result["estimated_1rm"] < 105
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::TestRPEEndpoint::test_valid_rpe_request -v
```

## Project Structure

```
ml-fitness-tools/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline
├── tests/                       # Test files
├── standalone/                  # Standalone tool versions
├── recovery_api.py              # Main API server
├── training_data.json           # Sample training data
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml              # Tool configuration
├── .pre-commit-config.yaml     # Pre-commit hooks
├── Makefile                    # Development commands
└── README.md                   # Main documentation
```

## Need Help?

- **Questions?** Open an issue with the "question" label
- **Bug reports?** Open an issue with the "bug" label
- **Feature requests?** Open an issue with the "enhancement" label

## Code of Conduct

- Be respectful and constructive
- Focus on what is best for the community
- Show empathy towards other contributors

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ML Fitness Tools! 💪🤖
