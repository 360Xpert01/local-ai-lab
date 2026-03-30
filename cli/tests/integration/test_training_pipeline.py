"""Integration tests for training pipeline."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock


class TestTrainingPipeline:
    """Integration tests for the full training workflow."""
    
    @pytest.mark.integration
    def test_script_generation_to_execution(self, temp_dir):
        """Test training script generation and validation."""
        from lab.training.local_trainer import LocalTrainer, LocalTrainingConfig
        
        trainer = LocalTrainer()
        trainer.lab_dir = temp_dir
        
        config = LocalTrainingConfig(
            agent_type="code",
            model_id="Qwen/Qwen2.5-Coder-7B-Instruct",
            training_steps=3,
            batch_size=1,
            use_mlx=False
        )
        
        # Generate script
        script_path = trainer.generate_training_script(config)
        
        # Verify script is syntactically valid Python
        import ast
        try:
            ast.parse(script_path.read_text())
            valid_syntax = True
        except SyntaxError:
            valid_syntax = False
        
        assert valid_syntax, "Generated script has syntax errors"
    
    @pytest.mark.integration
    def test_end_to_end_notebook_generation(self, temp_dir):
        """Test complete notebook generation workflow."""
        from lab.commands.train import generate_training_notebook
        import json
        
        # Create mock configs
        model_info = Mock()
        model_info.id = "qwen2.5-coder-7b-instruct"
        model_info.name = "Qwen 2.5 Coder"
        model_info.huggingface_id = "Qwen/Qwen2.5-Coder-7B-Instruct"
        model_info.family.value = "qwen"
        model_info.parameters = "7B"
        model_info.is_fine_tunable.return_value = True
        model_info.fine_tuning.trainer = "unsloth"
        model_info.fine_tuning.quantizations = ["q4_k_m"]
        model_info.fine_tuning.recommended_lora_r = 16
        
        agent_config = Mock()
        agent_config.name = "Code Assistant"
        agent_config.slug = "code-assistant"
        agent_config.training.datasets = ["code/alpaca"]
        agent_config.training.hyperparameters = {
            "lora_r": 16,
            "max_seq_length": 2048,
            "learning_rate": 2e-4
        }
        
        # Generate notebook
        notebook_path = generate_training_notebook(
            agent_config=agent_config,
            model_info=model_info,
            steps=100,
            output_name="test_notebook"
        )
        
        # Move to temp dir for cleanup
        final_path = temp_dir / "test_notebook.ipynb"
        notebook_path.rename(final_path)
        
        # Verify file was created
        assert final_path.exists()
        
        # Reload and verify structure
        with open(final_path) as f:
            loaded = json.load(f)
        
        assert loaded["metadata"]["language_info"]["name"] == "python"
        assert len(loaded["cells"]) > 2
    
    @pytest.mark.integration
    def test_model_registry_integration(self):
        """Test model registry with training configuration."""
        from lab.core.registry import ModelRegistry
        from lab.core.model_info import ModelInfo, ModelFamily, ModelCapability
        
        # Create a temporary registry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_dir = Path(tmpdir)
            registry = ModelRegistry(registry_dir)
            
            # Add a test model
            model = ModelInfo(
                id="test-integration-model",
                name="Test Integration Model",
                provider="ollama",
                ollama_name="test:latest",
                huggingface_id="test/model",
                family=ModelFamily.QWEN,
                parameters="7B",
                context_length=32768,
                capabilities=[ModelCapability.CODE]
            )
            
            registry.add_model(model)
            
            # Verify retrieval
            retrieved = registry.get_model("test-integration-model")
            assert retrieved is not None
            assert retrieved.huggingface_id == "test/model"
            
            # Verify it's fine-tunable
            assert retrieved.is_fine_tunable() is True


class TestAgentTrainingIntegration:
    """Integration tests for agent-specific training."""
    
    @pytest.mark.integration
    def test_agent_model_compatibility(self, mock_agent_config):
        """Test agent can use compatible models."""
        from lab.core.agent_config import AgentConfig
        
        # Check model compatibility
        compatible = mock_agent_config.is_model_compatible("qwen2.5-coder-7b-instruct")
        assert compatible is True
    
    @pytest.mark.integration
    def test_training_data_for_agent(self):
        """Test training data selection for different agents."""
        # Different agents should have different training data
        agent_datasets = {
            "code": ["code/alpaca", "code/frameworks"],
            "security": ["security/audits"],
            "ops": ["ops/docker", "ops/terraform"],
            "architect": ["architecture/design"]
        }
        
        for agent, datasets in agent_datasets.items():
            assert len(datasets) > 0
            assert all(isinstance(d, str) for d in datasets)
