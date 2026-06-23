#!/bin/bash
set -e

echo ""
echo "Cognitive Mirror — Bootstrap"
echo "============================="
echo ""

echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+ from https://python.org"
    exit 1
fi
PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  OK  python3 ($PYVER)"

echo ""
echo "Testing coherence engine directly (no install required)..."
cd "$(dirname "$0")/.."

DESCRIBE='{"jsonrpc":"2.0","id":1,"method":"describe"}'
RESULT=$(echo "$DESCRIBE" | python3 executas/coherence-engine/coherence_engine.py)

if echo "$RESULT" | python3 -c "import sys,json; r=json.loads(sys.stdin.read()); assert 'result' in r and 'name' in r['result']"; then
    echo "  OK  coherence engine describe"
else
    echo "  FAIL  coherence engine describe"
    echo "  Output: $RESULT"
    exit 1
fi

EVAL='{"jsonrpc":"2.0","id":2,"method":"call","params":{"name":"evaluate","arguments":{"messages":[{"content":"How do I approach this problem?","timestamp":1748965722,"topic":"coding","role":"user"}]}}}'
RESULT2=$(echo "$EVAL" | python3 executas/coherence-engine/coherence_engine.py)

if echo "$RESULT2" | python3 -c "import sys,json; r=json.loads(sys.stdin.read()); assert 'psi' in r['result']['output']"; then
    PSI=$(echo "$RESULT2" | python3 -c "import sys,json; r=json.loads(sys.stdin.read()); print(r['result']['output']['psi'])")
    echo "  OK  coherence engine evaluate (Psi=$PSI)"
else
    echo "  FAIL  coherence engine evaluate"
    exit 1
fi

echo ""
echo "Running test suite..."
python3 tests/test_coherence_engine.py
if [ $? -eq 0 ]; then
    echo "  OK  all tests passed"
else
    echo "  WARN  some tests failed — check output above"
fi

echo ""
echo "============================="
echo "Bootstrap complete!"
echo ""
echo "Standalone usage (no Anna install needed):"
echo "  Open bundle/index.html in a browser"
echo "  It runs in standalone mode automatically"
echo ""
echo "For Anna platform deployment:"
echo "  1. Go to https://anna.partners/executa"
echo "  2. My Tools → Create Tool → Mint ID"
echo "  3. My Skills → Create Skill → Mint ID"
echo "  4. Run: python scripts/set-tool-id.py apply --tool YOUR_TOOL_ID --skill YOUR_SKILL_ID"
echo "  5. Install tool: cd executas/coherence-engine && uv tool install . --reinstall"
echo "  6. Run: bash scripts/deploy.sh"
echo ""
