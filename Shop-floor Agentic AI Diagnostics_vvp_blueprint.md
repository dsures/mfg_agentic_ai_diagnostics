# Project Blueprint: Local-First Shop-Floor Agentic AI Diagnostics

## Executive Summary

This project delivers a local-first, edge-deployed diagnostic platform for high-consequence, regulated pharmaceutical manufacturing (such as sterile fill-finish and high-speed packaging lines).

By operating entirely within the local plant network boundary, the system connects shop-floor operational telemetry directly to an autonomous background AI agent and an operator-centric supervisory portal. This architecture eliminates cloud API latency, protects proprietary manufacturing telemetry inside the firewall, and enforces strict GxP and 21 CFR Part 11 compliance without complex external infrastructure.

---

## Strategic Value & Operational Impact

- **Unified Operator Interface:** Eliminates software fragmentation by giving operators a single view of real-time line health and contextualized incident data.
- **Lower Cognitive Load:** Lets technicians focus on fixing physical equipment rather than context-switching between disconnected software systems during downtime.
- **Streamlined GxP Compliance:** Eliminates manual paper trails and vendor cloud validation overhead with self-contained, cryptographically signed electronic records.

---

## Core Technical Architecture & Capabilities

### Step 1: High-Frequency Telemetry & WAL Concurrency
- **Implementation:** Streams 1 Hz sensor data, vial throughput, and PLC alarm codes into a local SQLite database operating in Write-Ahead Logging (WAL) mode.
- **Operational Impact:** Simulates real-time plant telemetry while enabling multi-process reads and writes simultaneously without database lockups or system freezing.

### Step 2: Asynchronous Agentic RCA Worker (Qwen-27B)
- **Implementation:** Runs a background AI worker that continuously polls incident queues, cross-references historical CMMS maintenance records, and programmatically synthesizes structured Root Cause Analysis (RCA) draft reports.
- **Operational Impact:** Automates repetitive data-gathering tasks and slashes incident investigation triage time from hours of manual searching down to seconds.

### Step 3: Supervisory Dashboard & Cryptographic 21 CFR Part 11 Audit Vault
- **Implementation:** Renders a clean Streamlit interface for live monitoring and QA review, executing role-authenticated electronic sign-offs that generate tamper-proof SHA-256 WORM (Write-Once-Read-Many) manifests.
- **Operational Impact:** Delivers immediate visual clarity for operators while providing an audit-ready, tamper-proof electronic log vault for regulatory compliance.

---


1. **Telemetry & Alarm Ingestion**
   ```bash
   python simulator.py
