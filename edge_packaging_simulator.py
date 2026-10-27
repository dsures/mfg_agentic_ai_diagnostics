import time
import uuid
import random
import sqlite3
from datetime import datetime, timezone

DB_PATH = "plant_data.db"
LINE_ID = "VIAL-PKG-01"
PLANNED_SHIFT_VIALS = 20000

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def enqueue_incident(alarm_code: int, reason: str, vial_snapshot: int):
    incident_id = f"INC-{str(uuid.uuid4())[:6].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO local_incident_queue 
            (incident_id, detected_at, line_id, alarm_code, qualification_reason, vial_count_snapshot, status)
            VALUES (?, ?, ?, ?, ?, ?, 'QUEUED')
        """, (incident_id, now_iso, LINE_ID, alarm_code, reason, vial_snapshot))
        conn.commit()
        
    print(f"\n🚨 [GxP Gate] Enqueued Incident: {incident_id} | Alarm: {alarm_code} | Reason: {reason}\n")

print(f"🏭 Packaging Telemetry Simulator Online: {LINE_ID}")
print(f"Shift Target: {PLANNED_SHIFT_VIALS:,} vials | Nominal Speed: 120 VPM")
print("Press Ctrl+C to terminate.\n")

current_vials = 13850
nominal_speed_vpm = 120.0
changeover_active = False
changeover_start_time = None
cycle = 0

try:
    while True:
        cycle += 1
        now_iso = datetime.now(timezone.utc).isoformat()
        alarm_code = 0
        speed = nominal_speed_vpm + random.uniform(-2.0, 2.0)
        changeover_duration_min = 0.0

        if not changeover_active:
            current_vials += 2
            if cycle == 10:
                alarm_code = 301
                speed = 0.0
                reason = "Vision OCR camera rejected 3 consecutive vials on 2D DataMatrix/Lot verification."
                enqueue_incident(alarm_code, reason, current_vials)
            elif cycle == 25:
                changeover_active = True
                changeover_start_time = time.time()
                print("🔄 [Operator Action] Batch Changeover initiated (2 mL -> 10 mL pucks).")
        else:
            speed = 0.0
            elapsed_sec = time.time() - changeover_start_time
            changeover_duration_min = round(elapsed_sec * 5.0, 1)

            if changeover_duration_min > 45.0 and cycle == 35:
                alarm_code = 303
                reason = f"Changeover duration ({changeover_duration_min} min) exceeded 45-min SOP limit."
                enqueue_incident(alarm_code, reason, current_vials)

            if cycle >= 40:
                changeover_active = False
                print(f"✅ [Operator Action] Changeover completed in {changeover_duration_min} min.")

        with get_connection() as conn:
            conn.execute("""
                INSERT INTO packaging_telemetry 
                (recorded_at, line_id, vial_counter, planned_vials, line_speed_vpm, changeover_active, changeover_duration_min, alarm_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now_iso, LINE_ID, current_vials, PLANNED_SHIFT_VIALS, speed, 1 if changeover_active else 0, changeover_duration_min, alarm_code))
            conn.commit()

        state_str = "CHANGEOVER" if changeover_active else ("FAULT" if alarm_code != 0 else "RUNNING")
        print(f"[{now_iso[11:19]}] {LINE_ID} | State: {state_str:<10} | Vials: {current_vials}/{PLANNED_SHIFT_VIALS} | Speed: {speed:.1f} VPM | Alarm: {alarm_code}")

        time.sleep(1.0)

except KeyboardInterrupt:
    print("\nSimulator stopped.")