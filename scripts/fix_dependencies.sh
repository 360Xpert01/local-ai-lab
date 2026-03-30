#!/bin/bash
# Fix dependency conflicts for Local AI Lab

echo "🔧 Fixing dependency conflicts..."
echo "================================"
echo ""

# Install compatible versions
echo "Installing compatible package versions..."

# First, uninstall conflicting packages
pip uninstall -y transformers tokenizers accelerate unsloth unsloth_zoo trl peft bitsandbytes torch torchvision torchao 2>/dev/null

# Install compatible versions
echo ""
echo "Installing compatible versions..."
pip install \
    torch==2.1.0 \
    transformers==4.44.2 \
    tokenizers==0.20.3 \
    accelerate==0.25.0 \
    datasets==2.16.0

echo ""
echo "Installing CLI dependencies..."
cd cli
pip install -e .

echo ""
echo "✅ Dependencies fixed!"
echo ""
echo "Note: For local training with Unsloth, install it separately:"
echo "  pip install \"unsloth[cu121-torch240] @ git+https://github.com/unslothai/unsloth.git\""
echo ""
echo "This may override some versions. Use a virtual environment for best results."
