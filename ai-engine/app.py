"""
AI SOC Engine - FastAPI server
Receives alert data, runs LLM analysis, returns structured triage output.
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from analyzer import AlertAnalyzer
from thehive_client import TheHiveClient

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI SOC Engine",
    description="LLM-powered alert triage and analysis for open-source SOC",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = AlertAnalyzer()
hive_client = TheHiveClient()


class AlertPayload(BaseModel):
    alert_id: str
    source: str  # wazuh | suricata | zeek
    rule_id: Optional[str] = None
    rule_description: str
    severity: int  # 1-15 (Wazuh scale)
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    hostname: Optional[str] = None
    timestamp: str
    raw_log: str
    misp_context: Optional[dict] = None
    geo_info: Optional[dict] = None


class TriageResult(BaseModel):
    alert_id: str
    verdict: str  # CLOSE | ESCALATE | ENRICH
    confidence: float  # 0.0 - 1.0
    severity_normalized: str  # LOW | MEDIUM | HIGH | CRITICAL
    mitre_tactic: Optional[str]
    mitre_technique: Optional[str]
    summary: str
    response_recommendation: str
    playbook_steps: list[str]
    analyst_notes: str
    ai_model: str
    processing_time_ms: int
    timestamp: str


@app.get("/health")
async def health():
    return {"status": "ok", "model": os.getenv("MODEL_NAME", "llama3")}


@app.post("/analyze", response_model=TriageResult)
async def analyze_alert(alert: AlertPayload, background_tasks: BackgroundTasks):
    start = datetime.utcnow()
    logger.info(f"Analyzing alert {alert.alert_id} from {alert.source}")

    try:
        result = await analyzer.analyze(alert.dict())
    except Exception as e:
        logger.error(f"Analysis failed for {alert.alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
    result["processing_time_ms"] = elapsed_ms
    result["timestamp"] = datetime.utcnow().isoformat()
    result["alert_id"] = alert.alert_id

    if result.get("verdict") in ("ESCALATE", "ENRICH"):
        background_tasks.add_task(hive_client.create_case, alert.dict(), result)

    logger.info(
        f"Alert {alert.alert_id} → verdict={result['verdict']} "
        f"severity={result['severity_normalized']} ({elapsed_ms}ms)"
    )
    return result


@app.post("/playbook")
async def generate_playbook(alert_type: str, context: Optional[str] = None):
    steps = await analyzer.generate_playbook(alert_type, context)
    return {"alert_type": alert_type, "steps": steps}


@app.post("/query")
async def natural_language_query(question: str):
    """Convert plain English into an Elasticsearch DSL query."""
    dsl = await analyzer.nl_to_dsl(question)
    return {"question": question, "elasticsearch_dsl": dsl}


@app.get("/stats")
async def stats():
    return analyzer.get_stats()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8888)
