"""Dynamic model registry with YAML configuration."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .model_info import ModelInfo, ModelCapability, ModelFamily


DEFAULT_REGISTRY = {
    "meta": {
        "version": "1.0",
        "description": "Local AI Lab Model Registry"
    },
    "models": {
        "qwen2.5-coder-7b-instruct": {
            "name": "Qwen2.5 Coder 7B Instruct",
            "description": "Alibaba's Qwen2.5 Coder optimized for code generation",
            "provider": "ollama",
            "ollama_name": "qwen2.5-coder:7b",
            "huggingface_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "family": "qwen",
            "parameters": "7B",
            "context_length": 32768,
            "license": "apache-2.0",
            "capabilities": ["code", "chat", "completion"],
            "fine_tuning": {
                "supported": True,
                "trainer": "unsloth",
                "quantizations": ["q4_k_m", "q5_k_m", "q8_0", "f16"],
                "recommended_lora_r": 16,
                "vram_requirements": {
                    "colab_free_t4": True,
                    "local_16gb": True
                }
            }
        },
        "llama-3.1-8b-instruct": {
            "name": "Llama 3.1 8B Instruct",
            "description": "Meta's Llama 3.1 with 128K context",
            "provider": "ollama",
            "ollama_name": "llama3.1:8b",
            "huggingface_id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "family": "llama",
            "parameters": "8B",
            "context_length": 128000,
            "license": "llama3.1",
            "capabilities": ["code", "chat", "reasoning", "long_context"],
            "fine_tuning": {
                "supported": True,
                "trainer": "unsloth",
                "quantizations": ["q4_k_m", "q5_k_m"],
                "recommended_lora_r": 16,
                "vram_requirements": {
                    "colab_free_t4": True,
                    "local_16gb": True
                }
            }
        },
        "codellama-7b-instruct": {
            "name": "CodeLlama 7B Instruct",
            "description": "Meta's CodeLlama optimized for code",
            "provider": "ollama",
            "ollama_name": "codellama:7b",
            "huggingface_id": "codellama/CodeLlama-7b-Instruct-hf",
            "family": "codellama",
            "parameters": "7B",
            "context_length": 16384,
            "license": "llama2",
            "capabilities": ["code", "chat", "completion"],
            "fine_tuning": {
                "supported": True,
                "trainer": "unsloth",
                "quantizations": ["q4_k_m", "q5_k_m"],
                "recommended_lora_r": 16,
                "vram_requirements": {
                    "colab_free_t4": True,
                    "local_16gb": True
                }
            }
        },
        "deepseek-coder-6.7b-instruct": {
            "name": "DeepSeek Coder 6.7B Instruct",
            "description": "DeepSeek Coder with strong performance",
            "provider": "ollama",
            "ollama_name": "deepseek-coder:6.7b",
            "huggingface_id": "deepseek-ai/deepseek-coder-6.7b-instruct",
            "family": "deepseek",
            "parameters": "6.7B",
            "context_length": 16384,
            "license": "deepseek",
            "capabilities": ["code", "chat", "completion"],
            "fine_tuning": {
                "supported": True,
                "trainer": "unsloth",
                "quantizations": ["q4_k_m", "q5_k_m"],
                "recommended_lora_r": 16,
                "vram_requirements": {
                    "colab_free_t4": True,
                    "local_16gb": True
                }
            }
        }
    }
}


class ModelRegistry:
    """Dynamic model registry loaded from YAML."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".lab" / "config"
        self.registry_file = self.config_dir / "models" / "registry.yaml"
        self._models: Dict[str, ModelInfo] = {}
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load model registry from YAML or create default."""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                data = yaml.safe_load(f)
        else:
            data = DEFAULT_REGISTRY
            self._save_default_registry()
        
        # Parse models
        for model_id, model_data in data.get("models", {}).items():
            self._models[model_id] = ModelInfo(id=model_id, **model_data)
    
    def _save_default_registry(self) -> None:
        """Save default registry to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        models_dir = self.config_dir / "models"
        models_dir.mkdir(exist_ok=True)
        
        with open(self.registry_file, 'w') as f:
            yaml.dump(DEFAULT_REGISTRY, f, default_flow_style=False, sort_keys=False)
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model by ID."""
        return self._models.get(model_id)
    
    def list_models(
        self,
        capability: Optional[ModelCapability] = None,
        fine_tunable_only: bool = False,
        family: Optional[ModelFamily] = None
    ) -> List[ModelInfo]:
        """List models with optional filtering."""
        models = list(self._models.values())
        
        if capability:
            models = [m for m in models if m.supports_capability(capability)]
        
        if fine_tunable_only:
            models = [m for m in models if m.is_fine_tunable()]
        
        if family:
            models = [m for m in models if m.family == family]
        
        return models
    
    def add_model(self, model_info: ModelInfo) -> None:
        """Add a new model to the registry."""
        self._models[model_info.id] = model_info
        self._save_registry()
    
    def _save_registry(self) -> None:
        """Save current registry to disk."""
        data = {
            "meta": {"version": "1.0", "description": "Local AI Lab Model Registry"},
            "models": {}
        }
        
        for model_id, model in self._models.items():
            data["models"][model_id] = model.model_dump(exclude={'id'})
        
        with open(self.registry_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def get_compatible_models(
        self,
        capabilities: List[ModelCapability],
        require_fine_tunable: bool = False
    ) -> List[ModelInfo]:
        """Get models compatible with required capabilities."""
        models = self._models.values()
        
        if require_fine_tunable:
            models = [m for m in models if m.is_fine_tunable()]
        
        # Model must support ALL required capabilities
        compatible = []
        for model in models:
            if all(model.supports_capability(cap) for cap in capabilities):
                compatible.append(model)
        
        return compatible


# Global registry instance
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """Get global registry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
