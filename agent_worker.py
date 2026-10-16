import time
import uuid
from datetime import datetime, timezone
import duckdb
from langchain_core.messages import HumanMessage
from agent_engine import app as agent_app

DB_PATH = "plant_data.duckdb"

def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return "\n".join(parts)
    return str(content)

print("[Worker] Diagnostics daemon online. Polling DuckDB queue...")

while True:
    job = None
    try:
        # Context-managed read to avoid DuckDB lock leaks
        with duckdb.connect(DB_PATH) as con:
            job = con.execute("""
                SELECT incident_id, machine_id, error_code, qualification_reason, detected_at
                FROM incident_queue
                WHERE status = 'QUEUED'
                ORDER BY detected_at ASC
                LIMIT 1
            """).fetchone()

            if job:
                incident_id = job[0]
                con.execute("UPDATE incident_queue SET status = 'PROCESSING' WHERE incident_id = ?", [incident_id])

    except Exception as e:
        print(f"[Worker Poll Error] {e}")
        time.sleep(2)
        continue

    if not job:
        time.sleep(1)
        continue

    # Unpack job variables
    incident_id, machine_id, error_code, reason, detected_at = job
    print(f"\n[Worker] Claimed {incident_id} (Code {error_code}) -> Processing")

    try:
        # 1. SANITIZE AND CONSTRUCT PROMPT HERE (INSIDE THE LOOP)
        clean_reason = str(reason).replace("<", "below").replace(">", "above")
        prompt = (
            f"Machine: {machine_id} | Error Code: {error_code} | Trigger: {clean_reason}. "
            f"Query historian, retrieve matching SOP, and compile the root cause and CAPA actions."
        )

        input_data = {
            "messages": [HumanMessage(content=prompt)]
        }

        # 2. Invoke Diagnostic Agent
        output = agent_app.invoke(input_data)
        report_text = extract_text(output["messages"][-1].content)

        # 3. Commit Completed Deviation Record
        dev_id = f"DEV-{str(uuid.uuid4())[:8].upper()}"
        with duckdb.connect(DB_PATH) as con:
            con.execute("""
                INSERT INTO deviation_records 
                (deviation_id, incident_id, generated_at, machine_id, error_code, deviation_summary, agent_raw_transcript, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING_REVIEW')
            """, [
                dev_id,
                incident_id,
                datetime.now(timezone.utc),
                machine_id,
                error_code,
                f"Anomaly on {machine_id} - Error {error_code}: {clean_reason}",
                report_text
            ])
            con.execute("UPDATE incident_queue SET status = 'PENDING_REVIEW' WHERE incident_id = ?", [incident_id])
        print(f"[Worker] Complete: {incident_id} -> {dev_id} (PENDING_REVIEW)")

    except Exception as llm_err:
        print(f"[Worker Error during LLM triage] {llm_err}")
        with duckdb.connect(DB_PATH) as con:
            con.execute("UPDATE incident_queue SET status = 'FAILED' WHERE incident_id = ?", [incident_id])

    time.sleep(1)