#!/bin/bash

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Local AI Lab - Setup Script                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "${RED}✗ Python 3.11+ is required${NC}"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION"
else
    echo -e "${RED}✗ Node.js 20+ is required${NC}"
    exit 1
fi

# Check Ollama
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama installed"
else
    echo -e "${YELLOW}!${NC} Ollama not found. Install from https://ollama.ai"
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker installed"
else
    echo -e "${YELLOW}!${NC} Docker not found. Install from https://docker.com"
fi

echo ""
echo -e "${BLUE}Setting up Local AI Lab...${NC}"

# Create config directory
mkdir -p ~/.lab/config/{models,agents}
mkdir -p ~/.lab/models/ollama

# Install CLI
echo -e "${BLUE}Installing CLI...${NC}"
cd cli
pip install -e . > /dev/null 2>&1
cd ..
echo -e "${GREEN}✓${NC} CLI installed"

# Initialize registries
echo -e "${BLUE}Initializing model registry...${NC}"
python3 -c "from cli.lab.core.registry import get_registry; get_registry()" > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Model registry initialized"

echo -e "${BLUE}Initializing agent registry...${NC}"
python3 -c "from cli.lab.core.agent_config import get_agent_registry; get_agent_registry()" > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Agent registry initialized"

# Install Web UI dependencies
echo -e "${BLUE}Installing Web UI dependencies...${NC}"
cd web-ui
npm install > /dev/null 2>&1
cd ..
echo -e "${GREEN}✓${NC} Web UI dependencies installed"

# Install Go agent dependencies (if Go is available)
if command -v go &> /dev/null; then
    echo -e "${BLUE}Installing Go agent dependencies...${NC}"
    cd agents/ops-agent
    go mod tidy > /dev/null 2>&1
    cd ../..
    echo -e "${GREEN}✓${NC} Go agent dependencies installed"
fi

# Install Rust agent dependencies (if Rust is available)
if command -v cargo &> /dev/null; then
    echo -e "${BLUE}Installing Rust agent dependencies...${NC}"
    cd agents/security-agent
    cargo fetch > /dev/null 2>&1
    cd ../..
    echo -e "${GREEN}✓${NC} Rust agent dependencies installed"
fi

# Install Node agent dependencies
echo -e "${BLUE}Installing Node agent dependencies...${NC}"
cd agents/architect-agent
npm install > /dev/null 2>&1
cd ../..
echo -e "${GREEN}✓${NC} Node agent dependencies installed"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Setup Complete!                               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Quick Start:"
echo "  1. Pull a base model:     lab model pull qwen2.5-coder-7b-instruct"
echo "  2. Spawn an agent:        lab agent spawn code"
echo "  3. Run multi-agent demo:  lab multi demo --scenario feature-dev"
echo "  4. Start API server:      lab server"
echo "  5. Open Web UI:           make start"
echo ""
echo "Documentation:"
echo "  - CLI help:               lab --help"
echo "  - Model management:       lab model --help"
echo "  - Agent commands:         lab agent --help"
echo "  - Multi-agent:            lab multi --help"
echo ""
