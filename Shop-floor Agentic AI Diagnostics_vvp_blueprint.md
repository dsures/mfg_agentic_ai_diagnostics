# Project Blueprint: Shop-floor Agentic AI Diagnostics

### An Agentic Shop-Floor Diagnostics & OEE Triage System for Regulated Manufacturing

## 1. Executive Summary & Strategic Positioning

This Value Validation Project (VVP) demonstrates an end-to-end Industry 4.0 architecture tailored for high-consequence, regulated manufacturing (e.g., Aseptic Fill-Finish, Biologics, and Active Pharmaceutical Ingredients).

Rather than presenting an ungrounded proof-of-concept, the platform establishes a realistic operational bridge between shop-floor operational technology (OT), enterprise systems (MES/QMS/Historians), and stateful agentic intelligence.

### Unified Positioning Matrix

```
                          +------------------------------------------------+
                          |             AsepticOps Copilot                 |
                          | (Generic Digital Shop-Floor Management Platform) |
                          +------------------------------------------------+
                                       /           |           \
                                      /            |            \
                                     /             |             \
                                    v              v              v
                  +---------------------+  +---------------+  +---------------------+
                  |       Pfizer        |  |  C&F Strategy |  | Deep Digital Group  |
                  +---------------------+  +---------------+  +---------------------+
                  | "Digital Teammate   |  | "OEE Value    |  | "UNS Event-Driven   |
                  |  for IMEx Tier-2    |  |  Realization  |  |  OT/IT Integration  |
                  |  Shift Huddles"     |  |  Roadmap"     |  |  Architecture"      |
                  +---------------------+  +---------------+  +---------------------+

```

* **Target 1 (Pfizer - Digital Operations Agentic Lead):** Framed as an AI operational teammate executing work directly alongside shift technicians within Daily Tiered Management / Shift Huddles (mapping directly to IMEx rituals) under strict human-in-the-loop GxP governance.

* **Target 2 (C&F - Manufacturing Solutions Business Consultant):** Framed as a Value Realization platform quantifying lost throughput, financial downtime per hour, and multi-horizon roadmap execution.

* **Target 3 (Deep Digital Solutions Group - Industry 4.0 & Manufacturing Data Specialist):** Framed as an event-driven Unified Namespace (UNS) reference implementation demonstrating OT/IT convergence across ISA-95 levels.

## 2. Technical Architecture & Tech Stack (100% Free / Student Tier)

```
 [Edge Sensor Simulators]
 (Vibration, Temp, Pressure)
            |
            | (MQTT / ISA-95 Namespace)
            v
 [Broker: HiveMQ Cloud / Mosquitto]
   Topic: Plant_A/Sterile_Injectables/Line_03/Filling_Cell/telemetry
            |
            v
 [Data Engine: Embedded DuckDB]
   ├── historian_telemetry (Timeseries)
   ├── mes_batch_execution (Context / Recipe)
   ├── cmms_work_orders    (Asset Failures)
   └── qms_deviations       (Historical CAPAs)
            |
            +--------------------------+
            |                          |
            v                          v
 [Vector Store: ChromaDB]     [Agent Engine: LangGraph + Groq/Llama-3.3-70B]
 (GxP SOPs & Tolerances)        ├── Node 1: Ingestion & Threshold Triage
                                ├── Node 2: Context Enrichment (MES/Historian)
                                ├── Node 3: SOP Vector Search
                                ├── Node 4: Loss Attribution (Availability/Perf/Quality)
                                ├── Node 5: Human Approval Interruption [GAMP 5 Gate]
                                └── Node 6: 21 CFR Part 11 Audit Record Draft
                                       |
                                       v
                     [UI: Generic Streamlit Cloud App]
                     Digital Shop-Floor Management (SFM)

```

| Layer | Component | Tool / Technology | Cost Tier | Purpose | 
| ----- | ----- | ----- | ----- | ----- | 
| **Connectivity** | Unified Namespace (UNS) | **HiveMQ Cloud Free Tier** or **Mosquitto** | Free | ISA-95 topic standard (`Site/Area/Line/Cell/Telemetry`) | 
| **Data Engine** | Multi-System Database | **DuckDB** + **Pandas** | Open Source | Simulates Historian, MES, CMMS, and QMS relational tables | 
| **Knowledge Base** | Contextual Search / RAG | **ChromaDB** + `all-MiniLM-L6-v2` | Open Source | Embedded vector store indexed with aseptic packaging SOPs | 
| **Intelligence** | Agentic Orchestrator | **LangGraph** (Python) | Open Source | Cyclical, stateful graph execution with deterministic validation | 
| **Inference** | Large Language Model | **Groq Cloud API** (`llama-3.3-70b-versatile`) | Free Tier | Low-latency inference for structured JSON function calling | 
| **Presentation** | Shop-Floor UI | **Streamlit** (Streamlit Community Cloud) | Free | Responsive Tier-2 Daily Management & Deviation Dashboard | 

