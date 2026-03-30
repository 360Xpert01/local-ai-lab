# 📖 Local AI Lab - Complete Usage Guide

Step-by-step instructions for setting up, training, and using your Local AI Lab.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Starting the System](#starting-the-system)
3. [Training Models](#training-models)
4. [Using Agents](#using-agents)
5. [Web UI](#web-ui)
6. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### Step 1: Install Dependencies

```bash
# Navigate to project
cd local-ai-lab

# Install CLI and dependencies
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This will:
- Install Python CLI (`lab` command)
- Install Node.js dependencies for Web UI
- Initialize model and agent registries
- Install Go and Rust dependencies (if available)

### Step 2: Verify Installation

```bash
# Check CLI is installed
lab --version

# Check system status
lab status

# List available models
lab model list

# List available agents
lab agent list
```

Expected output:
```
✓ CLI installed: 0.1.0
✓ Model registry initialized at ~/.lab/config/models/
✓ Agent configs initialized at ~/.lab/config/agents/
Available Models: 4 (Qwen, Llama, CodeLlama, DeepSeek)
Available Agents: 4 (code, security, ops, architect)
```

### Step 3: Pull Base Model

```bash
# Pull Qwen 2.5 Coder (recommended for coding)
lab model pull qwen2.5-coder-7b-instruct

# Or pull Llama 3.1 (better for general tasks)
lab model pull llama-3.1-8b-instruct
```

This downloads the model via Ollama. First time may take 5-10 minutes.

### Step 4: Verify Ollama

```bash
# Check Ollama is running
ollama list

# Test the model
ollama run qwen2.5-coder:7b

# Exit with Ctrl+D
```

---

## Starting the System

### Option A: Quick Start (Local Only)

```bash
# Just use CLI - no services needed
lab agent spawn code
```

### Option B: Full Stack (CLI + Web UI + Agents)

```bash
# Terminal 1: Start API Server
lab server

# Terminal 2: Start Web UI
cd web-ui && npm run dev

# Terminal 3: Start Agent Services (optional)
# Security Agent (Rust)
cd agents/security-agent && cargo run

# Ops Agent (Go)
cd agents/ops-agent && go run cmd/server/main.go

# Architect Agent (Node)
cd agents/architect-agent && npm start
```

### Option C: Docker (Everything at Once)

```bash
# Build and start all services
cd docker
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

Services started:
- API Server: http://localhost:8000
- Web UI: http://localhost:3000
- Security Agent: http://localhost:8081
- Ops Agent: http://localhost:8082
- Architect Agent: http://localhost:8083
- Redis: localhost:6379

---

## Training Models

### Method 1: Local Training (Recommended - Fully Automated)

```bash
# Step 1: Prepare training data (combine examples)
cat colab_training/training_data/code/*.jsonl > training_data.jsonl

# Step 2: Start training in background with notification
lab train local \
  --agent code \
  --steps 100 \
  --background \
  --notify

# Step 3: Check status (optional)
lab train status

# Step 4: Wait for notification (macOS/Linux)
# Or monitor progress:
watch -n 5 cat ~/.lab/local_training/progress_code.json
```

Expected output:
```
✓ Started with PID: 12345
Monitor with: ps aux | grep 12345
Progress file: ~/.lab/local_training/progress_code.json

Training takes ~10-15 minutes on M2 Pro
You'll get a notification when complete!
```

After completion:
```bash
# Import the trained model
lab train import \
  ~/.lab/local_training/code_model/unsloth.Q4_K_M.gguf \
  --agent-type code \
  --name my-code-agent

# Use it!
lab agent spawn code --model my-code-agent
```

### Method 2: Google Colab (Manual Upload)

```bash
# Step 1: Generate notebook
lab train start \
  --agent code \
  --base-model qwen2.5-coder-7b-instruct \
  --steps 100

# Output shows:
# ✓ Notebook generated: ~/.lab/training_jobs/train_code_qwen.ipynb
```

Manual steps:
1. Open https://colab.research.google.com
2. Click "Upload" tab
3. Select: `~/.lab/training_jobs/train_code_qwen.ipynb`
4. Upload your `training_data.jsonl` file (drag to Files panel)
5. Runtime → Change runtime type → GPU
6. Runtime → Run all (Ctrl+F9)
7. Wait 10-30 minutes
8. Download the `.gguf` file when prompted
9. Import:
```bash
lab train import ~/Downloads/unsloth.Q4_K_M.gguf --agent-type code
```

### Method 3: Background Training with Auto-Notification

```bash
# Start background training
lab train local \
  --agent security \
  --steps 150 \
  --background \
  --notify

# Continue working - you'll get a notification when done!

# Check any time:
lab train status

# View specific job:
lab train status train_security_1704067200

# Stop if needed:
lab train stop train_security_1704067200
```

### Training on Specific Frameworks

```bash
# Symfony/PHP only
cat colab_training/training_data/code/php_symfony.jsonl > training_data.jsonl
lab train local --agent code --steps 100

# Django only
cat colab_training/training_data/code/django.jsonl > training_data.jsonl
lab train local --agent code --steps 100

# NestJS only
cat colab_training/training_data/code/nestjs.jsonl > training_data.jsonl
lab train local --agent code --steps 100

# All frameworks
cat colab_training/training_data/code/*.jsonl > training_data.jsonl
lab train local --agent code --steps 200
```

---

## Using Agents

### Single Agent Mode

```bash
# Spawn a code agent
lab agent spawn code

# Spawn with specific model
lab agent spawn code --model qwen2.5-coder:7b

# Spawn with task
lab agent spawn code --task "Review this Python code for bugs"

# Interactive chat
lab chat --agent code

# Type your requests, /quit to exit
```

### Multi-Agent Mode (Parallel Execution)

```bash
# Spawn multiple agents in parallel
lab multi spawn \
  --agents "code,security,architect" \
  --task "Design and implement a secure API" \
  --parallel

# Pipeline mode (sequential)
lab multi spawn \
  --agents "architect,code,security" \
  --task "Build new feature" \
  --pipeline

# Quick demo scenarios
lab multi demo --scenario feature-dev
lab multi demo --scenario security-audit
lab multi demo --scenario infra-setup
```

### File Operations

```bash
# List files
lab file list

# Read file
lab file read src/config.py

# Create file
lab file create src/new_module.py --content "def hello(): pass"

# Edit with AI
lab file edit src/main.py \
  --agent code \
  --prompt "Add error handling to the main function"
```

### Working with Models

```bash
# List models
lab model list

# Pull new model
lab model pull llama3.1:8b

# Get model info
lab model info llama-3.1-8b-instruct

# Add custom model
lab model add \
  --name "Kimi Coder 7B" \
  --ollama-name "kimi/coder:7b" \
  --hf-id "kimi/coder-7b" \
  --family kimi
```

---

## Web UI

### Access the Dashboard

```bash
# Start the Web UI
cd web-ui
npm run dev

# Open browser
open http://localhost:3000
```

### Features

1. **Model Selector** (Top right)
   - Switch between available models
   - View model capabilities
   - Filter by fine-tunability

2. **Session Manager** (Left panel)
   - Create multi-agent sessions
   - Quick demo scenarios
   - View active sessions

3. **Terminal Widget** (Center)
   - Full terminal in browser
   - Run `lab` commands
   - Command history

4. **Agent Monitor** (Right panel)
   - Real-time agent status
   - Activity logs
   - Spawn/kill agents

### Web UI Shortcuts

```
Ctrl+` : Toggle terminal fullscreen
Ctrl+N : New session
Ctrl+R : Refresh agent status
```

---

## Complete Workflow Examples

### Example 1: Train and Use Custom Code Agent

```bash
# 1. Prepare training data with Symfony examples
cat colab_training/training_data/code/php_symfony.jsonl > training_data.jsonl

# 2. Train locally
lab train local \
  --agent code \
  --steps 100 \
  --background \
  --notify

# 3. Wait for notification...

# 4. Import model
lab train import \
  ~/.lab/local_training/code_model/unsloth.Q4_K_M.gguf \
  --agent-type code \
  --name symfony-expert

# 5. Use it
lab agent spawn code --model symfony-expert

# 6. Chat
lab chat --agent code
> Create a Symfony controller with JWT auth
```

### Example 2: Multi-Agent Feature Development

```bash
# Start multi-agent session
lab multi spawn \
  --name "New API Feature" \
  --agents "architect,code,security,ops" \
  --task "Design and implement a user authentication API with Docker deployment" \
  --pipeline

# Watch progress
lab multi status

# Agents work in sequence:
# 1. Architect designs the API
# 2. Code agent implements it
# 3. Security agent audits it
# 4. Ops agent creates Docker config
```

### Example 3: Background Training with Monitoring

```bash
# Terminal 1: Start training
lab train local \
  --agent security \
  --steps 200 \
  --background \
  --notify

# Terminal 2: Monitor
watch -n 10 lab train status

# Terminal 3: Continue working
lab agent spawn code --task "Review my code"

# Wait for notification when training completes!
```

---

## Command Reference

### Model Commands

```bash
lab model list                    # List all models
lab model list --fine-tunable    # Only fine-tunable
lab model info <id>              # Model details
lab model pull <id>              # Download model
lab model add ...                # Add new model
```

### Agent Commands

```bash
lab agent list                   # List agents
lab agent spawn <type>           # Spawn agent
lab agent create <name>          # Create custom agent
lab agent info <type>            # Agent details
```

### Training Commands

```bash
# Local training
lab train local --agent <type> --steps <n>

# Colab notebook generation
lab train start --agent <type> --steps <n>

# Import trained model
lab train import <file> --agent-type <type>

# Job management
lab train status                 # List jobs
lab train status <id>           # Job details
lab train stop <id>             # Stop job
```

### Multi-Agent Commands

```bash
lab multi spawn --agents "a,b" --task "..."
lab multi status                 # Session status
lab multi list                   # List sessions
lab multi demo --scenario <name> # Run demo
```

### File Commands

```bash
lab file list [path]
lab file read <path>
lab file create <path>
lab file edit <path> --agent <type>
lab file delete <path>
```

### Chat Commands

```bash
lab chat --agent <type>
lab chat --multi-agent
```

---

## Troubleshooting

### Issue: "lab command not found"

```bash
# Reinstall CLI
cd cli
pip install -e .

# Verify
which lab
lab --version
```

### Issue: "Ollama not running"

```bash
# Start Ollama
ollama serve &

# Or install
brew install ollama
```

### Issue: Training fails with OOM

```bash
# Reduce batch size
lab train local --agent code --steps 100

# Use smaller model
lab train local --agent code --base-model qwen2.5-coder-7b-instruct

# Use CPU only
lab train local --agent code --use-cpu
```

### Issue: Colab disconnects

```bash
# Use local training instead
lab train local --agent code --background --notify

# Or try Kaggle
# (See FINETUNING_GUIDE.md for Kaggle instructions)
```

### Issue: Web UI won't load

```bash
# Check API server is running
curl http://localhost:8000/api/health

# Restart Web UI
cd web-ui
npm run dev

# Check for errors
npm run build 2>&1 | head -20
```

### Issue: Background job not notifying

```bash
# Check job status
lab train status

# Check notification permissions (macOS)
# System Preferences → Notifications → Terminal

# Manual check
cat ~/.lab/local_training/progress_code.json
```

---

## Quick Reference Card

```bash
# SETUP
./scripts/setup.sh
lab model pull qwen2.5-coder-7b-instruct

# START
lab server                    # API
# (new terminal) cd web-ui && npm run dev

# TRAIN (Choose one)
lab train local --agent code --steps 100 --background --notify
# OR
lab train start --agent code  # Then upload to Colab

# USE
lab agent spawn code
lab chat --agent code

# MULTI-AGENT
lab multi demo --scenario feature-dev
```

---

## Next Steps

1. **Read the fine-tuning guide**: `FINETUNING_GUIDE.md`
2. **Explore training data**: `colab_training/training_data/`
3. **Try framework examples**: `colab_training/training_data/code/FRAMEWORKS.md`
4. **Customize agents**: Edit `~/.lab/config/agents/*.yaml`
5. **Add your own models**: Edit `~/.lab/config/models/registry.yaml`

Happy coding! 🚀
