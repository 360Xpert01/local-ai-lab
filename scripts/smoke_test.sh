#!/bin/bash
# Quick smoke test for Local AI Lab

set -e  # Exit on error

echo "🧪 Local AI Lab Smoke Test"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CLI_DIR="$PROJECT_ROOT/cli"

echo "Project root: $PROJECT_ROOT"
echo "CLI dir: $CLI_DIR"
echo ""

cd "$CLI_DIR"

# Helper function
run_pytest() {
    local name=$1
    local test_path=$2
    
    echo -n "Testing $name... "
    if python -m pytest "$test_path" -v --tb=no -q > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

run_python() {
    local name=$1
    local code=$2
    
    echo -n "Testing $name... "
    if python -c "$code" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

run_cli() {
    local name=$1
    local args=$2
    
    echo -n "Testing $name... "
    if python -m lab.cli $args > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "📦 Package Tests"
echo "----------------"
run_python "CLI package" "import lab"
run_python "Core modules" "from lab.core.registry import get_registry"
run_python "Training modules" "from lab.training.local_trainer import LocalTrainer"

echo ""
echo "🔧 CLI Tests"
echo "------------"
run_cli "CLI help" "--help"
run_cli "Model list" "model list"
run_cli "Agent list" "agent list"
run_cli "Status" "status"

echo ""
echo "🧠 Registry Tests"
echo "-----------------"
run_python "Registry load" "from lab.core.registry import get_registry; r = get_registry(); print(len(r.list_models()))"
run_python "Agent registry" "from lab.core.agent_config import get_agent_registry; r = get_agent_registry(); print(len(r.list_agents()))"

echo ""
echo "🎓 Training Tests"
echo "-----------------"
run_python "Training imports" "from lab.training.local_trainer import LocalTrainer, LocalTrainingConfig"
run_python "Colab adapter" "from lab.training.colab_adapter import ColabAdapter"

echo ""
echo "🤖 Multi-Agent Tests"
echo "--------------------"
run_python "Orchestrator" "from lab.agents.orchestrator import get_orchestrator; o = get_orchestrator()"

echo ""
echo "=========================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED test(s) failed${NC}"
    exit 1
fi