## 3. Database Schema Design (DuckDB)

To demonstrate authentic manufacturing data modeling, DuckDB will maintain four distinct schemas representing enterprise OT/IT systems:

```
-- 1. Historian: Sensor Telemetry
CREATE TABLE historian_telemetry (
    timestamp TIMESTAMP,
    site_id VARCHAR,
    line_id VARCHAR,
    asset_id VARCHAR,
    fill_speed_bpm FLOAT,
    vial_temp_celsius FLOAT,
    capper_torque_nm FLOAT,
    vacuum_pressure_mbar FLOAT,
    status_code VARCHAR
);

-- 2. MES: Batch Execution Records
CREATE TABLE mes_batch_execution (
    batch_id VARCHAR PRIMARY KEY,
    product_name VARCHAR,
    target_units INT,
    actual_units INT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    recipe_version VARCHAR,
    operator_id VARCHAR
);

-- 3. CMMS: Maintenance Work Orders
CREATE TABLE cmms_work_orders (
    work_order_id VARCHAR PRIMARY KEY,
    asset_id VARCHAR,
    failure_mode VARCHAR,
    downtime_minutes INT,
    technician_notes VARCHAR,
    date_resolved TIMESTAMP
);

-- 4. QMS: Past Deviations & CAPAs
CREATE TABLE qms_deviations (
    deviation_id VARCHAR PRIMARY KEY,
    batch_id VARCHAR,
    root_cause_category VARCHAR,
    capa_action VARCHAR,
    status VARCHAR
);

```

## 4. Step-by-Step Implementation Plan

### Phase 1: Data Architecture & Pipeline Foundations (Days 1–3)

* **Step 1.1: UNS Broker Setup**

  * Spin up a free HiveMQ Cloud cluster (up to 100 client connections).

  * Design the ISA-95 topic hierarchy:

    `Global_Ops/Site_01/Aseptic_Packaging/Line_02/Vial_Filler/state`

* **Step 1.2: Synthetic Edge Telemetry Engine**

  * Write a Python script (`edge_simulator.py`) using `paho-mqtt` that streams telemetry for a sterile vial-filling line.

  * Inject deliberate operational anomalies (e.g., capper torque micro-spikes causing jams, or vacuum pressure drops during stoppages).

* **Step 1.3: Relational Data Model (DuckDB)**

  * Initialize an embedded DuckDB file (`manufacturing_data.duckdb`).

  * Populate synthetic historical records for 30 days of production batches, CMMS maintenance history, and equipment failure modes.

### Phase 2: Regulatory Knowledge Base & Vector Ingestion (Days 4–5)

* **Step 2.1: Domain SOP Synthesis**

  * Create 5 realistic, unclassified aseptic filling SOPs in Markdown:

    * `SOP-PRD-101`: Lyophilizer vacuum excursion tolerance limits.

    * `SOP-PRD-102`: Capping torque variance and container-closure integrity standards.

    * `SOP-MNT-204`: Mechanical micro-jam clearance protocol (cleanroom class A/B).

    * `SOP-QMS-301`: Deviation escalation thresholds and batch quarantine protocols.

    * `SOP-QMS-302`: Root Cause Analysis (RCA) 5-Why methodology guidelines.

* **Step 2.2: Vector Store Pipeline**

  * Ingest the SOPs into a local **ChromaDB** collection with text chunking (chunk size: 500 tokens, overlap: 50).

  * Build a retrieval utility function returning verbatim section citations and regulatory bounds.

### Phase 3: LangGraph Agent Engine & Governance Controls (Days 6–8)

* **Step 3.1: Define Graph State**

  * Construct a typed `AgentState` containing: `telemetry_data`, `active_batch`, `anomalies_detected`, `sop_evidence`, `oee_impact`, `supervisor_approved`, and `audit_log`.

* **Step 3.2: Tool Registration**

  * `query_mes_state()`: Extracts active batch ID and target units.

  * `query_historian_trend()`: Performs windowed aggregations on sensor data.

  * `query_cmms_history()`: Cross-checks if current asset failure matches historical patterns.

  * `search_sop_guidelines()`: Performs semantic RAG over ChromaDB.

* **Step 3.3: Implement Human-in-the-Loop Interruption**

  * Use LangGraph's native `interrupt()` pattern.

  * The agent proposes a root-cause hypothesis and drafts a GxP deviation record, but halts execution until the user (supervisor) submits an approval signature.

