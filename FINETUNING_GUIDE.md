# 🎓 Fine-tuning Guide

Complete guide for fine-tuning models with Local AI Lab - including background training, local execution, and Colab fallbacks.

## Table of Contents

- [Quick Start](#quick-start)
- [Training Methods](#training-methods)
  - [Background Training (Recommended)](#background-training)
  - [Local Training on Mac](#local-training)
  - [Google Colab](#google-colab)
- [Handling Colab Blocks](#handling-colab-blocks)
- [Monitoring Training](#monitoring-training)
- [Best Practices](#best-practices)

## Quick Start

```bash
# ⭐ RECOMMENDED: Local training (fully automated, no manual steps)
lab train local --agent code --steps 100 --background --notify

# Check status anytime
lab train status
```

> ⚠️ **Important:** Google Colab requires **manual upload** (no public API). The system generates a notebook, but you must upload it to Colab yourself. Use **local training** for fully automated execution!

## Training Methods Comparison

| Method | Automation | Speed | Setup | Best For |
|--------|-----------|-------|-------|----------|
| **Local (MLX)** | ✅ Fully Automated | ⚡ Fastest | None | ⭐ **Recommended** |
| **Local (MPS)** | ✅ Fully Automated | 🚀 Fast | None | Daily use |
| **Background** | ✅ Auto-notification | Varies | None | Multi-tasking |
| **Google Colab** | ❌ Manual upload | Fast (T4) | Web upload | No local GPU |

## Training Methods

### Background Training

Run training in the background and get notified when complete:

```bash
# Start background training
lab train start --agent code \
  --base-model qwen2.5-coder-7b-instruct \
  --steps 100 \
  --background \
  --notify

# Output:
# ✓ Background job started: train_code_1704067200
# PID: 12345
# Monitor with: lab train status train_code_1704067200

# Check status anytime
lab train status                    # List all jobs
lab train status train_code_1234    # Specific job

# Stop a running job
lab train stop train_code_1234
```

**Features:**
- Runs in background (no terminal blocking)
- macOS notification when complete
- Progress tracking
- Can stop/resume

### Local Training

Train directly on your Mac M2 Pro without Colab:

```bash
# Check if your Mac is ready
lab train local --agent code --dry-run

# Start local training
lab train local --agent code \
  --steps 100 \
  --batch-size 1 \
  --background \
  --notify

# Use Apple MLX (fastest on M2)
lab train local --agent code --use-mlx

# CPU only (slowest but works everywhere)
lab train local --agent code --use-cpu
```

**Performance on Mac M2 Pro:**

| Method | Speed | Memory | Best For |
|--------|-------|--------|----------|
| MLX | ⚡ Fastest | ~8GB | Production training |
| MPS (Metal) | 🚀 Fast | ~10GB | Standard training |
| CPU | 🐢 Slow | ~6GB | Fallback/testing |

**Estimated Times (100 steps):**
- MLX: ~5-8 minutes
- MPS: ~10-15 minutes  
- CPU: ~30-45 minutes

### Google Colab (Manual Upload)

⚠️ **Colab requires manual steps** - there is no public API for automation.

The system generates a notebook, but you must manually upload and run it:

```bash
# Generate notebook for Colab
lab train start --agent code --steps 100

# Output shows:
# ✓ Notebook generated: ~/.lab/training_jobs/train_code_qwen.ipynb
# 
# === GOOGLE COLAB TRAINING - MANUAL UPLOAD REQUIRED ===
# 1. Open Colab:  https://colab.research.google.com
# 2. Upload:      Click 'Upload' → Select the notebook
# 3. Upload Data: Upload training_data.jsonl in Files panel
# 4. Set GPU:     Runtime → Change runtime → GPU
# 5. Run:         Runtime → Run all (Ctrl+F9)
```

**Why manual?** Google Colab doesn't provide a public API for:
- Automated notebook execution
- File uploads  
- Runtime management

This prevents abuse of free resources. For **fully automated** training, use [Local Training](#local-training) instead.

## Handling Colab Blocks

When Colab free tier blocks you, the system automatically detects and suggests alternatives:

```bash
$ lab train start --agent code

⚠️ You've had 2 failed Colab attempts today
⚠️ Colab rate limit likely

Recommendations:
  ⏳ Rate limited recently. Wait ~45 minutes or use local training.
  
  🔄 Alternatives:
     1. Use local training: lab train local --agent code
     2. Try Kaggle Notebooks (30h GPU/week free)
     3. Runpod.io (cheap GPU rental ~$0.20/hour)
     4. Lambda Labs ($0.50/hour for A10 GPU)

Would you like to train locally instead? [Y/n]: 
```

### Automatic Fallbacks

When running in Colab, the generated script includes automatic fallbacks:

1. **Try 1**: Full GPU training with Unsloth
2. **Try 2**: Reduced batch size if OOM
3. **Try 3**: Smaller sequence length
4. **Try 4**: CPU training (guaranteed to complete)

### Alternative Platforms

#### Kaggle Notebooks (Free - 30h GPU/week)

```bash
# Generate notebook same as Colab
lab train start --agent code

# Upload .ipynb to Kaggle
# Select "GPU" as accelerator
# Run training
```

#### RunPod.io (Paid - ~$0.20/hour)

```bash
# Rent GPU and run local training script
lab train local --agent code --steps 1000
```

#### Lambda Labs (Paid - ~$0.50/hour)

- $30 free credit for new users
- Upload notebook via Jupyter
- A10 GPU instances available

## Monitoring Training

### Background Jobs

```bash
# List all jobs
$ lab train status

┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID                  ┃ Agent   ┃ Model                       ┃ Status    ┃ Progress ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ train_code_abc123   │ code    │ qwen2.5-coder-7b-instruct   │ running   │ 45/100   │
│ train_sec_def456    │ security│ llama-3.1-8b-instruct       │ completed │ 100/100  │
│ train_ops_ghi789    │ ops     │ qwen2.5-coder-7b-instruct   │ failed    │ 20/100   │
└─────────────────────┴─────────┴─────────────────────────────┴───────────┴──────────┘

# Detailed status
$ lab train status train_code_abc123

Job ID: train_code_abc123
Agent: code
Model: qwen2.5-coder-7b-instruct
Status: [blue]RUNNING[/blue]
Started: 2024-01-15T10:30:00

Progress: 45/100 (45.0%)
Loss: 1.2345
```

### Local Training Progress

Local training saves progress to:
```
~/.lab/local_training/progress_<agent>.json
```

Monitor with:
```bash
# Watch progress
watch -n 5 cat ~/.lab/local_training/progress_code.json

# Or use the CLI
lab train status
```

### Notifications

When using `--notify`, you'll get:

**macOS:**
- Native notification when training completes
- Sound alert (Glass sound)
- Shows final loss and duration

**Linux:**
- notify-send notification
- Falls back to console output

**Background Jobs:**
```bash
# Start with notification
lab train start --agent code --background --notify

# You'll get a notification like:
# ✅ Training Complete: code
# Model qwen2.5-coder-7b-instruct finished training.
# Steps: 100
# Final loss: 0.5234
```

## Best Practices

### 1. Start Small

```bash
# Test with 50 steps first
lab train local --agent code --steps 50

# If successful, scale up
lab train local --agent code --steps 200 --background --notify
```

### 2. Use Quality Data

```bash
# Check your training data
cat colab_training/training_data/code/alpaca_code.jsonl | wc -l

# Add your own examples
echo '{"instruction":"Your task","input":"","output":"Your solution"}' >> \
  colab_training/training_data/code/custom.jsonl
```

### 3. Monitor Resource Usage

```bash
# On Mac, watch memory usage during training
watch -n 2 "ps aux | grep python | head -5"

# Check available memory
vm_stat | grep "Pages free"

# Check disk space
df -h ~
```

### 4. Save Checkpoints

The generated notebooks automatically save checkpoints every 10 steps. If Colab disconnects:

1. Reconnect runtime
2. Re-run cells from the beginning
3. Training resumes from last checkpoint

### 5. Use Appropriate Models

| Your Goal | Recommended Model | VRAM | Colab Free? |
|-----------|-------------------|------|-------------|
| Coding | qwen2.5-coder-7b | 6GB | ✅ Yes |
| General | llama-3.1-8b | 6GB | ✅ Yes |
| Code specific | codellama-7b | 6GB | ✅ Yes |
| Long context | llama-3.1-8b | 6GB | ✅ Yes |
| 13B models | Any 13B Q4 | 10GB | ⚠️ May OOM |

### 6. Troubleshooting

#### Out of Memory

```bash
# Reduce batch size
lab train local --agent code --batch-size 1

# Use smaller model
lab train start --agent code --base-model qwen2.5-coder-7b-instruct
```

#### Colab Keeps Disconnecting

```bash
# Use background mode which handles disconnects
lab train start --agent code --background

# Or train locally
lab train local --agent code
```

#### Training Too Slow

```bash
# Use MLX on Mac (fastest)
lab train local --agent code --use-mlx

# Reduce steps for testing
lab train local --agent code --steps 50
```

## Complete Workflow Example

```bash
# 1. Prepare data
cat > colab_training/training_data/code/my_examples.jsonl << 'EOF'
{"instruction":"Write Python to parse JSON","input":"","output":"import json\n\ndata = json.loads('{\"key\": \"value\"}')"}
EOF

# 2. Start background training
lab train local --agent code \
  --steps 100 \
  --background \
  --notify

# 3. Wait for notification (or check status)
lab train status

# 4. Import trained model
lab train import \
  ~/.lab/local_training/code_model/unsloth.Q4_K_M.gguf \
  --agent-type code \
  --name my-code-assistant

# 5. Use the model
lab agent spawn code --model my-code-assistant
```

## Advanced Options

### Custom Training Script

```bash
# Generate script without running
lab train local --agent code --steps 100 --dry-run

# Edit the generated script
vim ~/.lab/local_training/local_train_code_*.py

# Run manually
python ~/.lab/local_training/local_train_code_*.py
```

### Multiple Concurrent Trainings

```bash
# Train multiple agents simultaneously
lab train local --agent code --steps 100 --background &
lab train local --agent security --steps 100 --background &
lab train local --agent ops --steps 100 --background &

# Monitor all
watch -n 5 lab train status
```

### Resume Interrupted Training

If training is interrupted:

```bash
# Check what completed
ls -la ~/.lab/local_training/

# Re-run with same settings to continue
lab train local --agent code --steps 100
```

## Getting Help

```bash
# Command help
lab train --help
lab train start --help
lab train local --help

# Check system readiness
lab train local --agent code --dry-run
```

---

**Happy Fine-tuning! 🚀**
