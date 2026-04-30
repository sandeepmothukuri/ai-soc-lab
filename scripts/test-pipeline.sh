#!/usr/bin/env bash
# End-to-end pipeline health check
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAILURES=$((FAILURES+1)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

FAILURES=0

check_http() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    local code
    code=$(curl -sk -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    if [ "$code" = "$expected_code" ] || [ "$code" = "200" ] || [ "$code" = "302" ]; then
        pass "$name ($url) → HTTP $code"
    else
        fail "$name ($url) → HTTP $code (expected $expected_code)"
    fi
}

echo ""
echo "=== AI-SOC Lab Pipeline Health Check ==="
echo ""

echo "--- Core Services ---"
check_http "Wazuh Dashboard" "https://localhost:443" 200
check_http "Wazuh API" "https://localhost:55000" 401
check_http "TheHive" "http://localhost:9000" 200
check_http "Cortex" "http://localhost:9001" 200
check_http "Shuffle" "http://localhost:3001" 200
check_http "MISP" "http://localhost:8080" 200
check_http "Ollama" "http://localhost:11434/api/tags" 200
check_http "AI Engine Health" "http://localhost:8888/health" 200
check_http "AI Engine Docs" "http://localhost:8888/docs" 200

echo ""
echo "--- Docker Container Status ---"
containers=("wazuh-manager" "wazuh-indexer" "wazuh-dashboard" "thehive" "cortex" "cassandra" "shuffle-backend" "shuffle-frontend" "ollama" "ai-engine" "misp")
for c in "${containers[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "$c"; then
        pass "Container: $c"
    else
        fail "Container: $c (not running)"
    fi
done

echo ""
echo "--- AI Engine Functional Test ---"
if curl -sf "http://localhost:8888/health" >/dev/null 2>&1; then
    AI_RESPONSE=$(curl -sf "http://localhost:8888/health")
    MODEL=$(echo "$AI_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('model','unknown'))" 2>/dev/null || echo "unknown")
    pass "AI Engine health check (model: $MODEL)"

    TEST_RESULT=$(python3 scripts/send-test-alert.py ssh-bruteforce 2>&1 || true)
    if echo "$TEST_RESULT" | grep -q "VERDICT:"; then
        pass "AI alert analysis working"
    else
        fail "AI alert analysis failed"
        echo "$TEST_RESULT"
    fi
else
    fail "AI Engine not reachable"
fi

echo ""
echo "================================"
if [ "$FAILURES" -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
else
    echo -e "${RED}$FAILURES check(s) failed${NC}"
    exit 1
fi
echo ""
