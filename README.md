# ⬡ Quantum K8s: The Whisperer SRE Agent

An autonomous, LangGraph-powered AI agent designed to observe, diagnose, and remediate Kubernetes cluster anomalies with "System Thinking" precision.

## 🚀 Overview
Quantum K8s (The Whisperer) is a production-grade SRE agent that solves the "Risky AI" problem. Unlike standard bots that simply execute commands, the Whisperer performs **Context-Aware Dependency Mapping** and validates fixes in a **Shadow Run Pre-Flight Simulator** before touching production.

### Key Capabilities:
- **Autonomous Detection:** Scans cluster events for `CrashLoopBackOff`, `OOMKilled`, and `Pending` pods.
- **Why-Tree Analysis:** Recursively traces upstream, downstream, and sideways dependencies to identify the true root cause (e.g., node starvation vs. code bug).
- **Shadow Run Simulator:** Clones failing components into temporary sandbox namespaces to verify fixes before production promotion.
- **Metric-Driven Audits:** Uses a Prometheus MCP to cross-reference event logs against real-time CPU/Memory telemetry.
- **Human-in-the-Loop:** Seamlessly pauses for high-risk operations, requesting approval via Slack or the Integrated Dashboard.

## 🛠️ Tech Stack
- **AI Core:** LangGraph (Stateful Multi-Agent Orchestration)
- **Model:** Llama 3.3 70B via Groq (Sub-second inference)
- **Infrastructure:** Kubernetes (kubectl), Prometheus (Metric Audits)
- **Frontend:** Streamlit (Glassmorphic SRE Dashboard)
- **Communication:** FastAPI Webhooks & Slack HITL

## 📦 Installation & Setup

### 1. Prerequisites
- Minikube / Local K8s Cluster
- Groq API Key
- Python 3.10+

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_key_here
SLACK_WEBHOOK_URL=your_webhook_here
PROMETHEUS_URL=http://localhost:9090
```

### 3. Run the Agent
```powershell
# 1. Initialize Virtual Environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Launch Dashboard
streamlit run ui/app.py
```

## 🛡️ Security & RBAC
The agent is designed with the principle of **Least Privilege**. Included in the repository is a strictly-scoped `rbac.yaml` that limits the agent to pod-level operations, ensuring it never requires `cluster-admin` privileges.

## 📜 Audit Trail
Every decision made by the agent is recorded in a persistent `audit_log.json`, providing a complete forensic record of every anomaly detected and remediation attempted.

---
**Developed for the Advanced Agentic Coding Presentation.**
