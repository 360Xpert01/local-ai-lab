"""Unit tests for training components."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestLocalTrainer:
    """Test cases for LocalTrainer."""
    
    @pytest.mark.unit
    def test_check_readiness_mps(self):
        """Test checking MPS availability."""
        from lab.training.local_trainer import LocalTrainer
        
        trainer = LocalTrainer()
        
        with patch('torch.backends.mps.is_available', return_value=True):
            with patch('torch.backends.mps.is_built', return_value=True):
                readiness = trainer.check_readiness()
        
        assert readiness.get('device', {}).get('has_mps') is True
        assert readiness.get('device', {}).get('has_cuda') is False
    
    @pytest.mark.unit
    def test_generate_training_script(self, temp_dir):
        """Test training script generation."""
        from lab.training.local_trainer import LocalTrainer, LocalTrainingConfig
        
        trainer = LocalTrainer()
        trainer.lab_dir = temp_dir
        
        config = LocalTrainingConfig(
            agent_type="code",
            model_id="Qwen/Qwen2.5-Coder-7B-Instruct",
            training_steps=10,
            batch_size=1,
            use_mlx=False
        )
        
        script_path = trainer.generate_training_script(config)
        
        assert script_path.exists()
        content = script_path.read_text()
        assert "Qwen/Qwen2.5-Coder-7B-Instruct" in content
        assert "TRAINING_STEPS = 10" in content
    
    @pytest.mark.unit
    def test_training_config_defaults(self):
        """Test training configuration defaults."""
        from lab.training.local_trainer import LocalTrainingConfig
        
        config = LocalTrainingConfig(
            agent_type="code",
            model_id="test-model"
        )
        
        assert config.training_steps == 100
        assert config.batch_size == 1
        assert config.learning_rate == 0.0002
        assert config.use_mlx is False


class TestColabAdapter:
    """Test cases for Colab training adapter."""
    
    @pytest.mark.unit
    def test_colab_adapter_creation(self):
        """Test Colab adapter initializes correctly."""
        from lab.training.colab_adapter import ColabAdapter
        
        adapter = ColabAdapter()
        
        assert adapter is not None
        assert hasattr(adapter, 'attempts')
        assert hasattr(adapter, 'check_colab_readiness')
    
    @pytest.mark.unit
    def test_check_colab_readiness(self):
        """Test Colab readiness check."""
        from lab.training.colab_adapter import ColabAdapter
        
        adapter = ColabAdapter()
        readiness = adapter.check_colab_readiness()
        
        assert 'can_proceed' in readiness
        assert 'todays_attempts' in readiness
        assert 'recommendations' in readiness
        assert isinstance(readiness['can_proceed'], bool)
    
    @pytest.mark.unit
    def test_suggest_alternatives(self):
        """Test alternative suggestions."""
        from lab.training.colab_adapter import ColabAdapter
        
        adapter = ColabAdapter()
        alternatives = adapter.suggest_alternatives()
        
        assert len(alternatives) > 0
        # Should mention local training
        assert any('local' in str(a).lower() for a in alternatives)
    
    @pytest.mark.unit
    def test_generate_colab_script(self, temp_dir):
        """Test Colab runner script generation."""
        from lab.training.colab_adapter import ColabAdapter
        
        adapter = ColabAdapter()
        
        notebook_path = temp_dir / "test.ipynb"
        notebook_path.write_text("{}")
        
        script_path = adapter.generate_colab_script(
            notebook_path=notebook_path,
            output_dir=temp_dir,
            use_fallbacks=True
        )
        
        assert script_path.exists()
        content = script_path.read_text()
        assert "Colab Training Runner" in content
        assert "check_gpu" in content


class TestTrainingData:
    """Test cases for training data handling."""
    
    @pytest.mark.unit
    def test_load_training_data(self):
        """Test loading training data from JSONL."""
        import json
        import tempfile
        
        data = [
            {"instruction": "Test 1", "input": "", "output": "Output 1"},
            {"instruction": "Test 2", "input": "", "output": "Output 2"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
            temp_path = f.name
        
        # Load and verify
        loaded = []
        with open(temp_path) as f:
            for line in f:
                loaded.append(json.loads(line))
        
        assert len(loaded) == 2
        assert loaded[0]["instruction"] == "Test 1"
        
        Path(temp_path).unlink()
    
    @pytest.mark.unit
    def test_training_data_format(self, sample_training_data):
        """Test training data format validation."""
        for item in sample_training_data:
            assert "instruction" in item
            assert "input" in item
            assert "output" in item
            assert isinstance(item["instruction"], str)
            assert isinstance(item["output"], str)
