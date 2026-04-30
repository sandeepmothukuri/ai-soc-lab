# AI Prompt Engineering Guide

## Overview

The AI engine uses four prompt templates stored in `ai-engine/prompts/`.
Each is designed for a specific task and tuned for security analysis.

---

## Prompt Files

### `triage.txt` — Alert Triage
**Purpose**: Classify an alert as ESCALATE / ENRICH / CLOSE with confidence score.

**Key design decisions**:
- Instructed to consider false positive likelihood first
- Temperature set to 0.1 for consistent, deterministic output
- Output constrained to strict JSON to enable automated parsing
- MITRE ATT&CK knowledge is embedded in the system context

**Tuning tips**:
- Add your organization's known scanner IPs as false positive examples
- Include common internal tool names (Nessus, Qualys) to reduce false positives
- Lower confidence threshold if you want fewer CLOSE verdicts

---

### `summary.txt` — Alert Summary
**Purpose**: Generate a human-readable 2-3 sentence summary for analysts.

**Key design decisions**:
- Kept short — analysts read many alerts
- Directed to cover: what, where, impact
- Technical audience assumed — no over-explanation

---

### `playbook.txt` — Response Playbook
**Purpose**: Generate step-by-step incident response procedures.

**Key design decisions**:
- Structured as numbered steps for direct execution
- Follows IR framework: Contain → Investigate → Eradicate → Recover → Document
- Capped at 10 steps to keep actionable

---

### `nl_to_dsl.txt` — Natural Language to Elasticsearch DSL
**Purpose**: Let analysts query Wazuh with plain English.

**Example queries**:
```
"Show me all failed SSH logins from Russia in the last 24 hours"
"Find any alerts with severity above 10 on the finance server"
"List all DNS queries to suspicious domains today"
```

---

## Customizing Prompts

Edit any file in `ai-engine/prompts/` — changes take effect on next restart.

**To add your organization context**:

```
# In triage.txt, after the ALERT DATA section, add:

ORGANIZATION CONTEXT:
- Known scanner IPs: 10.0.0.5 (Nessus), 10.0.0.6 (Qualys)
- Business hours: 08:00-18:00 UTC Mon-Fri
- Critical assets: db-prod-01, payroll-server
```

---

## Testing Prompts

```bash
# Test a specific prompt against the running model
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "llama3",
    "prompt": "You are a SOC analyst. Classify this: SSH brute force 200 attempts success from Russia. Respond: ESCALATE or CLOSE",
    "stream": false
  }'
```

---

## Model Comparison for SOC Tasks

| Model | Triage Accuracy | Speed | RAM |
|-------|---------------|-------|-----|
| llama3:70b | Highest | Slow | 40GB |
| llama3 | High | Medium | 8GB |
| mistral | Good | Fast | 5GB |
| phi3 | Moderate | Very fast | 3GB |

Recommendation: Use `llama3` for production, `mistral` for testing.
