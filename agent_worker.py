import time
import uuid
import sqlite3
from datetime import datetime, timezone
from agent_engine import run_diagnostic_agent

DB_PATH = "plant_data.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def claim_next_incident() -> dict:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT incident_id, detected_at, line_id, alarm_code, qualification_reason, vial_count_snapshot
            FROM local_incident_queue
            WHERE status = 'QUEUED'
            ORDER BY detected_at ASC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            return None
        
        incident = dict(row)
        cursor.execute("UPDATE local_incident_queue SET status = 'PROCESSING' WHERE incident_id = ?", (incident["incident_id"],))
        conn.commit()
        return incident

def save_deviation(incident: dict, diagnostic_output: dict):
    dev_id = f"DEV-{str(uuid.uuid4())[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO deviation_records 
            (deviation_id, incident_id, generated_at, line_id, alarm_code, deviation_summary, agent_raw_transcript, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING_REVIEW')
        """, (
            dev_id,
            incident["incident_id"],
            now_iso,
            incident["line_id"],
            incident["alarm_code"],
            diagnostic_output["deviation_summary"],
            diagnostic_output["agent_raw_transcript"]
        ))
        conn.commit()
    return dev_id

def update_queue_status(incident_id: str, new_status: str):
    with get_connection() as conn:
        conn.execute("UPDATE local_incident_queue SET status = ? WHERE incident_id = ?", (new_status, incident_id))
        conn.commit()

def run_worker():
    print("🤖 AI Diagnostic Worker Daemon Online (SQLite WAL)...")
    while True:
        try:
            incident = claim_next_incident()
            if incident:
                inc_id = incident["incident_id"]
                alarm = incident["alarm_code"]
                print(f"⚡ [Ingestion] Processing Incident: {inc_id} (Alarm Code: {alarm})...")
                
                try:
                    diagnostic = run_diagnostic_agent(incident)
                    dev_id = save_deviation(incident, diagnostic)
                    update_queue_status(inc_id, "PENDING_REVIEW")
                    print(f"✅ [Triage Complete] Created {dev_id} for {inc_id}")
                except Exception as inner_e:
                    print(f"❌ [Error] Failed processing {inc_id}: {inner_e}")
                    update_queue_status(inc_id, "FAILED")
            
            time.sleep(2.0)
        except KeyboardInterrupt:
            print("\nWorker terminated.")
            break
        except Exception as e:
            print(f"⚠️ [Worker Loop Exception]: {e}")
            time.sleep(3.0)

if __name__ == "__main__":
    run_worker()