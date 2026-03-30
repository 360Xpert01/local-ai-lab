# 🎯 Local AI Lab - Cheat Sheet

Quick commands for common tasks.

## Setup

```bash
# One-command setup
./scripts/quickstart.sh

# Manual setup
cd cli && pip install -e .
lab setup
ollama pull qwen2.5-coder:7b
```

## Training

### Local Training (Fully Automated)
```bash
# Quick training
lab train local --agent code --steps 100

# With notification
lab train local --agent code --steps 100 --background --notify

# Specific framework
lab train local --agent code --base-model llama3.1:8b

# Monitor
lab train status
watch -n 5 cat ~/.lab/local_training/progress_code.json

# Import after training
lab train import ~/.lab/local_training/model.gguf --agent-type code
```

### Google Colab (Manual)
```bash
# Generate notebook
lab train start --agent code --steps 100

# Manual steps:
# 1. Open https://colab.research.google.com
# 2. Upload notebook from ~/.lab/training_jobs/
# 3. Upload training_data.jsonl
# 4. Runtime → GPU → Run all
# 5. Download .gguf file
# 6. Import:
lab train import ~/Downloads/unsloth.Q4_K_M.gguf --agent-type code
```

## Using Agents

### Single Agent
```bash
# Spawn agent
lab agent spawn code
lab agent spawn code --model qwen2.5-coder:7b

# Interactive chat
lab chat --agent code
lab chat --agent security

# With task
lab agent spawn code --task "Review this function"
```

### Multi-Agent
```bash
# Parallel execution
lab multi spawn \
  --agents "code,security,ops" \
  --task "Build API" \
  --parallel

# Pipeline execution
lab multi spawn \
  --agents "architect,code,security" \
  --task "Design and implement" \
  --pipeline

# Demo scenarios
lab multi demo --scenario feature-dev
lab multi demo --scenario security-audit
lab multi demo --scenario infra-setup
```

## File Operations

```bash
# List files
lab file list
lab file list src/ --recursive

# Read file
lab file read src/main.py

# Create file
lab file create src/new.py --content "print('hello')"

# Edit with AI
lab file edit src/main.py \
  --agent code \
  --prompt "Add error handling"

# Delete file
lab file delete src/old.py
```

## Model Management

```bash
# List models
lab model list
lab model list --fine-tunable

# Get info
lab model info qwen2.5-coder-7b-instruct

# Pull model
lab model pull llama3.1:8b
lab model pull codellama:7b

# Add custom
lab model add \
  --name "My Model" \
  --ollama-name "custom:7b" \
  --hf-id "org/model"
```

## Web UI

```bash
# Start API server
lab server

# Start Web UI (new terminal)
cd web-ui && npm run dev

# Access
open http://localhost:3000
```

## Docker

```bash
# Start all services
cd docker && docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f

# Stop
docker-compose down
```

## Monitoring

```bash
# Job status
lab train status              # List all
lab train status <job_id>     # Specific job
lab train stop <job_id>       # Stop job

# System status
lab status
ollama list
ps aux | grep lab
```

## Training Data

```bash
# Use all examples
cat colab_training/training_data/code/*.jsonl > training_data.jsonl

# Use specific framework
cat colab_training/training_data/code/nestjs.jsonl > training_data.jsonl
cat colab_training/training_data/code/django.jsonl > training_data.jsonl
cat colab_training/training_data/code/symfony.jsonl > training_data.jsonl

# Combine frameworks
cat colab_training/training_data/code/{nestjs,django}.jsonl > training_data.jsonl
```

## Common Workflows

### 1. Quick Code Help
```bash
lab chat --agent code
> How do I write a Python decorator?
```

### 2. Multi-Agent Code Review
```bash
lab multi spawn \
  --agents "code,security" \
  --task "Review src/auth.py for bugs and security issues" \
  --parallel
```

### 3. Train & Deploy Custom Agent
```bash
# Train
lab train local --agent code --steps 100 --background --notify

# Wait for notification...

# Import
lab train import model.gguf --agent-type code --name my-agent

# Use
lab agent spawn code --model my-agent
```

### 4. Framework-Specific Training
```bash
# Prepare Symfony data
cat colab_training/training_data/code/php_symfony.jsonl > training_data.jsonl

# Train
lab train local --agent code --steps 100

# Use for PHP projects
lab chat --agent code
> Create a Symfony controller for user management
```

## Troubleshooting

```bash
# CLI not found
pip install -e ./cli

# Ollama not running
ollama serve &

# Training OOM
lab train local --agent code --batch-size 1

# Colab issues
# Use local training instead:
lab train local --agent code

# Web UI issues
cd web-ui && npm install && npm run dev
```

## File Locations

```
~/.lab/                          # Config & data
├── config/
│   ├── models/registry.yaml    # Model definitions
│   └── agents/*.yaml           # Agent configs
├── training_jobs/              # Generated notebooks
└── local_training/             # Local training output

./colab_training/
├── training_data/              # Training examples
│   ├── code/                   # 35 examples
│   ├── security/               # 5 examples
│   ├── ops/                    # 5 examples
│   └── architecture/           # 3 examples
└── templates/                  # Notebook templates
```

## Keyboard Shortcuts

### CLI
- `Tab` - Auto-complete
- `↑/↓` - Command history
- `Ctrl+C` - Cancel operation

### Web UI
- ``Ctrl+` `` - Toggle terminal fullscreen
- `Ctrl+N` - New session
- `Ctrl+R` - Refresh

---

**Quick Links:**
- Full Guide: `USAGE_GUIDE.md`
- Training Guide: `FINETUNING_GUIDE.md`
- Quick Start: `./scripts/quickstart.sh`
