import time
import uuid
from datetime import datetime, timezone
import duckdb

con = duckdb.connect("plant_data.duckdb")

def qualify_and_enqueue(machine_id, readings):
    """
    Simulates the qualification gate:
    readings = list of tuples [(temp_c, error_code), ...]
    """
    for temp, err in readings:
        now = datetime.now(timezone.utc)
        con.execute("""
            INSERT INTO raw_telemetry (recorded_at, machine_id, temp_c, speed_cpm, error_code)
            VALUES (?, ?, ?, ?, ?)
        """, [now, machine_id, temp, 0 if err != 0 else 180.0, err])
    
    # Check qualification gate on the batch
    latest_temp, latest_err = readings[-1]
    
    if latest_err == 0:
        return None
    
    # Check 1: Critical Severity (< 100°C)
    if latest_temp < 100.0:
        reason = f"CRITICAL SEVERITY (Temp: {latest_temp}°C < 100°C)"
    # Check 2: Persistence (>= 3 consecutive fault records)
    elif len([e for _, e in readings if e != 0]) >= 3:
        reason = f"SUSTAINED FAULT ({len(readings)} cycles)"
    else:
        print(f"[-] Fault ignored by gate: Transient Noise (only {len(readings)} cycle).")
        return None

    # Enqueue qualified fault
    incident_id = f"INC-{str(uuid.uuid4())[:6].upper()}"
    con.execute("""
        INSERT INTO incident_queue (incident_id, detected_at, machine_id, error_code, qualification_reason, status)
        VALUES (?, ?, ?, ?, ?, 'QUEUED')
    """, [incident_id, datetime.now(timezone.utc), machine_id, latest_err, reason])
    
    print(f"[+] QUALIFIED & ENQUEUED: {incident_id} | Code: {latest_err} | {reason}")
    return incident_id

print("\n--- INITIATING 3-CASE DETERMINISTIC TEST ---")

# CASE 1: 1-second transient spike (104) -> Should NOT enqueue
print("\n[Simulating Case 1] 1-second transient sensor glitch (Error 104, 112°C)...")
qualify_and_enqueue("BLISTER-01", [(112.0, 104)])

time.sleep(1)

# CASE 2: Sustained failure (4 records of Error 104 at 105°C) -> Enqueues as Job 1
print("\n[Simulating Case 2] Sustained temperature excursion (Error 104, 105°C across 4 cycles)...")
case2_id = qualify_and_enqueue("BLISTER-01", [(108.0, 104), (106.0, 104), (105.0, 104), (105.0, 104)])

time.sleep(1)

# CASE 3: Critical thermal failure (-50°C) occurring right behind Case 2 -> Enqueues as Job 2
print("\n[Simulating Case 3] Critical temperature drop (-50°C) firing immediately...")
case3_id = qualify_and_enqueue("BLISTER-01", [(-50.0, 104)])

con.close()
print("\n--- Simulation finished. Check worker terminal & database! ---")