#!/bin/bash
# Example training workflow with all features

set -e

echo "🎓 Local AI Lab - Training Example"
echo "==================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Check if we're ready
echo -e "${YELLOW}Step 1: Checking system readiness...${NC}"
lab train local --agent code --dry-run 2>/dev/null || true
echo ""

# 2. Start background training with notification
echo -e "${YELLOW}Step 2: Starting background training...${NC}"
echo "This will train the 'code' agent in the background."
echo "You'll get a notification when it's done!"
echo ""

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama is not running. Starting it..."
    ollama serve &
    sleep 2
fi

# Start training
JOB_OUTPUT=$(lab train local --agent code --steps 50 --background --notify 2>&1)
echo "$JOB_OUTPUT"

# Extract job ID (last line containing "Started with PID")
PID=$(echo "$JOB_OUTPUT" | grep "PID:" | awk '{print $2}')

if [ -n "$PID" ]; then
    echo ""
    echo -e "${GREEN}✓ Training started with PID: $PID${NC}"
    echo ""
    
    # 3. Show monitoring commands
    echo -e "${YELLOW}Step 3: Monitoring commands${NC}"
    echo ""
    echo "Check status:"
    echo "  lab train status"
    echo ""
    echo "View progress file:"
    echo "  cat ~/.lab/local_training/progress_code.json"
    echo ""
    echo "Stop training:"
    echo "  kill $PID"
    echo ""
    
    # 4. Wait for completion (demo only - normally you'd do other work)
    echo -e "${YELLOW}Step 4: Waiting for training to complete (demo)...${NC}"
    echo "(In real usage, continue working. You'll get a notification!)"
    echo ""
    
    # Show a spinner
    spin='-\|/'
    i=0
    while kill -0 $PID 2>/dev/null; do
        i=$(( (i+1) %4 ))
        printf "\r${spin:$i:1} Training in progress... (PID: $PID)"
        sleep 0.5
    done
    printf "\r${GREEN}✓ Training process finished!          ${NC}\n"
    echo ""
    
    # 5. Check final status
    echo -e "${YELLOW}Step 5: Final status${NC}"
    lab train status | head -20
    echo ""
    
    # 6. Show import instructions
    echo -e "${YELLOW}Step 6: Import trained model${NC}"
    echo ""
    echo "If training completed successfully, import with:"
    echo "  lab train import ~/.lab/local_training/code_model/unsloth.Q4_K_M.gguf --agent-type code"
    echo ""
    echo "Then use it:"
    echo "  lab agent spawn code --model lab-code-model"
    echo ""
    
else
    echo "⚠️  Could not start training job"
    echo "Check that all dependencies are installed:"
    echo "  pip install -e ./cli"
fi

echo "🎉 Example complete!"
