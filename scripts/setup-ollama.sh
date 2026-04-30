#!/usr/bin/env bash
# Pull and configure Ollama models for the AI SOC engine
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
DEFAULT_MODEL="${1:-llama3}"

wait_for_ollama() {
    log "Waiting for Ollama to be ready..."
    local attempts=0
    while ! curl -sf "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; do
        sleep 3
        attempts=$((attempts + 1))
        if [ $attempts -ge 40 ]; then
            echo "Ollama did not start in time."
            exit 1
        fi
    done
    log "Ollama is ready"
}

pull_model() {
    local model=$1
    log "Pulling model: $model (this may take several minutes)..."
    curl -sf "${OLLAMA_HOST}/api/pull" \
        -d "{\"name\": \"$model\"}" \
        -H "Content-Type: application/json" | \
        python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line:
        try:
            d = json.loads(line)
            if 'status' in d:
                print(f'  {d[\"status\"]}', flush=True)
        except:
            pass
"
    log "Model $model pulled successfully"
}

test_model() {
    local model=$1
    log "Testing model $model..."
    response=$(curl -sf "${OLLAMA_HOST}/api/generate" \
        -d "{\"model\": \"$model\", \"prompt\": \"Reply with: READY\", \"stream\": false}" \
        -H "Content-Type: application/json")
    echo "  Model response: $(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','N/A'))")"
    log "Model test passed"
}

recommend_model() {
    local total_ram
    total_ram=$(free -g | awk '/^Mem:/{print $2}' 2>/dev/null || echo 8)

    echo ""
    echo "System RAM: ${total_ram}GB"
    echo ""
    if [ "$total_ram" -ge 32 ]; then
        echo "  Recommended: llama3:70b (best accuracy)"
    elif [ "$total_ram" -ge 16 ]; then
        echo "  Recommended: llama3 (8B, good balance)"
    elif [ "$total_ram" -ge 8 ]; then
        echo "  Recommended: mistral (7B, faster)"
    else
        echo "  Recommended: phi3 (3.8B, minimal RAM)"
    fi
    echo ""
}

main() {
    log "Ollama model setup for AI-SOC Engine"
    recommend_model
    wait_for_ollama
    pull_model "$DEFAULT_MODEL"
    test_model "$DEFAULT_MODEL"

    log "Setup complete. AI Engine will use model: $DEFAULT_MODEL"
    echo ""
    echo "To use a different model:"
    echo "  ./setup-ollama.sh mistral"
    echo "  ./setup-ollama.sh phi3"
    echo "  ./setup-ollama.sh llama3:70b"
    echo ""
    echo "Update MODEL_NAME in docker-compose.ollama.yml to switch."
}

main "$@"
