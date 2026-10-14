# 🛡️ AI Agent Security Platform

> **A Defense-in-Depth Runtime Security Perimeter for Autonomous AI Agents and LLM Applications.**  
> Defending against Prompt Injection (OWASP LLM01), Unauthorized Tool Escalation (OWASP LLM08), and Sensitive Data Exfiltration (OWASP LLM02) with Human-in-the-Loop Oversight.

[![Tests](https://img.shields.io/badge/tests-41%2F41%20passing-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)]()
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)]()
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

---

## 📌 Overview

As Large Language Models evolve into **Autonomous AI Agents** capable of invoking external APIs, querying databases, and executing tools, traditional cybersecurity defenses (WAFs, static regex) become insufficient. Because agents interpret untrusted natural language as instructions, adversarial inputs can cause agents to override safety instructions, escalate permissions, or exfiltrate credentials.

This platform implements an **enterprise-grade defensive perimeter** placed directly between untrusted inputs, the LLM agent, and external tools.

---

## 🏛️ High-Level Architecture

```
                                      +------------------------------------+
                                      |       React 19 Security Console    |
                                      +-----------------+------------------+
                                                        |
                                                        v (JWT Authenticated)
+---------------------------------------------------------------------------------------------------------+
|                                     FASTAPI DEFENSIVE PERIMETER GATEWAY                                 |
|                                                                                                         |
|   1. Normalization & Decode   ==>   2. Multi-Vector Prompt   ==>   3. Transparent Risk Scoring Engine   |
|      (Base64, Delimiters,              Injection Detector             (0-100 Score, 5 Risk Tiers,       |
|       Unicode normalization)           (Direct & Indirect)             Compound Threat Penalty)         |
+-------------------------------------------------------+-------------------------------------------------+
                                                        |
                                       [ Risk >= 70? ] -+- Yes ===> 🚨 BLOCKED & INTERCEPTED (Audit Log)
                                                        |
                                                        v No
+---------------------------------------------------------------------------------------------------------+
|                                        AGENT EXECUTION & TOOL RUNTIME                                   |
|                                                                                                         |
|   4. Tool RBAC Engine         ==>   5. Human-in-the-Loop Queue  ==>  6. Output Data Leakage Scanner     |
|      (User / Reviewer / Admin)         (High-Risk Pause & Review)       (Secret & Credential Redaction) |
+---------------------------------------------------------------------------------------------------------+
```

---

## 🧩 The 10 Major System Modules

| Module | Name | Description | Key File |
| :---: | :--- | :--- | :--- |
| **01** | **AI Agent Runtime** | Core LLM reasoning engine with Groq LLaMA 3.3 70B & local fallback | `backend/app/agent/runner.py` |
| **02** | **Prompt Injection Detector** | Detects instruction overrides, DAN jailbreaks, delimiters, and indirect document injection | `backend/app/security/detector.py` |
| **03** | **Risk Scoring & Classification** | 0–100 numerical risk score across 5 tiers (*Safe, Low, Medium, High, Critical*) | `backend/app/security/risk_scorer.py` |
| **04** | **Tool RBAC Policy Engine** | Role-based tool access control (`USER`, `REVIEWER`, `ADMIN`) with live DB policy editor | `backend/app/security/policy_engine.py` |
| **05** | **Agent Action Monitoring** | Observability for all tool calls, arguments, timestamps, and perimeter verdicts | `backend/app/models/security_event.py` |
| **06** | **Output Security Scanner** | Inspects generated outputs and masks leaked API keys, tokens, and credentials | `backend/app/security/output_scanner.py` |
| **07** | **Human-in-the-Loop (HITL)** | Intercepts high-risk operations (e.g. `rotate_credentials`) for analyst review | `backend/app/api/v1/approvals.py` |
| **08** | **SOC Dashboard & Benchmark** | Centralized security analytics, threat charts, and **16-vector benchmark suite** | `backend/app/api/v1/simulator.py` |
| **09** | **Threat Intelligence Engine** | IOC checker validating suspicious domains, phishing URLs, IPs, and hashes | `backend/app/security/threat_intel.py` |
| **10** | **Agent Memory Security** | Sanitizes memory entries to prevent indirect prompt poisoning of persistent storage | `backend/app/security/agent_memory.py` |

---

## 🧪 16-Vector Defense Benchmark

The automated attack simulator tests 16 canonical vectors with **100% accuracy**:
- **Vector 1:** Direct Instruction Override (`Ignore all previous instructions...`) $\rightarrow$ **Blocked**
- **Vector 2:** DAN Mode Jailbreak Persona $\rightarrow$ **Blocked**
- **Vector 3:** System Prompt & Directive Extraction $\rightarrow$ **Blocked**
- **Vector 4:** Delimiter Manipulation & XML Tag Escape $\rightarrow$ **Blocked**
- **Vector 5:** Base64 Obfuscated Injection $\rightarrow$ **Blocked**
- **Vector 6:** Indirect Document Injection $\rightarrow$ **Blocked**
- **Vector 7:** Roleplay Authority Escalation $\rightarrow$ **Blocked**
- **Vector 8:** Recursive / Multi-Turn Instruction Escape $\rightarrow$ **Blocked**
- **Vector 9:** Unauthorized Privilege Escalation $\rightarrow$ **Blocked**
- **Vector 10:** Tool Execution Denial (Standard User) $\rightarrow$ **Blocked**
- **Vector 11:** Human-in-the-Loop Escalation $\rightarrow$ **Pending Approval**
- **Vector 12:** Output Secret & Token Exfiltration $\rightarrow$ **Redacted**
- **Vector 13:** Output System Prompt Disclosure Prevention $\rightarrow$ **Redacted**
- **Vector 14:** Threat Intelligence Malicious IOC Block $\rightarrow$ **Blocked**
- **Vector 15:** Persistent Memory Poisoning Attempt $\rightarrow$ **Blocked**
- **Vector 16:** Clean Baseline Task (`Calculate 25 * 40`) $\rightarrow$ **Allowed (0.0 False Positives)**

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
Frontend Security Console will be live at: `http://127.0.0.1:5173`

---

## 👥 Demo Accounts

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@agentsec.com` | `AdminPass123!` | Tool RBAC editing, approvals, system configuration, audit export |
| **Security Analyst** | `analyst@agentsec.com` | `AnalystPass123!` | HITL approval queue, 16-vector benchmark execution, SOC telemetry |
| **Standard User** | `user@agentsec.com` | `UserPass123!` | Standard agent interactions (restricted from sensitive tools) |

---

## 📊 Automated Test Suite

Run the full pytest suite (41 unit tests across all 10 modules):
```bash
PYTHONPATH=backend pytest tests/ -v
```

```
============================== 41 passed in 7.30s ==============================
```

---

## 📄 License
This project is developed as an academic semester project and is released under the MIT License.