* **Step 3.4: 21 CFR Part 11 Audit Trail Generator**

  * Output a tamper-evident, deterministic JSON payload logging timestamp, inputs, retrieval sources, prompt hash, and user sign-off credentials.

### Phase 4: Generic Digital Shop-Floor Management UI (Days 9–11)

* **Step 4.1: Top Section - OEE & Financial Impact Bar**

  * Live KPI cards: **Availability (%)**, **Performance (%)**, **Quality (%)**, and aggregate **OEE (%)**.

  * Financial impact counter: Lost production cost calculated dynamically at `$125/minute` of line downtime.

* **Step 4.2: Middle Section - Real-time Line Monitoring & Telemetry**

  * Live-updating chart (Plotly/Streamlit) tracking vacuum pressure and fill speed vs. upper/lower control limits (UCL/LCL).

  * Stoppage alert banner triggering when a simulated anomaly occurs.

* **Step 4.3: Bottom Section - Agent Reasoning Workspace & Sign-Off Modal**

  * Expandable agent trace displaying: *Telemetry Queried* → *Historical Match Found* → *SOP Clause Referenced*.

  * Draft Deviation Form with an interactive "Approve & Sign Electronic Record" button that exports the finalized audit log.

### Phase 5: Packaging, Documentation & Executive Deliverables (Days 12–14)

* **Step 5.1: Cloud Deployment**

  * Push code to a public GitHub repository with a clean layout and automated setup instructions.

  * Deploy the live web application on Streamlit Community Cloud.

* **Step 5.2: Executive Deliverables Deck (6-Slide PDF)**

  * *Slide 1:* Executive Problem Statement (Aseptic line downtime costs and deviation cycle time).

  * *Slide 2:* Event-Driven UNS Architecture (ISA-95 compliant OT/IT design).

  * *Slide 3:* Agentic Orchestration Architecture (LangGraph state machine with human-in-the-loop).

  * *Slide 4:* Quantitative ROI Model (Translating a 3.5% OEE uplift to annual site EBITDA).

  * *Slide 5:* Compliance & GAMP 5 Governance (Audit trail design and verification).

  * *Slide 6:* Live System Links (Live Streamlit app + GitHub repository).

* **Step 5.3: 2-Minute Video Walkthrough**

  * Record a crisp Loom video walking through: Anomaly Trigger → Agent Diagnosis → Supervisor Sign-Off → Financial Impact.

## 5. 14-Day Delivery Timeline

```
Day  1  2  3  4  5  6  7  8  9  10  11  12  13  14
     [---Phase 1---]
                 [--Phase 2--]
                       [---Phase 3---]
                                   [---Phase 4---]
                                               [--Phase 5--]

```

* **Days 1–3 (Data Foundations):** MQTT Broker setup, synthetic telemetry simulator, and DuckDB manufacturing schemas.

* **Days 4–5 (Knowledge Engineering):** GxP SOP drafting, text chunking, and ChromaDB vector indexing.

* **Days 6–8 (Agent Intelligence):** LangGraph state machine, tool bindings, Groq/Llama-3.3 integration, and human-in-the-loop gate.

* **Days 9–11 (Shop-Floor UI):** Streamlit Daily Management dashboard, OEE calculator, and interactive sign-off modal.

* **Days 12–14 (Deliverables & Polish):** Public cloud hosting, GitHub repository documentation, 6-slide executive deck, and 2-minute video recording.

## 6. Target-Specific Outreach Customization

### Outreach Angle for Pfizer (Digital Operations Agentic Lead)

> *"I designed **AsepticOps Copilot** to demonstrate how agentic digital teammates can integrate directly into Tier 1/Tier 2 Daily Management cadences. The solution assists technicians with automated deviation root-cause analysis while maintaining strict 21 CFR Part 11 human-in-the-loop sign-offs and zero automated writes."*

### Outreach Angle for C&F (Manufacturing Solutions Business Consultant)

> *"I built **AsepticOps Copilot** to model the financial and operational impact of digital manufacturing transformations. It features an interactive OEE value model linking asset downtime directly to balance-sheet EBITDA, backed by a phased multi-horizon implementation roadmap."*

### Outreach Angle for Deep Digital Solutions Group (Senior Specialist - Industry 4.0)

> *"I developed **AsepticOps Copilot** as a reference implementation for event-driven Unified Namespace (UNS) architectures. It bridges OT telemetry to enterprise analytical stores using MQTT topic hierarchies, in-process analytical engines, and real-time anomaly detection."*