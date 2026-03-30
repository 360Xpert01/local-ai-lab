"""Optional imports with graceful fallbacks."""

try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False
    FastLanguageModel = None

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

def check_training_dependencies():
    """Check if training dependencies are available."""
    missing = []
    
    if not TORCH_AVAILABLE:
        missing.append("torch")
    
    if not UNSLOTH_AVAILABLE:
        missing.append("unsloth")
    
    return missing
