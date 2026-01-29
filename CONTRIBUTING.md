# Contributing to Mnemonic

Thank you for your interest in contributing to Mnemonic! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Running Tests](#running-tests)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We expect all contributors to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

Unacceptable behavior may result in removal from the project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- A virtual environment manager (recommended: `venv` or `uv`)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/bacharyehya/claude-memory-architecture.git
   cd claude-memory-architecture
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

   Or with `uv`:

   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Install with development dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

   Or with `uv`:

   ```bash
   uv pip install -e ".[dev]"
   ```

4. **Verify the installation**

   ```bash
   python -m mnemonic
   ```

### Project Structure

```
mnemonic-memory/
├── src/mnemonic/
│   ├── __init__.py      # Package init and main entry
│   ├── __main__.py      # CLI entry point
│   ├── config.py        # Configuration constants
│   ├── server.py        # FastMCP server definition
│   ├── core/
│   │   ├── memory.py    # CRUD operations
│   │   ├── search.py    # Search functionality
│   │   └── export.py    # Import/export operations
│   └── db/
│       ├── connection.py # Database connection management
│       └── schema.py     # SQLite schema definitions
├── pyproject.toml        # Project configuration
├── README.md
├── SPEC.md              # Architecture specification
└── LICENSE
```

## Code Style

We use **ruff** for linting and formatting. The project is configured with specific rules in `pyproject.toml`.

### Style Guidelines

1. **Line length**: Maximum 100 characters

2. **Type hints**: Required for all function signatures

   ```python
   # Good
   async def create_memory(
       title: str,
       content: str,
       tags: Optional[list[str]] = None,
   ) -> dict[str, Any]:
       ...

   # Bad
   async def create_memory(title, content, tags=None):
       ...
   ```

3. **Docstrings**: Required for all public functions and classes

   ```python
   async def get_memory(memory_id: str) -> Optional[dict[str, Any]]:
       """
       Get a memory by ID.

       Args:
           memory_id: The memory UUID

       Returns:
           Memory dictionary or None if not found
       """
       ...
   ```

4. **Imports**: Sorted by ruff (isort rules)
   - Standard library first
   - Third-party packages second
   - Local imports last

### Running Linters

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Pre-commit Checks

Before committing, ensure your code passes:

```bash
ruff check .
ruff format --check .
```

## Running Tests

We use **pytest** with **pytest-asyncio** for testing.

### Running the Test Suite

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_memory.py

# Run a specific test
pytest tests/test_memory.py::test_create_memory

# Run with coverage (if installed)
pytest --cov=mnemonic
```

### Writing Tests

1. Place tests in the `tests/` directory
2. Name test files with `test_` prefix
3. Name test functions with `test_` prefix
4. Use `pytest.mark.asyncio` for async tests

Example:

```python
import pytest
from mnemonic.core.memory import create_memory, get_memory

@pytest.mark.asyncio
async def test_create_memory():
    """Test that memories can be created with required fields."""
    memory = await create_memory(
        title="Test Memory",
        content="This is test content",
        tags=["test", "example"],
    )

    assert memory["title"] == "Test Memory"
    assert memory["content"] == "This is test content"
    assert "test" in memory["tags"]
    assert memory["id"] is not None
```

## Pull Request Process

### Before Submitting

1. **Create an issue first** (for significant changes)
2. **Fork the repository** and create a feature branch
3. **Write tests** for new functionality
4. **Update documentation** if needed
5. **Run linters and tests** locally

### Branch Naming

Use descriptive branch names:

- `feature/semantic-search` - New features
- `fix/memory-deletion-bug` - Bug fixes
- `docs/update-readme` - Documentation updates
- `refactor/db-connection` - Code refactoring

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add semantic search with embeddings
fix: Handle empty tag list in search
docs: Update installation instructions
refactor: Extract database connection logic
test: Add tests for memory export
```

Prefix conventions:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code change that neither fixes a bug nor adds a feature
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Submitting the PR

1. Push your branch to your fork
2. Open a Pull Request against `main`
3. Fill in the PR template with:
   - Description of changes
   - Related issue number
   - Testing performed
   - Screenshots (if applicable)
4. Request review from maintainers

### Review Process

- PRs require at least one approval before merging
- Address review feedback promptly
- Keep PRs focused and reasonably sized
- Squash commits if requested

## Issue Guidelines

### Bug Reports

When reporting bugs, include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Numbered steps to trigger the bug
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**: Python version, OS, package version
6. **Logs/Errors**: Any error messages or stack traces

Example:

```markdown
## Bug Description
Memory search returns empty results when using special characters.

## Steps to Reproduce
1. Create a memory with title "Test & Example"
2. Search for "Test & Example"
3. Observe empty results

## Expected Behavior
The memory should be found.

## Actual Behavior
Search returns empty array.

## Environment
- Python: 3.11.4
- OS: macOS 14.2
- mnemonic-memory: 0.1.0
```

### Feature Requests

When requesting features, include:

1. **Problem statement**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Alternatives considered**: Other approaches you've thought about
4. **Additional context**: Use cases, examples, mockups

### Questions

For questions about usage or implementation:

1. Check the [README](README.md) and [SPEC](SPEC.md) first
2. Search existing issues for similar questions
3. If still unclear, open an issue with the `question` label

---

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Be patient and respectful when awaiting responses

Thank you for contributing to Mnemonic!
