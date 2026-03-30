# Local AI Lab

A dynamic, model-agnostic local AI development environment with multi-agent support, fine-tuning pipelines, and hybrid CLI + Web UI.

## Features

- **Dynamic Model Registry**: Add new models via YAML config, no code changes
- **Multi-Agent System**: Code, Security, DevOps, and Architecture agents
- **Hybrid Interface**: CLI-first with Web UI cockpit
- **Fine-tuning Pipeline**: Local (MLX/MPS/CPU) or Colab training
- **48+ Training Examples**: PHP/Symfony, Python/Django, NestJS, FeatherJS
- **Model Agnostic**: Works with Qwen, Llama, CodeLlama, and future models
- **Background Training**: Run training with notifications when complete

## 🚀 Quick Start (3 Commands)

```bash
# 1. Run setup (installs everything)
./scripts/quickstart.sh

# 2. Start training (local, fully automated)
lab train local --agent code --steps 100 --background --notify

# 3. Use your trained agent
lab chat --agent code
```

Or start the Web UI:
```bash
lab server              # Terminal 1: API server
cd web-ui && npm run dev  # Terminal 2: Web UI
open http://localhost:3000
```

## CLI Usage

```bash
# List available models
lab model list

# Spawn an agent
lab agent spawn code --model qwen2.5-coder-7b-instruct

# Chat with agent
lab chat --agent code

# Fine-tune a model
lab train start --agent code --base-model llama-3.1-8b-instruct
```

## Project Structure

```
local-ai-lab/
├── cli/                 # Python CLI core
├── agents/              # Agent services (Rust, Go, Node)
├── web-ui/              # Next.js dashboard
├── colab_training/      # Training notebooks
└── docker/              # Docker compose files
```

## Requirements

- Mac M2 Pro with 32GB RAM (or similar)
- Python 3.11+
- Node.js 20+
- Go 1.21+
- Rust 1.75+
- Ollama
- Docker Desktop

## License

MIT

## ⚠️ Dependency Notes

### If you have dependency conflicts

If you see errors about `transformers`, `tokenizers`, or `torch` versions:

```bash
# Option 1: Use the fix script
./scripts/fix_dependencies.sh

# Option 2: Use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows
pip install -e ./cli

# Option 3: Use conda
conda create -n lab python=3.11
conda activate lab
pip install -e ./cli
```

### For Local Training

Local training requires additional packages. Install only when needed:

```bash
# Install training dependencies
pip install torch==2.1.0 transformers==4.44.2

# Then install unsloth
pip install "unsloth[cu121-torch240] @ git+https://github.com/unslothai/unsloth.git"
```

Or use Colab (no local dependencies needed):

```bash
# Just generate notebook - training happens on Colab
lab train start --agent code --steps 100
```
