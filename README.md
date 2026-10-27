# 🏭 GxP-Compliant Agentic AI Diagnostics for Pharmaceutical Vial Packaging

A local-first, event-driven agentic observability and deviation management system designed for pharmaceutical vial packaging lines. Built to satisfy **21 CFR Part 11** electronic record and signature requirements, substituting complex cloud governance with zero-collision local execution.

---

## 🚀 Overall Architecture & Concept

Manufacturing packaging lines require rigorous real-time monitoring and immutable auditability. This system bridges edge telemetry with autonomous AI root cause analysis (RCA):

1. **Edge Telemetry Simulator**: Emits 1 Hz high-frequency packaging metrics (vial counts, line speeds, changeover timers, and alarm codes) into a local store.
2. **SQLite WAL Concurrency Layer**: Uses SQLite in Write-Ahead Logging (WAL) mode to allow concurrent multi-process writes (Simulator, AI Worker, and UI) without file lock contention.
3. **Agentic AI Diagnostic Worker**: An asynchronous daemon polling the local incident queue, utilizing **Qwen 27B via Groq** with explicit tool-calling bindings to query historical Computerized Maintenance Management System (CMMS) records and pre-incident time-series telemetry.
4. **Supervisory QA Portal & Audit Vault**: A Streamlit interface delivering real-time KPI monitoring, AI deviation reviews, and 21 CFR Part 11 electronic sign-off generating immutable SHA-256 cryptographic manifests.

# 🏗️ System Architecture

```
[ Edge Packaging Simulator ]
(Emits 1 Hz Telemetry & Alarms)
            │
            ▼
┌───────────────────────────────────────┐
│       SQLite WAL Database             │
│ (local_queue.db & plant_data.db)      │
└───────────┬───────────────┬───────────┘
            │               │
            │               │ (Reads/Writes Deviations)
            ▼               ▼
┌──────────────────────┐  ┌──────────────────────┐
│  Agentic AI Worker   │  │ Streamlit Portal     │
│ (Qwen-27B via Groq)  │  │ (Live UI & E-Sign)   │
└───────────┬───────────────▲────────────────────┘
            │               │
            ▼               │
   [ CMMS Historian ] ──────┘
   (Maintenance Logs)
---

## 🛠️ Tech Stack

* **Language**: Python 3.10+
* **Data Storage**: SQLite (WAL Mode for high-concurrency local queues and historian)
* **Agentic Framework**: LangChain, ChatGroq (`qwen/qwen3.8-27b`)
* **Supervisory Interface**: Streamlit, Pandas, Altair
* **Compliance & Security**: SHA-256 Cryptographic WORM Manifests (21 CFR Part 11)

---

## 📦 Project Structure


├── audit_vault/                  # Immutable JSON electronic signature manifests (SHA-256)
├── agent_engine.py               # LangChain Qwen-27B tool-calling RCA & CAPA engine
├── agent_worker.py               # Background daemon polling SQLite queue for incidents
├── app.py                        # Streamlit supervisory dashboard & e-signature portal
├── edge_packaging_simulator.py   # 1 Hz plant-floor telemetry and alarm simulator
├── init_db.py                    # Database schema setup with WAL mode and CMMS seed data
├── requirements.txt              # Project dependencies
└── README.md


## ⚙️ Setup & Installation

### 1. Clone & Navigate to Repository
```cmd
git clone https://github.com/dsures/mfg_agentic_ai_diagnostics.git
cd mfg_agentic_ai_diagnostics
```

### 2. Install Dependencies
```cmd
pip install -r requirements.txt
```
*(Dependencies include: `streamlit`, `langchain-groq`, `langchain-core`, `groq`, `pandas`, `python-dotenv`)*

### 3. Configure Environment Variables
Create a `.env` file in your root directory and add your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Initialize Database
Initialize the SQLite WAL database and seed default CMMS failure modes:
```cmd
python init_db.py
```

---

## 🚀 Reproduction & Execution Commands

To run the end-to-end system locally, open **three separate terminal windows** and execute the corresponding process in each:

### Terminal 1: Edge Packaging Simulator (Producer)
Streams 1 Hz line speeds, updates vial counts, and injects downtime alarms (`301` & `303`) into the queue.
```cmd
python edge_packaging_simulator.py
```

### Terminal 2: AI Diagnostic Worker Daemon (Consumer & RCA)
Polls the SQLite queue, invokes the Qwen-27B tool-calling agent, correlates CMMS history, and generates deviation records.
```cmd
python agent_worker.py
```

### Terminal 3: Supervisory & QA Portal (UI)
Launches the real-time monitoring dashboard, deviation review desk, and GxP electronic signature vault.
```cmd
streamlit run app.py
```

---

## 🔒 21 CFR Part 11 Verification Workflow

1. Open the Streamlit UI at `http://localhost:8501`.
2. Observe live KPI metrics updating as the simulator runs.
3. When an alarm (e.g., Alarm `301` Vision OCR Failure) is triggered, the AI worker will generate a deviation investigation.
4. Navigate to the **Pending AI Deviation & CAPA Investigations** section in the UI.
5. Enter your credential PIN/password, select your role, and click **Electronically Sign & Authorize**.
6. Verify that an immutable JSON manifest containing the SHA-256 checksum is written to the `audit_vault/` directory and logged in the audit trail ledger.
