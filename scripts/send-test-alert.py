#!/usr/bin/env python3
"""
Send test alerts to the AI SOC engine to verify the pipeline.
Usage: python send-test-alert.py [scenario]
Scenarios: ssh-bruteforce, port-scan, web-attack, malware, data-exfil
"""

import sys
import json
import httpx
from datetime import datetime

AI_ENGINE_URL = "http://localhost:8888"

TEST_ALERTS = {
    "ssh-bruteforce": {
        "alert_id": "TEST-001",
        "source": "wazuh",
        "rule_id": "5712",
        "rule_description": "SSH brute force attack followed by successful authentication",
        "severity": 12,
        "source_ip": "185.220.101.45",
        "dest_ip": "10.0.1.15",
        "hostname": "web-server-01",
        "timestamp": datetime.utcnow().isoformat(),
        "raw_log": (
            "Feb 15 03:42:11 web-server-01 sshd[12345]: Failed password for root from "
            "185.220.101.45 port 52341 ssh2 (x200 attempts) | "
            "Feb 15 03:44:02 web-server-01 sshd[12346]: Accepted password for root from "
            "185.220.101.45 port 52398 ssh2"
        ),
        "geo_info": {"country": "Russia", "city": "Moscow", "asn": "AS50581"},
        "misp_context": {
            "found": True,
            "tags": ["botnet", "tor-exit-node"],
            "threat_level": "high",
        },
    },
    "port-scan": {
        "alert_id": "TEST-002",
        "source": "suricata",
        "rule_id": "ET-SCAN-001",
        "rule_description": "Nmap SYN port scan detected from external host",
        "severity": 8,
        "source_ip": "192.168.100.50",
        "dest_ip": "10.0.0.0/24",
        "hostname": "firewall-01",
        "timestamp": datetime.utcnow().isoformat(),
        "raw_log": "ET SCAN Nmap Scripting Engine User-Agent Detected | 2000+ packets in 30s",
        "geo_info": {"country": "Internal", "city": "N/A", "asn": "Internal"},
        "misp_context": None,
    },
    "web-attack": {
        "alert_id": "TEST-003",
        "source": "wazuh",
        "rule_id": "31103",
        "rule_description": "SQL injection attempt detected in web application",
        "severity": 10,
        "source_ip": "203.0.113.100",
        "dest_ip": "10.0.1.20",
        "hostname": "app-server-01",
        "timestamp": datetime.utcnow().isoformat(),
        "raw_log": (
            "POST /login HTTP/1.1 | User-Agent: sqlmap/1.7 | "
            "Payload: admin' OR '1'='1'--  | Response: 200 OK"
        ),
        "geo_info": {"country": "China", "city": "Beijing", "asn": "AS4134"},
        "misp_context": {"found": False},
    },
    "malware": {
        "alert_id": "TEST-004",
        "source": "wazuh",
        "rule_id": "553",
        "rule_description": "Malware detected - suspicious file execution with known hash",
        "severity": 14,
        "source_ip": None,
        "dest_ip": None,
        "hostname": "workstation-finance-03",
        "timestamp": datetime.utcnow().isoformat(),
        "raw_log": (
            "File: C:\\Users\\jsmith\\Downloads\\invoice.exe | "
            "SHA256: 3f4a8b2c1d9e... | VirusTotal: 45/72 engines | "
            "Process spawned: cmd.exe | Network connection: 104.21.45.100:443"
        ),
        "geo_info": None,
        "misp_context": {
            "found": True,
            "tags": ["ransomware", "emotet"],
            "threat_level": "critical",
        },
    },
    "data-exfil": {
        "alert_id": "TEST-005",
        "source": "zeek",
        "rule_id": "ZEEK-DNS-TUN",
        "rule_description": "Possible DNS tunneling / data exfiltration via DNS",
        "severity": 11,
        "source_ip": "10.0.1.55",
        "dest_ip": "8.8.8.8",
        "hostname": "dev-workstation-07",
        "timestamp": datetime.utcnow().isoformat(),
        "raw_log": (
            "DNS query volume: 4500 queries/hour (baseline: 50/hour) | "
            "Subdomain entropy: 4.8 | Domain: c2.malicious-domain.xyz | "
            "Total data transferred: 450MB via DNS"
        ),
        "geo_info": None,
        "misp_context": {
            "found": True,
            "tags": ["c2", "dns-tunneling"],
            "threat_level": "high",
        },
    },
}


def send_alert(scenario: str):
    alert = TEST_ALERTS.get(scenario)
    if not alert:
        print(f"Unknown scenario: {scenario}")
        print(f"Available: {', '.join(TEST_ALERTS.keys())}")
        sys.exit(1)

    print(f"\nSending test alert: {scenario}")
    print(f"Alert ID: {alert['alert_id']}")
    print(f"Severity: {alert['severity']}")
    print("-" * 50)

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{AI_ENGINE_URL}/analyze", json=alert)
            resp.raise_for_status()
            result = resp.json()
    except httpx.ConnectError:
        print(f"Cannot connect to AI Engine at {AI_ENGINE_URL}")
        print("Is the AI Engine running? Check: docker ps")
        sys.exit(1)

    print(f"\nVERDICT:    {result['verdict']}")
    print(f"CONFIDENCE: {result['confidence']:.0%}")
    print(f"SEVERITY:   {result['severity_normalized']}")
    print(f"MITRE:      {result['mitre_tactic']}")
    print(f"            {result['mitre_technique']}")
    print(f"\nSUMMARY:\n{result['summary']}")
    print(f"\nRECOMMENDATION:\n{result['response_recommendation']}")
    print(f"\nPLAYBOOK STEPS:")
    for i, step in enumerate(result.get("playbook_steps", []), 1):
        print(f"  {i}. {step}")
    print(f"\nProcessing time: {result['processing_time_ms']}ms | Model: {result['ai_model']}")


def main():
    scenario = sys.argv[1] if len(sys.argv) > 1 else "ssh-bruteforce"

    if scenario == "all":
        for s in TEST_ALERTS:
            send_alert(s)
            print("\n" + "=" * 60 + "\n")
    else:
        send_alert(scenario)


if __name__ == "__main__":
    main()
