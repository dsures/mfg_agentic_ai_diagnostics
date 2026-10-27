import os
import json
import hashlib
import sqlite3
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

DB_PATH = "plant_data.db"
AUDIT_VAULT_DIR = "audit_vault"
LINE_ID = "VIAL-PKG-01"
PLANNED_SHIFT_VIALS = 20000

os.makedirs(AUDIT_VAULT_DIR, exist_ok=True)

st.set_page_config(page_title="GxP Packaging Monitor & Sign-Off", layout="wide")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def load_latest_telemetry(limit: int = 60):
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT recorded_at, vial_counter, planned_vials, line_speed_vpm, changeover_active, changeover_duration_min, alarm_code
            FROM packaging_telemetry
            WHERE line_id = ?
            ORDER BY recorded_at DESC
            LIMIT ?
        """, conn, params=(LINE_ID, limit))

def load_pending_deviations():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT deviation_id, incident_id, generated_at, line_id, alarm_code, deviation_summary, agent_raw_transcript, status
            FROM deviation_records
            WHERE status = 'PENDING_REVIEW'
            ORDER BY generated_at DESC
        """, conn)

def load_audit_trail():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT audit_id, deviation_id, signed_at, signer_name, signer_role, signature_intent, sha256_checksum
            FROM gxp_audit_trail
            ORDER BY signed_at DESC
        """, conn)

def sign_and_approve_deviation(dev_id: str, transcript: str, name: str, role: str, intent: str):
    now_iso = datetime.now(timezone.utc).isoformat()
    audit_id = f"AUDIT-{int(datetime.now(timezone.utc).timestamp())}"

    manifest_data = {
        "audit_id": audit_id,
        "deviation_id": dev_id,
        "timestamp_utc": now_iso,
        "signer_name": name,
        "signer_role": role,
        "signature_intent": intent,
        "content_body": transcript
    }
    raw_payload = json.dumps(manifest_data, sort_keys=True)
    sha256_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    manifest_data["sha256_checksum"] = sha256_hash

    with get_connection() as conn:
        conn.execute("UPDATE deviation_records SET status = 'APPROVED' WHERE deviation_id = ?", (dev_id,))
        conn.execute("""
            INSERT INTO gxp_audit_trail
            (audit_id, deviation_id, signed_at, signer_name, signer_role, signature_intent, sha256_checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (audit_id, dev_id, now_iso, name, role, intent, sha256_hash))
        conn.commit()

    manifest_filepath = os.path.join(AUDIT_VAULT_DIR, f"{audit_id}_{dev_id}.json")
    with open(manifest_filepath, "w") as f:
        json.dump(manifest_data, f, indent=4)

    return audit_id, sha256_hash, manifest_filepath

st.title("🏭 Sterile Vial Packaging — Supervisory & QA Portal")
st.caption(f"Line Asset: **{LINE_ID}** | Validated Shift Target: **{PLANNED_SHIFT_VIALS:,} vials**")

# Sidebar Controls
st.sidebar.header("Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh Dashboard (5s)", value=True)

# Define auto-refreshing telemetry block using st.fragment
@st.fragment(run_every=5 if auto_refresh else None)
def render_live_telemetry():
    st.subheader("📡 Live Line Telemetry")
    telemetry_df = load_latest_telemetry(60)

    if not telemetry_df.empty:
        latest = telemetry_df.iloc[0]
        vial_cnt = int(latest["vial_counter"])
        planned = int(latest["planned_vials"])
        speed = float(latest["line_speed_vpm"])
        is_changeover = bool(latest["changeover_active"])
        changeover_dur = float(latest["changeover_duration_min"])
        alarm = int(latest["alarm_code"])

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Current Yield", f"{vial_cnt:,} / {planned:,}", f"{round((vial_cnt/planned)*100, 1)}% Target")
        k2.metric("Line Speed", f"{speed:.1f} VPM", "Nominal 120 VPM")
        k3.metric("Changeover Timer", f"{changeover_dur:.1f} min" if is_changeover else "RUNNING", "Max 45 min" if is_changeover else "Normal")
        k4.metric("Operational Status", "NORMAL" if alarm == 0 else f"ALARM {alarm}", "Fault" if alarm != 0 else "Clear")

        pct_complete = min(1.0, max(0.0, vial_cnt / planned))
        st.progress(pct_complete, text=f"Shift Batch Completion: {round(pct_complete * 100, 1)}%")

        st.subheader("Line Speed History (Last 60s)")
        chart_df = telemetry_df[["recorded_at", "line_speed_vpm"]].sort_values("recorded_at")
        st.line_chart(chart_df.set_index("recorded_at"))
    else:
        st.info("Awaiting telemetry stream. Ensure edge_packaging_simulator.py is running.")

render_live_telemetry()

st.divider()

st.subheader("📋 Pending AI Deviation & CAPA Investigations")
pending_devs = load_pending_deviations()

if pending_devs.empty:
    st.success("No pending deviations requiring QA review.")
else:
    for idx, row in pending_devs.iterrows():
        dev_id = row["deviation_id"]
        inc_id = row["incident_id"]
        alarm_code = row["alarm_code"]
        summary = row["deviation_summary"]
        transcript = row["agent_raw_transcript"]

        with st.expander(f"⚠️ {dev_id} | Incident {inc_id} | Alarm {alarm_code} — {summary}", expanded=True):
            st.markdown(transcript)
            
            with st.form(key=f"sign_form_{dev_id}"):
                c1, c2 = st.columns(2)
                signer_name = c1.text_input("Signer Full Name", value="Darvin Sureskumar")
                signer_role = c1.selectbox("Role", ["Quality Assurance Lead", "Packaging Operations Supervisor", "Qualified Person (QP)"])
                signer_intent = c2.selectbox("Signature Intent", [
                    "I approve the root cause analysis and immediate containment actions.",
                    "I confirm batch disposition and authorized CAPA implementation."
                ])
                password_confirm = c2.text_input("Credential / PIN", type="password")
                
                submitted = st.form_submit_button("Electronically Sign & Authorize (SHA-256)")
                if submitted:
                    if not password_confirm:
                        st.error("PIN authentication required.")
                    else:
                        audit_id, digest, filepath = sign_and_approve_deviation(
                            dev_id, transcript, signer_name, signer_role, signer_intent
                        )
                        st.success(f"Authorized: {audit_id}")
                        st.code(f"SHA-256: {digest}\nVault: {filepath}", language="text")
                        st.rerun()

st.divider()
st.subheader("🔒 Immutable GxP Audit Trail Ledger")
audit_df = load_audit_trail()
if not audit_df.empty:
    st.dataframe(audit_df, use_container_width=True)
else:
    st.write("No electronic signatures committed yet.")