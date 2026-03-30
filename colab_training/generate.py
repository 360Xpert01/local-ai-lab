#!/usr/bin/env python3
"""Generate Colab training notebooks from templates."""

import json
import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def generate_notebook(
    agent_type: str,
    model_id: str,
    output_dir: Path = None
) -> Path:
    """Generate a fine-tuning notebook for specific agent and model."""
    
    # Load model and agent info
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'cli'))
    
    from lab.core.registry import get_registry
    from lab.core.agent_config import get_agent_registry
    
    registry = get_registry()
    agent_registry = get_agent_registry()
    
    model = registry.get_model(model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")
    
    agent = agent_registry.get_agent(f"{agent_type}-assistant") or \
            agent_registry.get_agent(f"{agent_type}-expert") or \
            agent_registry.get_agent(agent_type)
    
    if not agent:
        raise ValueError(f"Agent {agent_type} not found")
    
    # Load template
    template_dir = Path(__file__).parent / 'templates'
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('unsloth_base.ipynb.j2')
    
    # Prepare context
    context = {
        'model': {
            'name': model.name,
            'id': model.id,
            'family': model.family.value,
            'parameters': model.parameters,
            'huggingface_id': model.huggingface_id,
        },
        'agent': {
            'name': agent.name,
            'slug': agent.slug,
        },
        'training': {
            'lora_r': agent.training.hyperparameters.get('lora_r', 16),
            'lora_alpha': agent.training.hyperparameters.get('lora_alpha', 16),
            'max_steps': agent.training.hyperparameters.get('max_steps', 100),
            'learning_rate': agent.training.hyperparameters.get('learning_rate', 2e-4),
        },
        'test_instruction': get_test_instruction(agent_type),
        'test_input': '',
    }
    
    # Render notebook
    notebook_json = template.render(**context)
    notebook = json.loads(notebook_json)
    
    # Save
    if output_dir is None:
        output_dir = Path(__file__).parent / 'generated'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"train_{agent_type}_{model.family.value}.ipynb"
    
    with open(output_file, 'w') as f:
        json.dump(notebook, f, indent=2)
    
    return output_file


def get_test_instruction(agent_type: str) -> str:
    """Get a test instruction appropriate for the agent type."""
    instructions = {
        'code': 'Write a Python function to implement binary search',
        'security': 'Review this code for SQL injection: "SELECT * FROM users WHERE id = \'+user_id+\'"',
        'ops': 'Create a Dockerfile for a Node.js application',
        'architect': 'Design a URL shortener service with high availability',
    }
    return instructions.get(agent_type, 'Write a function to reverse a string')


def main():
    parser = argparse.ArgumentParser(description='Generate Colab training notebooks')
    parser.add_argument('--agent', '-a', required=True, help='Agent type (code, security, ops, architect)')
    parser.add_argument('--model', '-m', required=True, help='Model ID (e.g., qwen2.5-coder-7b-instruct)')
    parser.add_argument('--output', '-o', help='Output directory', default=None)
    
    args = parser.parse_args()
    
    output_dir = Path(args.output) if args.output else None
    
    try:
        output_file = generate_notebook(args.agent, args.model, output_dir)
        print(f"✓ Generated notebook: {output_file}")
        print(f"\nTo use:")
        print(f"1. Upload {output_file} to Google Colab")
        print(f"2. Upload your training_data.jsonl file")
        print(f"3. Run all cells")
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
