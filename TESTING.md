# Testing Guide for Local AI Lab

This guide explains how to test the Local AI Lab application comprehensively.

## Quick Start

```bash
cd local-ai-lab/cli

# Run all tests
python tests/run_tests.py

# Or use pytest directly
pytest tests/

# Run specific test types
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/e2e/          # End-to-end tests only
```

## Test Structure

```
cli/tests/
├── conftest.py              # Shared fixtures
├── run_tests.py             # Test runner script
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_registry.py     # Model registry tests
│   └── test_training.py     # Training component tests
├── integration/             # Integration tests (medium speed)
│   └── test_training_pipeline.py
└── e2e/                     # End-to-end tests (slower)
    └── test_cli_workflows.py
```

## Test Categories

### 1. Unit Tests (`pytest -m unit`)

Fast tests for individual components. No external dependencies.

```bash
# Run unit tests
pytest tests/unit/ -v

# Examples:
pytest tests/unit/test_registry.py::TestModelRegistry::test_get_model_existing -v
```

**What they test:**
- Model registry operations
- Training configuration validation
- Script generation
- Data format validation

### 2. Integration Tests (`pytest -m integration`)

Tests for component interactions. May use temporary files.

```bash
# Run integration tests
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ --cov=lab
```

**What they test:**
- Training script generation → file output
- Registry → Model info retrieval
- Agent config → Training data mapping

### 3. End-to-End Tests (`pytest -m e2e`)

Full workflow tests. May be slow.

```bash
# Run E2E tests
pytest tests/e2e/ -v

# Skip slow tests
pytest tests/ -m "not slow"
```

**What they test:**
- CLI command execution
- Full training workflow setup
- Multi-agent session creation

## Running Tests

### Basic Commands

```bash
# All tests
pytest

# With verbose output
pytest -v

# Stop on first failure
pytest -x

# Specific test file
pytest tests/unit/test_registry.py

# Specific test
pytest tests/unit/test_registry.py::TestModelRegistry::test_get_model_existing
```

### With Markers

```bash
# Only unit tests
pytest -m unit

# Exclude slow tests
pytest -m "not slow"

# Only integration and e2e
pytest -m "integration or e2e"

# Tests requiring Ollama
pytest -m requires_ollama
```

### With Coverage

```bash
# Install coverage
pip install pytest-cov

# Run with coverage report
pytest --cov=lab --cov-report=term-missing

# Generate HTML report
pytest --cov=lab --cov-report=html
# Open htmlcov/index.html
```

## Writing New Tests

### Unit Test Example

```python
# tests/unit/test_my_feature.py
import pytest
from lab.core.my_module import MyClass

class TestMyFeature:
    @pytest.mark.unit
    def test_basic_functionality(self):
        """Test the basic feature works."""
        obj = MyClass()
        result = obj.do_something()
        assert result == expected_value
    
    @pytest.mark.unit
    def test_edge_case(self):
        """Test edge case handling."""
        obj = MyClass()
        with pytest.raises(ValueError):
            obj.do_something(invalid_input)
```

### Integration Test Example

```python
# tests/integration/test_workflow.py
import pytest

class TestWorkflow:
    @pytest.mark.integration
    def test_full_workflow(self, temp_dir):
        """Test complete workflow with temporary directory."""
        # Setup
        config = create_config(temp_dir)
        
        # Execute
        result = run_workflow(config)
        
        # Verify
        assert result.output_file.exists()
```

### E2E Test Example

```python
# tests/e2e/test_cli.py
import pytest
import subprocess

class TestCLI:
    @pytest.mark.e2e
    def test_command_runs(self):
        """Test CLI command executes successfully."""
        result = subprocess.run(
            ["lab", "status"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
```

## Available Fixtures

The following fixtures are available in `conftest.py`:

### `temp_dir`
Creates a temporary directory that's cleaned up after the test.

```python
def test_with_temp_dir(temp_dir):
    file_path = temp_dir / "test.txt"
    file_path.write_text("content")
    assert file_path.exists()
```

### `mock_registry`
Provides a mock model registry.

```python
def test_with_mock_registry(mock_registry):
    model = mock_registry.get_model("test-model")
    assert model.id == "test-model"
```

### `mock_agent_config`
Provides a mock agent configuration.

```python
def test_with_mock_agent(mock_agent_config):
    assert mock_agent_config.slug == "code-assistant"
```

### `sample_training_data`
Provides sample training data.

```python
def test_with_sample_data(sample_training_data):
    assert len(sample_training_data) == 2
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          cd cli
          pip install -e ".[dev]"
      
      - name: Run unit tests
        run: |
          cd cli
          pytest tests/unit/ -v
      
      - name: Run integration tests
        run: |
          cd cli
          pytest tests/integration/ -v
```

## Troubleshooting

### Tests Not Found

```bash
# Make sure you're in the right directory
cd local-ai-lab/cli

# Check pytest can find tests
pytest --collect-only
```

### Import Errors

```bash
# Install the package in development mode
cd local-ai-lab/cli
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/cli"
```

### Slow Tests

```bash
# Skip slow tests
pytest -m "not slow"

# Run with timeout
pip install pytest-timeout
pytest --timeout=60
```

## Best Practices

1. **Use markers**: Tag tests with `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.e2e`

2. **Use fixtures**: Leverage existing fixtures for common setup

3. **Clean up**: Always clean up resources, use `temp_dir` fixture

4. **Isolate tests**: Tests should not depend on each other

5. **Descriptive names**: Use descriptive test names that explain what's being tested

6. **Arrange-Act-Assert**: Structure tests clearly:
   ```python
   def test_example():
       # Arrange
       obj = create_object()
       
       # Act
       result = obj.do_something()
       
       # Assert
       assert result == expected
   ```

## Test Coverage Goals

- **Unit tests**: 80%+ coverage for core modules
- **Integration tests**: Cover all major workflows
- **E2E tests**: Cover critical user paths

Run coverage report:
```bash
pytest --cov=lab --cov-report=term-missing
```
