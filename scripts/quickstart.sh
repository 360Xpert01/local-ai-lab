#!/bin/bash
# Local AI Lab - Quick Start Script
# This script automates the initial setup and first training

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Local AI Lab - Quick Start                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "cli" ]; then
    echo -e "${RED}✗ Error: Please run this script from the local-ai-lab directory${NC}"
    exit 1
fi

PROJECT_DIR=$(pwd)

echo -e "${YELLOW}Step 1: Installing CLI and dependencies...${NC}"
echo "=========================================================="

# Install CLI
cd "$PROJECT_DIR/cli"
if pip install -e . > /dev/null 2>&1; then
    echo -e "${GREEN}✓ CLI installed${NC}"
else
    echo -e "${RED}✗ Failed to install CLI${NC}"
    echo "Make sure Python 3.11+ is installed"
    exit 1
fi

# Initialize registries
echo -e "${YELLOW}Initializing registries...${NC}"
python3 -c "from lab.core.registry import get_registry; get_registry()" > /dev/null 2>&1
python3 -c "from lab.core.agent_config import get_agent_registry; get_agent_registry()" > /dev/null 2>&1
echo -e "${GREEN}✓ Registries initialized${NC}"

echo ""
echo -e "${YELLOW}Step 2: Checking Ollama...${NC}"
echo "=========================================================="

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama installed${NC}"
    
    # Check if running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is running${NC}"
    else
        echo -e "${YELLOW}! Starting Ollama...${NC}"
        ollama serve &
        sleep 3
    fi
else
    echo -e "${YELLOW}! Ollama not found. Please install from https://ollama.ai${NC}"
    echo "Then run: ollama serve"
fi

echo ""
echo -e "${YELLOW}Step 3: Pulling base model (this may take 5-10 minutes)...${NC}"
echo "=========================================================="

MODEL="qwen2.5-coder:7b"

if ollama list | grep -q "$MODEL"; then
    echo -e "${GREEN}✓ Model $MODEL already available${NC}"
else
    echo "Pulling $MODEL..."
    ollama pull $MODEL
    echo -e "${GREEN}✓ Model pulled successfully${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Preparing training data...${NC}"
echo "=========================================================="

# Combine training data
cd "$PROJECT_DIR"
if cat colab_training/training_data/code/*.jsonl > training_data.jsonl 2>/dev/null; then
    COUNT=$(grep -c '"instruction"' training_data.jsonl)
    echo -e "${GREEN}✓ Training data prepared: $COUNT examples${NC}"
else
    echo -e "${YELLOW}! Using default training data${NC}"
fi

echo ""
echo -e "${YELLOW}Step 5: Testing installation...${NC}"
echo "=========================================================="

# Test CLI
echo "Testing CLI..."
lab --version > /dev/null 2>&1 && echo -e "${GREEN}✓ CLI working${NC}" || echo -e "${RED}✗ CLI test failed${NC}"

# Test model
lab model list > /dev/null 2>&1 && echo -e "${GREEN}✓ Model registry working${NC}" || echo -e "${RED}✗ Model registry failed${NC}"

# Test agents
lab agent list > /dev/null 2>&1 && echo -e "${GREEN}✓ Agent registry working${NC}" || echo -e "${RED}✗ Agent registry failed${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Setup Complete! 🎉                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}QUICK START OPTIONS:${NC}"
echo ""
echo "1️⃣  START TRAINING (Recommended):"
echo ""
echo "    # Train locally (fully automated):"
echo "    lab train local --agent code --steps 100 --background --notify"
echo ""
echo "    # Or generate Colab notebook:"
echo "    lab train start --agent code --steps 100"
echo ""
echo "2️⃣  START USING AGENTS:"
echo ""
echo "    # Chat with code agent:"
echo "    lab chat --agent code"
echo ""
echo "    # Multi-agent demo:"
echo "    lab multi demo --scenario feature-dev"
echo ""
echo "3️⃣  START WEB UI:"
echo ""
echo "    # Terminal 1: Start API"
echo "    lab server"
echo ""
echo "    # Terminal 2: Start Web UI"
echo "    cd web-ui && npm run dev"
echo ""
echo "    # Then open: http://localhost:3000"
echo ""
echo "4️⃣  VIEW DOCUMENTATION:"
echo ""
echo "    cat USAGE_GUIDE.md"
echo "    cat FINETUNING_GUIDE.md"
echo ""

# Save a quick reference file
cat > QUICKSTART.txt << 'EOF'
╔════════════════════════════════════════════════════════════╗
║              Local AI Lab - Quick Reference                ║
╚════════════════════════════════════════════════════════════╝

TRAIN LOCALLY (Fully Automated):
────────────────────────────────
lab train local --agent code --steps 100 --background --notify

TRAIN ON COLAB (Manual Upload):
───────────────────────────────
lab train start --agent code --steps 100
# Then upload to https://colab.research.google.com

USE AGENTS:
───────────
lab agent spawn code
lab chat --agent code
lab multi demo --scenario feature-dev

START WEB UI:
─────────────
lab server
cd web-ui && npm run dev
open http://localhost:3000

MANAGE MODELS:
──────────────
lab model list
lab model pull qwen2.5-coder-7b-instruct
lab agent spawn code --model qwen2.5-coder:7b

MONITOR TRAINING:
─────────────────
lab train status
lab train status <job_id>
watch -n 5 cat ~/.lab/local_training/progress_code.json

HELP:
─────
lab --help
lab train --help
lab agent --help
cat USAGE_GUIDE.md
EOF

echo -e "${GREEN}✓ Quick reference saved to: QUICKSTART.txt${NC}"
echo ""
echo -e "${BLUE}Happy coding! 🚀${NC}"
echo ""

# Offer to start training immediately
read -p "Would you like to start training now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Starting training...${NC}"
    lab train local --agent code --steps 100 --background --notify
    echo ""
    echo -e "${GREEN}Training started in background!${NC}"
    echo "You'll receive a notification when complete."
    echo ""
    echo "Check status with: lab train status"
fi
