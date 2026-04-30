# MITRE ATT&CK Mapping Reference

This lab covers detection for the following MITRE ATT&CK techniques.

## Detection Coverage

| Technique ID | Technique Name | Detection Source | Wazuh Rule |
|-------------|---------------|-----------------|------------|
| T1110 | Brute Force | Wazuh auth logs | 5710-5716, 100001 |
| T1046 | Network Service Scanning | Suricata, Zeek | ET-SCAN-* |
| T1190 | Exploit Public-Facing Application | Wazuh web logs | 31100-31199 |
| T1505.003 | Web Shell | Wazuh syscheck | 100003 |
| T1068 | Exploitation for Privilege Escalation | Wazuh sudo logs | 100002 |
| T1136 | Create Account | Wazuh useradd | 100005 |
| T1021 | Remote Services | Wazuh, Zeek | 5700-5799 |
| T1041 | Exfiltration Over C2 Channel | Zeek, Suricata | 100004 |
| T1048 | Exfiltration Over Alternative Protocol | Zeek | ZEEK-DNS-TUN |
| T1071.004 | Application Layer Protocol: DNS | Zeek | 100008 |
| T1486 | Data Encrypted for Impact | Wazuh FIM | 100006 |
| T1550.002 | Pass the Hash | Wazuh Windows | 100007 |
| T1566 | Phishing | Wazuh email integration | 100100+ |
| T1204 | User Execution | Wazuh syscheck | 553, 554 |

## Tactic Coverage

| Tactic | Coverage |
|--------|----------|
| TA0001 Initial Access | Phishing, Web exploits |
| TA0002 Execution | Malware, scripts |
| TA0003 Persistence | Web shells, new accounts |
| TA0004 Privilege Escalation | Sudo abuse, exploits |
| TA0006 Credential Access | Brute force, pass-the-hash |
| TA0007 Discovery | Port scanning |
| TA0008 Lateral Movement | Remote services |
| TA0010 Exfiltration | DNS tunneling, C2 |
| TA0011 Command and Control | C2 channels |
| TA0040 Impact | Ransomware |

## AI MITRE Auto-Mapping

The AI engine automatically maps alerts to MITRE techniques using keyword analysis.
See `ai-engine/analyzer.py` → `MITRE_PATTERNS` to add or modify mappings.
