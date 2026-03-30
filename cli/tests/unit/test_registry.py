"""Unit tests for model registry."""

import pytest
from unittest.mock import patch, mock_open
from pathlib import Path


class TestModelRegistry:
    """Test cases for ModelRegistry."""
    
    def test_get_model_existing(self, mock_registry):
        """Test retrieving an existing model."""
        model = mock_registry.get_model("test-model")
        
        assert model is not None
        assert model.id == "test-model"
        assert model.name == "Test Model"
    
    def test_get_model_nonexistent(self, mock_registry):
        """Test retrieving a non-existent model."""
        mock_registry.get_model.return_value = None
        
        model = mock_registry.get_model("nonexistent")
        assert model is None
    
    def test_list_models(self, mock_registry):
        """Test listing all models."""
        models = mock_registry.list_models()
        
        assert len(models) == 1
        assert models[0].id == "test-model"
    
    def test_model_capabilities(self, mock_registry):
        """Test model capability checking."""
        from lab.core.model_info import ModelCapability
        
        model = mock_registry.get_model("test-model")
        
        assert ModelCapability.CODE in model.capabilities
        assert ModelCapability.CHAT in model.capabilities
    
    def test_model_fine_tunable(self, mock_registry):
        """Test fine-tunability check."""
        model = mock_registry.get_model("test-model")
        
        # Mock the fine_tuning config
        model.fine_tuning.trainer = "unsloth"
        model.fine_tuning.quantizations = ["q4_k_m", "q5_k_m"]
        
        assert model.is_fine_tunable() is True


class TestModelInfo:
    """Test cases for ModelInfo dataclass."""
    
    def test_model_info_creation(self):
        """Test creating ModelInfo instance."""
        from lab.core.model_info import ModelInfo, ModelFamily, ModelCapability
        
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="ollama",
            ollama_name="test:latest",
            family=ModelFamily.QWEN,
            parameters="7B",
            context_length=32768,
            capabilities=[ModelCapability.CODE]
        )
        
        assert model.id == "test-model"
        assert model.parameters == "7B"
        assert model.context_length == 32768
    
    def test_model_info_validation(self):
        """Test model info validation."""
        from lab.core.model_info import ModelInfo, ModelFamily
        
        # Valid model family
        model = ModelInfo(
            id="test",
            name="Test",
            provider="ollama",
            ollama_name="test:latest",
            family=ModelFamily.LLAMA,
            parameters="8B",
            context_length=8192,
            capabilities=[]
        )
        assert model.family == ModelFamily.LLAMA
