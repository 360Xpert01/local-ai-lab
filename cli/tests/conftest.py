"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_registry():
    """Create a mock model registry."""
    from lab.core.model_info import ModelInfo, ModelFamily, ModelCapability
    
    registry = Mock()
    
    # Create a sample model
    model = ModelInfo(
        id="test-model",
        name="Test Model",
        provider="ollama",
        ollama_name="test-model:latest",
        huggingface_id="test/model",
        family=ModelFamily.QWEN,
        parameters="7B",
        context_length=32768,
        capabilities=[ModelCapability.CODE, ModelCapability.CHAT]
    )
    
    registry.get_model.return_value = model
    registry.list_models.return_value = [model]
    
    return registry


@pytest.fixture
def mock_agent_config():
    """Create a mock agent configuration."""
    from lab.core.agent_config import AgentConfig, ModelSelectionConfig
    
    config = Mock(spec=AgentConfig)
    config.slug = "code-assistant"
    config.name = "Code Assistant"
    config.description = "A code generation agent"
    
    # Setup model config as a proper object
    model_config = Mock(spec=ModelSelectionConfig)
    model_config.default = "qwen2.5-coder-7b-instruct"
    model_config.allow_user_override = True
    config.model = model_config
    
    config.get_default_model.return_value = Mock(id="qwen2.5-coder-7b-instruct", name="Qwen 2.5 Coder")
    config.get_compatible_models.return_value = [Mock(id="qwen2.5-coder-7b-instruct")]
    config.is_model_compatible.return_value = True
    config.tools = ["file_reader", "code_writer"]
    
    return config


@pytest.fixture
def sample_training_data():
    """Provide sample training data."""
    return [
        {
            "instruction": "Write a Python function to reverse a string",
            "input": "",
            "output": "def reverse_string(s):\n    return s[::-1]"
        },
        {
            "instruction": "Create a FastAPI endpoint",
            "input": "",
            "output": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/hello')\ndef hello():\n    return {'message': 'Hello World'}"
        }
    ]


@pytest.fixture
def mock_ollama_response():
    """Mock response from Ollama API."""
    return {
        "model": "qwen2.5-coder:7b",
        "created_at": "2024-01-01T00:00:00Z",
        "response": "def hello():\n    print('Hello World')",
        "done": True
    }
