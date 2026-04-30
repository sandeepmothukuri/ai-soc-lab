#!/usr/bin/env bash
# Full SOC lab deployment script
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[-]${NC} $1"; exit 1; }

check_requirements() {
    log "Checking requirements..."
    command -v docker >/dev/null 2>&1 || err "Docker not found. Install Docker first."
    command -v docker-compose >/dev/null 2>&1 || err "docker-compose not found."

    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 16 ]; then
        warn "Less than 16GB RAM detected ($TOTAL_MEM GB). Performance may suffer."
    fi

    DISK_FREE=$(df -BG . | awk 'NR==2{print $4}' | tr -d 'G')
    if [ "$DISK_FREE" -lt 50 ]; then
        warn "Less than 50GB free disk ($DISK_FREE GB). Some services may fail."
    fi
}

set_system_params() {
    log "Configuring system parameters..."
    sysctl -w vm.max_map_count=262144 2>/dev/null || warn "Could not set vm.max_map_count (run as root)"
    echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf 2>/dev/null || true
}

create_network() {
    log "Creating SOC network..."
    docker network create soc-network 2>/dev/null || warn "Network 'soc-network' already exists"
}

deploy_service() {
    local name=$1
    local file=$2
    log "Deploying $name..."
    docker-compose -f "$file" up -d
    log "$name deployed"
}

wait_for_service() {
    local name=$1
    local url=$2
    local max_wait=${3:-120}
    local waited=0

    log "Waiting for $name to be ready..."
    while ! curl -sf "$url" >/dev/null 2>&1; do
        sleep 5
        waited=$((waited + 5))
        if [ $waited -ge $max_wait ]; then
            warn "$name did not become ready in ${max_wait}s, continuing..."
            return
        fi
    done
    log "$name is ready"
}

print_summary() {
    echo ""
    echo -e "${GREEN}==============================${NC}"
    echo -e "${GREEN}  AI-SOC Lab Deployed!${NC}"
    echo -e "${GREEN}==============================${NC}"
    echo ""
    echo "  Wazuh Dashboard  → https://localhost:443"
    echo "  TheHive          → http://localhost:9000"
    echo "  Cortex           → http://localhost:9001"
    echo "  Shuffle          → http://localhost:3001"
    echo "  MISP             → http://localhost:8080"
    echo "  AI Engine        → http://localhost:8888"
    echo "  Ollama           → http://localhost:11434"
    echo ""
    echo "  Default Wazuh credentials: admin / SecretPassword"
    echo "  Default MISP credentials: admin@admin.test / admin"
    echo "  Default Shuffle credentials: admin / password"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Run: ./scripts/setup-ollama.sh"
    echo "  2. Import shuffle-workflows/ into Shuffle"
    echo "  3. Connect Wazuh webhook to Shuffle"
    echo ""
}

main() {
    log "Starting AI-SOC Lab deployment..."
    check_requirements
    set_system_params
    create_network

    DOCKER_DIR="$(dirname "$0")/../docker"

    deploy_service "Wazuh SIEM" "$DOCKER_DIR/docker-compose.wazuh.yml"
    sleep 15

    deploy_service "TheHive + Cortex" "$DOCKER_DIR/docker-compose.thehive.yml"
    deploy_service "Shuffle SOAR" "$DOCKER_DIR/docker-compose.shuffle.yml"
    deploy_service "MISP" "$DOCKER_DIR/docker-compose.misp.yml"

    wait_for_service "Wazuh" "https://localhost:443" 180
    wait_for_service "TheHive" "http://localhost:9000" 120
    wait_for_service "Shuffle" "http://localhost:3001" 120

    deploy_service "Ollama + AI Engine" "$DOCKER_DIR/docker-compose.ollama.yml"

    wait_for_service "AI Engine" "http://localhost:8888/health" 120

    print_summary
}

main "$@"
