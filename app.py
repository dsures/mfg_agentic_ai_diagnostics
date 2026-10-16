import streamlit as st
import duckdb
import pandas as pd
import hashlib
import uuid
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="AsepticOps Copilot | Diagnostic Queue",
    page_icon="🏭",
    layout="wide"
)

# 1. Fetch System State
def fetch_system_state():
    try:
        con = duckdb.connect("plant_data.duckdb", read_only=True)
        latest = con.execute("""
            SELECT recorded_at, machine_id, temp_c, speed_cpm, error_code 
            FROM raw_telemetry 
            ORDER BY recorded_at DESC 
            LIMIT 1
        """).fetchone()

        oee_df = con.execute("SELECT temp_c, speed_cpm, error_code FROM raw_telemetry").fetchdf()

        queue_df = con.execute("""
            SELECT incident_id, detected_at, machine_id, error_code, qualification_reason, status 
            FROM incident_queue 
            ORDER BY detected_at DESC
        """).fetchdf()

        processing_job = con.execute("""
            SELECT incident_id, machine_id, error_code, qualification_reason, detected_at 
            FROM incident_queue 
            WHERE status = 'PROCESSING' 
            ORDER BY detected_at ASC 
            LIMIT 1
        """).fetchone()

        pending_dev = con.execute("""
            SELECT deviation_id, incident_id, generated_at, machine_id, error_code, deviation_summary, agent_raw_transcript 
            FROM deviation_records 
            WHERE status = 'PENDING_REVIEW' 
            ORDER BY generated_at ASC 
            LIMIT 1
        """).fetchone()

        con.close()
        return latest, oee_df, queue_df, processing_job, pending_dev
    except Exception:
        return None, pd.DataFrame(), pd.DataFrame(), None, None

latest_row, oee_data, queue_data, active_job, active_deviation = fetch_system_state()

# Auto-refresh runs continuously to track queue updates
# Pauses only when supervisor is actively viewing a report waiting for sign-off
if active_deviation is None:
    st_autorefresh(interval=2000, key="historian_poll")

# 2. Header & Metrics
st.title("🏭 AsepticOps Copilot")
st.caption("Shop-Floor Diagnostics | Persistent Incident Queue | 21 CFR Part 11 Electronic Ledger")

def calculate_oee(df: pd.DataFrame):
    if df.empty:
        return 0.0, 0.0, 0.0, 0.0
    total = len(df)
    operating = (df["error_code"] == 0).sum()
    availability = operating / total if total > 0 else 0.0
    speeds = df[df["error_code"] == 0]["speed_cpm"]
    avg_speed = speeds.mean() if not speeds.empty else 0.0
    performance = min(1.0, avg_speed / 180.0)
    quality = ((df["temp_c"] >= 110.0).sum()) / total if total > 0 else 0.0
    return availability * performance * quality * 100, availability * 100, performance * 100, quality * 100

oee_val, avail_val, perf_val, qual_val = calculate_oee(oee_data)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Overall OEE", f"{oee_val:.1f} %")
m2.metric("Availability", f"{avail_val:.1f} %")
m3.metric("Performance", f"{perf_val:.1f} %")
m4.metric("Quality", f"{qual_val:.1f} %")

st.divider()

# 3. Telemetry Snapshot
t1, t2, t3, t4 = st.columns(4)
if latest_row:
    rec_time, machine_id, temp_c, speed_cpm, err_code = latest_row
    t1.metric("Asset ID", machine_id)
    t2.metric("Seal Temperature", f"{temp_c:.1f} °C", delta=f"{temp_c - 125.0:.1f} °C vs Spec", delta_color="normal" if temp_c >= 110 else "inverse")
    t3.metric("Line Speed", f"{speed_cpm:.1f} cpm")
    t4.metric("Asset State", "NORMAL" if err_code == 0 else f"FAULT ({err_code})")
else:
    st.info("No telemetry records detected.")

st.divider()

# 4. Active Investigation Banner
if active_job:
    job_id, j_mach, j_err, j_reason, j_time = active_job
    with st.container(border=True):
        st.markdown(f"#### ⚙️ Agent Currently Triaging: `{job_id}`")
        st.write(f"🔄 **Status:** LLM Reasoning In Progress... | **Asset:** `{j_mach}` | **Fault Code:** `{j_err}` | **Reason:** {j_reason}")

# 5. Incident Queue Table with Status Icons
st.subheader("📋 Incident Backlog & Execution Queue")
if not queue_data.empty:
    status_icon_map = {
        "PROCESSING": "⚙️ RUNNING",
        "QUEUED": "⏳ IN QUEUE",
        "PENDING_REVIEW": "📝 AWAITING SIGN-OFF",
        "RESOLVED": "✅ COMPLETED",
        "FAILED": "❌ FAILED"
    }
    display_df = queue_data.copy()
    display_df["status"] = display_df["status"].map(lambda s: status_icon_map.get(s, s))

    st.dataframe(
        display_df,
        column_config={
            "incident_id": "Incident ID",
            "detected_at": "Timestamp",
            "machine_id": "Asset",
            "error_code": "Fault Code",
            "qualification_reason": "Trigger Qualification",
            "status": "Queue State"
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("Queue is empty. Waiting for fault triggers.")

# 6. GxP Deviation Report Review (Where the LLM Output Shows)
if active_deviation:
    dev_id, inc_id, gen_time, mach_id, err, summary, transcript = active_deviation
    st.divider()
    st.subheader(f"📋 GxP Deviation Review: {dev_id}")
    st.warning(f"⚠️ **Review Required:** Anomaly on asset `{mach_id}` (Reference Incident: `{inc_id}`)")

    # Dynamic LLM Report Output Container
    with st.container(border=True):
        st.markdown("### 📄 Root Cause & Deviation Analysis (LLM Output)")
        st.markdown(transcript)

    # 21 CFR Part 11 Electronic Signature Box
    with st.container(border=True):
        st.markdown("### ✍️ Supervisor Electronic Sign-Off")
        c1, c2 = st.columns(2)
        with c1:
            signer_name = st.text_input("Approver Identity", value="Darvin Sureskumar")
            signer_role = st.selectbox("Designation", ["Lead Systems Engineer", "Quality Assurance Lead", "Shift Automation Engineer"])
        with c2:
            intent = st.selectbox("Signature Intent", [
                "I authorize diagnostic conclusions and confirm containment",
                "I approve CAPA actions and release line for maintenance",
                "Investigation rejected - Physical inspection required"
            ])
            certify = st.checkbox("I verify that the above entries are accurate and legally binding.", value=True)

        if st.button("🔒 Authorize & Digitally Sign Deviation", type="primary", use_container_width=True):
            if certify:
                sign_timestamp = datetime.now(timezone.utc).isoformat()
                record_payload = f"{dev_id}|{inc_id}|{transcript}|{signer_name}|{sign_timestamp}"
                sha_hash = hashlib.sha256(record_payload.encode()).hexdigest()

                con = duckdb.connect("plant_data.duckdb")
                con.execute("""
                    INSERT INTO gxp_audit_trail VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [str(uuid.uuid4())[:8], dev_id, sign_timestamp, signer_name, signer_role, intent, sha_hash])

                con.execute("UPDATE deviation_records SET status = 'APPROVED' WHERE deviation_id = ?", [dev_id])
                con.execute("UPDATE incident_queue SET status = 'RESOLVED' WHERE incident_id = ?", [inc_id])
                con.close()

                st.success(f"Deviation {dev_id} signed and archived. Loading next case...")
                st.rerun()
            else:
                st.warning("Please check the verification box to sign.")