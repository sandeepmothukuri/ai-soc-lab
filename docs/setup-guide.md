# Setup Guide

## System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 16 GB | 32 GB |
| Disk | 100 GB | 200 GB SSD |
| OS | Ubuntu 20.04 | Ubuntu 22.04 LTS |

---

## Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Set kernel parameter for Elasticsearch
echo 'vm.max_map_count=262144' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Log out and back in for Docker group to apply
```

---

## Step 2: Clone and Deploy

```bash
git clone https://github.com/YOUR_USERNAME/ai-soc-lab.git
cd ai-soc-lab

chmod +x scripts/*.sh
./scripts/deploy.sh
```

---

## Step 3: Pull AI Model

```bash
# Detect your system and pull the right model
./scripts/setup-ollama.sh

# For specific models:
./scripts/setup-ollama.sh mistral     # low RAM (8GB)
./scripts/setup-ollama.sh llama3      # standard (16GB)
./scripts/setup-ollama.sh llama3:70b  # high accuracy (32GB)
```

---

## Step 4: Configure Wazuh Webhook to Shuffle

1. Log into Wazuh Dashboard → `https://localhost:443`
2. Go to **Management → Integrations**
3. Add new integration:
   - Name: `shuffle`
   - Hook URL: `http://localhost:5001/api/v1/hooks/WEBHOOK_ID`
   - Alert format: `json`
   - Alert levels: `7` and above

Get your webhook ID from Shuffle:
1. Open Shuffle → `http://localhost:3001`
2. Import workflow from `shuffle-workflows/ssh-bruteforce.json`
3. Click the Webhook trigger → copy the URL

---

## Step 5: Configure TheHive API Key

1. Log into TheHive → `http://localhost:9000`
   - Username: `admin@thehive.local`
   - Password: `secret`
2. Go to **Settings → API Key → Create**
3. Copy the key
4. Update `docker-compose.ollama.yml`:
   ```yaml
   environment:
     - THEHIVE_API_KEY=your_key_here
   ```
5. Restart AI Engine: `docker-compose -f docker/docker-compose.ollama.yml restart ai-engine`

---

## Step 6: Import TheHive Case Templates

```bash
# Get TheHive API key first (step 5)
export THEHIVE_API_KEY="your_key_here"

curl -X POST http://localhost:9000/api/case/template \
  -H "Authorization: Bearer $THEHIVE_API_KEY" \
  -H "Content-Type: application/json" \
  -d @thehive-config/case-templates.json
```

---

## Step 7: Verify Pipeline

```bash
# Run health check
./scripts/test-pipeline.sh

# Send a test alert through the full pipeline
python3 scripts/send-test-alert.py ssh-bruteforce

# Test all scenarios
python3 scripts/send-test-alert.py all
```

---

## Connecting Endpoints to Wazuh

### Linux endpoint

```bash
# On the endpoint
curl -so wazuh-agent.deb https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.7.3-1_amd64.deb
sudo WAZUH_MANAGER="YOUR_WAZUH_IP" dpkg -i ./wazuh-agent.deb
sudo systemctl enable wazuh-agent && sudo systemctl start wazuh-agent
```

### Windows endpoint

```powershell
# On the endpoint (PowerShell as Admin)
Invoke-WebRequest -Uri "https://packages.wazuh.com/4.x/windows/wazuh-agent-4.7.3-1.msi" -OutFile wazuh-agent.msi
msiexec /i wazuh-agent.msi WAZUH_MANAGER="YOUR_WAZUH_IP" /quiet
net start WazuhSvc
```

---

## Common Issues

### Elasticsearch won't start

```bash
sudo sysctl -w vm.max_map_count=262144
```

### Out of memory

Reduce Java heap in compose files:
```yaml
environment:
  - "ES_JAVA_OPTS=-Xms256m -Xmx512m"
```

### Ollama model won't load

```bash
# Check available RAM
free -h
# Try a smaller model
./scripts/setup-ollama.sh phi3
```

### AI Engine can't reach Ollama

```bash
# Check network
docker exec ai-engine curl http://ollama:11434/api/tags
# Check logs
docker logs ai-engine
```
