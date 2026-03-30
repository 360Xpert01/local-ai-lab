"""Model information and metadata structures."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ModelFamily(str, Enum):
    """Supported model families."""
    QWEN = "qwen"
    LLAMA = "llama"
    CODELLAMA = "codellama"
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"
    KIMI = "kimi"  # Future support
    CUSTOM = "custom"


class ModelCapability(str, Enum):
    """Model capabilities."""
    CODE = "code"
    CHAT = "chat"
    COMPLETION = "completion"
    REASONING = "reasoning"
    LONG_CONTEXT = "long_context"


class VRAMRequirements(BaseModel):
    """VRAM requirements for different environments."""
    colab_free_t4: bool = False
    colab_pro_t4: bool = False
    colab_pro_a100: bool = False
    local_8gb: bool = False
    local_16gb: bool = False
    local_24gb: bool = False


class FineTuningConfig(BaseModel):
    """Fine-tuning configuration for a model."""
    supported: bool = True
    trainer: str = "unsloth"  # unsloth, llama_factory, axolotl
    quantizations: List[str] = Field(default_factory=lambda: ["q4_k_m"])
    recommended_lora_r: int = 16
    recommended_lora_alpha: int = 16
    vram_requirements: VRAMRequirements = Field(default_factory=VRAMRequirements)


class ModelInfo(BaseModel):
    """Complete model information."""
    id: str
    name: str
    description: Optional[str] = None
    
    # Provider info
    provider: str = "ollama"
    ollama_name: str
    huggingface_id: Optional[str] = None
    
    # Model specs
    family: ModelFamily
    parameters: str  # e.g., "7B", "13B"
    context_length: int = 4096
    license: Optional[str] = None
    
    # Capabilities
    capabilities: List[ModelCapability] = Field(default_factory=list)
    
    # Fine-tuning
    fine_tuning: FineTuningConfig = Field(default_factory=FineTuningConfig)
    
    # Extra metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def supports_capability(self, capability: ModelCapability) -> bool:
        """Check if model supports a specific capability."""
        return capability in self.capabilities
    
    def is_fine_tunable(self) -> bool:
        """Check if model supports fine-tuning."""
        return self.fine_tuning.supported
    
    def get_quantization_options(self) -> List[str]:
        """Get available quantization options."""
        return self.fine_tuning.quantizations
