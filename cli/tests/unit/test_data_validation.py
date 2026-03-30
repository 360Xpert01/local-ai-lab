"""Tests for training data validation."""

import pytest
import json
from pathlib import Path


class TestTrainingDataValidation:
    """Validate training data format and quality."""
    
    @pytest.mark.unit
    def test_training_data_jsonl_exists(self):
        """Check training data file exists."""
        # Look for training data in various locations
        possible_paths = [
            Path("training_data.jsonl"),
            Path("../training_data.jsonl"),
            Path("../../training_data.jsonl"),
        ]
        
        found = any(p.exists() for p in possible_paths)
        
        # This is a soft check - data might not be committed
        if found:
            print("Training data file found!")
        else:
            pytest.skip("Training data file not found (may need to be generated)")
    
    @pytest.mark.unit
    def test_training_data_format(self, tmp_path):
        """Test training data format is valid JSONL."""
        # Create sample training data
        sample_data = [
            {
                "instruction": "Write a function",
                "input": "",
                "output": "def func(): pass"
            }
        ]
        
        # Write to temp file
        data_file = tmp_path / "test_data.jsonl"
        with open(data_file, 'w') as f:
            for item in sample_data:
                f.write(json.dumps(item) + '\n')
        
        # Read and validate
        loaded = []
        with open(data_file) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    item = json.loads(line)
                    loaded.append(item)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON on line {line_num}: {e}")
        
        assert len(loaded) == 1
        assert "instruction" in loaded[0]
    
    @pytest.mark.unit
    def test_alpaca_format_validation(self):
        """Test Alpaca format compliance."""
        # Valid Alpaca format
        valid_item = {
            "instruction": "Write a Python function",
            "input": "def example():",
            "output": "def example():\n    pass"
        }
        
        # Check required fields
        required_fields = ["instruction", "input", "output"]
        for field in required_fields:
            assert field in valid_item, f"Missing required field: {field}"
            assert isinstance(valid_item[field], str), f"Field {field} must be a string"
    
    @pytest.mark.unit
    def test_sharegpt_format_validation(self):
        """Test ShareGPT format compliance."""
        # Valid ShareGPT format
        valid_item = {
            "conversations": [
                {"from": "human", "value": "Write a function"},
                {"from": "gpt", "value": "def func(): pass"}
            ]
        }
        
        assert "conversations" in valid_item
        assert isinstance(valid_item["conversations"], list)
        assert len(valid_item["conversations"]) >= 1
        
        for conv in valid_item["conversations"]:
            assert "from" in conv
            assert "value" in conv
            assert conv["from"] in ["human", "gpt", "system"]
    
    @pytest.mark.unit
    def test_data_quality_checks(self):
        """Test data quality metrics."""
        test_item = {
            "instruction": "Write a function",
            "input": "",
            "output": "def example():\n    return 42"
        }
        
        # Check instruction is not empty
        assert test_item["instruction"].strip(), "Instruction should not be empty"
        
        # Check output is not empty
        assert test_item["output"].strip(), "Output should not be empty"
        
        # Check reasonable length
        assert len(test_item["instruction"]) < 1000, "Instruction too long"
        assert len(test_item["output"]) < 10000, "Output too long"
    
    @pytest.mark.unit
    def test_framework_specific_examples(self):
        """Test framework-specific training examples."""
        frameworks = {
            "nestjs": {
                "instruction": "Create a NestJS controller",
                "keywords": ["@Controller", "@Get", "@Module"]
            },
            "django": {
                "instruction": "Create a Django view",
                "keywords": ["def", "request", "HttpResponse"]
            },
            "react": {
                "instruction": "Create a React component",
                "keywords": ["function", "return", "export"]
            }
        }
        
        # Verify framework detection logic
        for framework, config in frameworks.items():
            instruction = config["instruction"].lower()
            assert framework.lower() in instruction or any(
                kw.lower() in instruction for kw in config["keywords"]
            ), f"Could not identify {framework} example"


class TestModelCompatibility:
    """Test model compatibility with training."""
    
    @pytest.mark.unit
    def test_model_has_required_fields(self):
        """Test model info has all required fields for training."""
        from lab.core.model_info import ModelInfo, ModelFamily
        
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="ollama",
            ollama_name="test-model:latest",
            family=ModelFamily.QWEN,
            parameters="7B",
            context_length=32768,
            capabilities=[]
        )
        
        # Check required fields exist
        assert model.id
        assert model.name
        assert model.family
        assert model.parameters
        assert model.context_length > 0
    
    @pytest.mark.unit
    def test_fine_tuning_config(self):
        """Test fine-tuning configuration validation."""
        from lab.core.model_info import FineTuningConfig
        
        config = FineTuningConfig(
            supported=True,
            trainer="unsloth",
            quantizations=["q4_k_m", "q5_k_m"],
            recommended_lora_r=16
        )
        
        assert config.supported is True
        assert config.trainer in ["unsloth", "trl", "mlx"]
        assert len(config.quantizations) > 0
        assert 4 <= config.recommended_lora_r <= 128
