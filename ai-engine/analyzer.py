"""
Core alert analysis logic using LangChain + Ollama.
"""

import os
import json
import re
import logging
from pathlib import Path
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"

MITRE_PATTERNS = {
    "brute force": ("TA0006 - Credential Access", "T1110 - Brute Force"),
    "port scan": ("TA0007 - Discovery", "T1046 - Network Service Scanning"),
    "sql injection": ("TA0001 - Initial Access", "T1190 - Exploit Public-Facing Application"),
    "xss": ("TA0001 - Initial Access", "T1190 - Exploit Public-Facing Application"),
    "privilege escalation": ("TA0004 - Privilege Escalation", "T1068 - Exploitation for Privilege Escalation"),
    "lateral movement": ("TA0008 - Lateral Movement", "T1021 - Remote Services"),
    "exfiltration": ("TA0010 - Exfiltration", "T1048 - Exfiltration Over Alternative Protocol"),
    "malware": ("TA0002 - Execution", "T1204 - User Execution"),
    "ransomware": ("TA0040 - Impact", "T1486 - Data Encrypted for Impact"),
    "c2": ("TA0011 - Command and Control", "T1071 - Application Layer Protocol"),
    "phishing": ("TA0001 - Initial Access", "T1566 - Phishing"),
    "web shell": ("TA0003 - Persistence", "T1505.003 - Web Shell"),
    "dns tunneling": ("TA0011 - Command and Control", "T1071.004 - DNS"),
}


class AlertAnalyzer:
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME", "llama3")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self._stats = {"analyzed": 0, "escalated": 0, "closed": 0, "errors": 0}

        self.llm = Ollama(
            model=self.model_name,
            base_url=self.ollama_host,
            temperature=0.1,        # low temperature = consistent, deterministic output
        )

        self.triage_prompt = PromptTemplate(
            input_variables=["alert"],
            template=self._load_prompt("triage.txt"),
        )
        self.summary_prompt = PromptTemplate(
            input_variables=["alert"],
            template=self._load_prompt("summary.txt"),
        )
        self.playbook_prompt = PromptTemplate(
            input_variables=["alert_type", "context"],
            template=self._load_prompt("playbook.txt"),
        )
        self.nl_dsl_prompt = PromptTemplate(
            input_variables=["question"],
            template=self._load_prompt("nl_to_dsl.txt"),
        )

        self.triage_chain = LLMChain(llm=self.llm, prompt=self.triage_prompt)
        self.summary_chain = LLMChain(llm=self.llm, prompt=self.summary_prompt)
        self.playbook_chain = LLMChain(llm=self.llm, prompt=self.playbook_prompt)
        self.nl_dsl_chain = LLMChain(llm=self.llm, prompt=self.nl_dsl_prompt)

    def _load_prompt(self, filename: str) -> str:
        path = PROMPT_DIR / filename
        if path.exists():
            return path.read_text()
        logger.warning(f"Prompt file {filename} not found, using fallback")
        return self._fallback_prompt(filename)

    def _fallback_prompt(self, filename: str) -> str:
        fallbacks = {
            "triage.txt": (
                "You are a SOC analyst. Analyze this security alert and respond with JSON only.\n"
                "Alert: {alert}\n"
                'Respond: {{"verdict":"ESCALATE|CLOSE|ENRICH","confidence":0.0-1.0,'
                '"severity":"LOW|MEDIUM|HIGH|CRITICAL","reasoning":"..."}}'
            ),
            "summary.txt": (
                "Summarize this security alert in 2-3 sentences for an analyst.\nAlert: {alert}"
            ),
            "playbook.txt": (
                "Generate a step-by-step incident response playbook for: {alert_type}\n"
                "Context: {context}\nFormat as numbered list."
            ),
            "nl_to_dsl.txt": (
                "Convert this question to Elasticsearch DSL JSON query:\n"
                "Question: {question}\nRespond with valid JSON only."
            ),
        }
        return fallbacks.get(filename, "{alert}")

    def _map_mitre(self, description: str) -> tuple[str, str]:
        desc_lower = description.lower()
        for keyword, (tactic, technique) in MITRE_PATTERNS.items():
            if keyword in desc_lower:
                return tactic, technique
        return "Unknown Tactic", "Unknown Technique"

    def _normalize_severity(self, wazuh_level: int) -> str:
        if wazuh_level >= 12:
            return "CRITICAL"
        elif wazuh_level >= 9:
            return "HIGH"
        elif wazuh_level >= 6:
            return "MEDIUM"
        return "LOW"

    def _parse_triage_json(self, raw: str) -> dict:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"verdict": "ENRICH", "confidence": 0.5, "reasoning": raw}

    async def analyze(self, alert: dict) -> dict:
        self._stats["analyzed"] += 1
        alert_str = json.dumps(alert, indent=2)
        mitre_tactic, mitre_technique = self._map_mitre(alert.get("rule_description", ""))
        severity_normalized = self._normalize_severity(alert.get("severity", 5))

        try:
            triage_raw = self.triage_chain.run(alert=alert_str)
            triage = self._parse_triage_json(triage_raw)

            summary_raw = self.summary_chain.run(alert=alert_str)

            verdict = triage.get("verdict", "ENRICH")
            if verdict == "ESCALATE":
                self._stats["escalated"] += 1
            elif verdict == "CLOSE":
                self._stats["closed"] += 1

            playbook = await self.generate_playbook(
                alert.get("rule_description", "security incident"),
                f"Source IP: {alert.get('source_ip')}, Severity: {severity_normalized}"
            )

            return {
                "verdict": verdict,
                "confidence": float(triage.get("confidence", 0.7)),
                "severity_normalized": triage.get("severity", severity_normalized),
                "mitre_tactic": mitre_tactic,
                "mitre_technique": mitre_technique,
                "summary": summary_raw.strip(),
                "response_recommendation": triage.get("reasoning", "Review alert manually."),
                "playbook_steps": playbook,
                "analyst_notes": (
                    f"AI model: {self.model_name} | "
                    f"Rule: {alert.get('rule_id')} | "
                    f"Source: {alert.get('source')}"
                ),
                "ai_model": self.model_name,
            }

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"LLM analysis error: {e}")
            raise

    async def generate_playbook(self, alert_type: str, context: str = "") -> list[str]:
        raw = self.playbook_chain.run(alert_type=alert_type, context=context or "No additional context")
        lines = [line.strip() for line in raw.strip().split("\n") if line.strip()]
        steps = [re.sub(r"^\d+[\.\)]\s*", "", line) for line in lines if line]
        return steps[:10]

    async def nl_to_dsl(self, question: str) -> dict:
        raw = self.nl_dsl_chain.run(question=question)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"error": "Could not parse DSL", "raw": raw}

    def get_stats(self) -> dict:
        return self._stats
