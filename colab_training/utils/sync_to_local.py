#!/usr/bin/env python3
"""Sync trained models from Colab to local Ollama instance."""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for model import."""
    name: str
    gguf_file: str
    system_prompt: str
    temperature: float = 0.3
    top_p: float = 0.9


AGENT_SYSTEM_PROMPTS = {
    'code': """You are an expert software engineer and coding assistant. 
You write clean, efficient, and well-documented code.
You follow best practices, design patterns, and write comprehensive tests.
Always explain your reasoning and consider edge cases.""",
    
    'security': """You are a cybersecurity expert and code auditor.
You identify security vulnerabilities, suggest fixes, and explain security best practices.
Focus on OWASP Top 10, secure coding patterns, and defense in depth.""",
    
    'ops': """You are a DevOps engineer and infrastructure expert.
You create Docker configurations, Kubernetes manifests, CI/CD pipelines, and Terraform code.
You follow infrastructure-as-code best practices and cloud-native patterns.""",
    
    'architect': """You are a senior system architect.
You design scalable systems, APIs, and database schemas.
You create comprehensive architecture diagrams and detailed technical specifications."""
}


def create_modelfile(config: ModelConfig, output_dir: Path) -> Path:
    """Create Ollama Modelfile."""
    modelfile_content = f"""FROM ./{config.gguf_file}

# Model parameters
PARAMETER temperature {config.temperature}
PARAMETER top_p {config.top_p}
PARAMETER top_k 40
PARAMETER num_ctx 4096

# Stop sequences (model-specific)
PARAMETER stop "<|endoftext|>"
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|eot_id|>"

# System prompt
SYSTEM {config.system_prompt}
"""
    
    modelfile_path = output_dir / "Modelfile"
    modelfile_path.write_text(modelfile_content)
    return modelfile_path


def import_to_ollama(model_name: str, modelfile_dir: Path) -> bool:
    """Import model to Ollama using Modelfile."""
    try:
        result = subprocess.run(
            ['ollama', 'create', model_name, '-f', 'Modelfile'],
            cwd=modelfile_dir,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Successfully imported model: {model_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to import model: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ Ollama not found. Please install Ollama first.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Sync trained model from Colab to local Ollama'
    )
    parser.add_argument(
        'gguf_file',
        help='Path to the GGUF file downloaded from Colab'
    )
    parser.add_argument(
        '--name', '-n',
        help='Model name in Ollama (default: auto-generated from filename)'
    )
    parser.add_argument(
        '--agent-type', '-a',
        choices=['code', 'security', 'ops', 'architect'],
        help='Agent type for system prompt selection'
    )
    parser.add_argument(
        '--system-prompt', '-s',
        help='Custom system prompt (overrides agent-type)'
    )
    parser.add_argument(
        '--temp', '-t',
        type=float,
        default=0.3,
        help='Temperature parameter (default: 0.3)'
    )
    parser.add_argument(
        '--keep-files', '-k',
        action='store_true',
        help='Keep temporary files after import'
    )
    
    args = parser.parse_args()
    
    # Validate GGUF file
    gguf_path = Path(args.gguf_file)
    if not gguf_path.exists():
        print(f"✗ File not found: {gguf_path}")
        return 1
    
    if not gguf_path.suffix == '.gguf':
        print(f"✗ Not a GGUF file: {gguf_path}")
        return 1
    
    # Determine model name
    model_name = args.name or f"lab-{gguf_path.stem.lower().replace('_', '-')}"
    
    # Determine system prompt
    if args.system_prompt:
        system_prompt = args.system_prompt
    elif args.agent_type:
        system_prompt = AGENT_SYSTEM_PROMPTS.get(args.agent_type, AGENT_SYSTEM_PROMPTS['code'])
    else:
        system_prompt = "You are a helpful AI assistant."
    
    # Create temporary directory for import
    import_dir = gguf_path.parent / f"import_{model_name}"
    import_dir.mkdir(exist_ok=True)
    
    # Copy GGUF file to import directory
    import_gguf = import_dir / gguf_path.name
    if not import_gguf.exists():
        import_gguf.write_bytes(gguf_path.read_bytes())
        print(f"✓ Copied GGUF file to {import_dir}")
    
    # Create ModelConfig
    config = ModelConfig(
        name=model_name,
        gguf_file=gguf_path.name,
        system_prompt=system_prompt,
        temperature=args.temp
    )
    
    # Create Modelfile
    modelfile_path = create_modelfile(config, import_dir)
    print(f"✓ Created Modelfile: {modelfile_path}")
    
    # Import to Ollama
    print(f"\nImporting to Ollama as '{model_name}'...")
    if import_to_ollama(model_name, import_dir):
        print(f"\n✓ Model '{model_name}' is ready!")
        print(f"\nTest it with:")
        print(f"  ollama run {model_name}")
        print(f"\nOr via the CLI:")
        print(f"  lab agent spawn {args.agent_type or 'code'} --model {model_name}")
    else:
        print("\n✗ Import failed. Check the error above.")
        return 1
    
    # Cleanup
    if not args.keep_files:
        import shutil
        shutil.rmtree(import_dir)
        print(f"\n✓ Cleaned up temporary files")
    else:
        print(f"\nℹ Temporary files kept in: {import_dir}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
