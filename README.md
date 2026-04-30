# 🧠 AI-Augmented SOC Lab

A full open-source Security Operations Center (SOC) lab enhanced with a local AI decision-support layer. Built for learning, research, and practical blue-team skill development.

---

## 📐 Architecture

```
Logs / Events
(Wazuh, Suricata, Zeek)
        ↓
   SIEM (Elastic via Wazuh)
        ↓
    Alert Trigger
        ↓
     Shuffle (SOAR)
        ↓
   Enrichment Phase
   ├─ MISP (threat intel)
   ├─ Cortex analyzers
   └─ External APIs
        ↓
   AI Engine (Ollama + LangChain)
        ↓
   Output:
   - Alert summary
   - Severity classification
   - MITRE ATT&CK mapping
   - Response recommendation
        ↓
   TheHive Case Creation
        ↓
   Analyst Decision / Automated Response
```

---

## 🛠️ Stack

| Component | Role |
|-----------|------|
| **Wazuh** | SIEM + EDR + Log aggregation |
| **Suricata** | Network IDS/IPS |
| **Zeek** | Network traffic analysis |
| **TheHive** | Case management |
| **Cortex** | Alert enrichment / analyzers |
| **Shuffle** | SOAR / workflow automation |
| **MISP** | Threat intelligence platform |
| **Ollama** | Local LLM inference (privacy-safe) |
| **LangChain** | AI pipeline orchestration |

---

## ⚙️ AI Use Cases

### 1. Alert Summarization
Converts raw log data into structured, analyst-readable summaries with MITRE ATT&CK mapping.

### 2. False Positive Reduction
AI filters known scanners, internal vulnerability scans, and maintenance window traffic.

### 3. Automated Triage (L1 Replacement Layer)
AI classifies alerts as: `CLOSE` / `ESCALATE` / `ENRICH` — with confidence score.

### 4. Playbook Generation
Given an alert type, AI generates a step-by-step incident response workflow.

### 5. Natural Language SIEM Queries
Ask questions in plain English and get Elasticsearch DSL queries back.

---

## 🚀 Quick Start

### Prerequisites

- Docker + Docker Compose
- 16 GB RAM minimum (32 GB recommended)
- 100 GB disk space
- Linux (Ubuntu 22.04 recommended) or WSL2

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/ai-soc-lab.git
cd ai-soc-lab
```

### 2. Deploy the core stack

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 3. Pull the AI model

```bash
./scripts/setup-ollama.sh
```

### 4. Start the AI engine

```bash
cd ai-engine
pip install -r requirements.txt
python app.py
```

### 5. Import Shuffle workflows

Import the JSON files from `shuffle-workflows/` into your Shuffle instance.

---

## 📁 Project Structure

```
ai-soc-lab/
├── docker/                    # Docker Compose configs per service
│   ├── docker-compose.wazuh.yml
│   ├── docker-compose.thehive.yml
│   ├── docker-compose.shuffle.yml
│   ├── docker-compose.misp.yml
│   └── docker-compose.ollama.yml
├── ai-engine/                 # Python AI pipeline
│   ├── app.py                 # FastAPI server
│   ├── analyzer.py            # Core alert analysis logic
│   ├── prompts/               # LLM prompt templates
│   │   ├── triage.txt
│   │   ├── summary.txt
│   │   └── playbook.txt
│   └── requirements.txt
├── shuffle-workflows/         # SOAR automation workflows
│   ├── ssh-bruteforce.json
│   ├── malware-detection.json
│   └── data-exfiltration.json
├── wazuh-config/              # Custom Wazuh rules and decoders
│   ├── custom-rules.xml
│   └── ossec.conf
├── thehive-config/            # TheHive case templates
│   └── case-templates.json
├── scripts/                   # Deployment and utility scripts
│   ├── deploy.sh
│   ├── setup-ollama.sh
│   ├── test-pipeline.sh
│   └── send-test-alert.py
└── docs/                      # Extended documentation
    ├── setup-guide.md
    ├── ai-prompts.md
    ├── shuffle-workflows.md
    └── mitre-mapping.md
```

---

## 🔐 Security Considerations

- All LLM inference runs **locally via Ollama** — no data leaves your network
- AI output is **advisory only** — analysts retain final decision authority
- Every AI decision is **logged with timestamp, confidence score, and reasoning**
- Avoid sending raw logs to cloud-based LLMs

---

## 📊 Day-by-Day Build Plan

| Day | Task |
|-----|------|
| 1-2 | Deploy Wazuh + connect endpoints |
| 3 | Deploy TheHive + Cortex |
| 4 | Deploy Shuffle + configure webhooks |
| 5 | Install Ollama + pull LLaMA 3 |
| 6-7 | Connect pipeline: Shuffle → AI Engine → TheHive |

---

## 🤖 Supported AI Models (via Ollama)

| Model | Size | Best For |
|-------|------|----------|
| `llama3` | 8B | General triage, balanced |
| `mistral` | 7B | Fast triage, low RAM |
| `phi3` | 3.8B | Minimal resources |
| `llama3:70b` | 70B | High-accuracy analysis |

---

## 📜 License

MIT — free to use, modify, and share.

---

## 🤝 Contributing

Pull requests welcome. See [docs/setup-guide.md](docs/setup-guide.md) to get started.
