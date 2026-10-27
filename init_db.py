import sqlite3
import os

DB_PATH = "plant_data.db"

def initialize_database():
    print(f"Configuring high-concurrency WAL database: {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enforce WAL mode and 10-second busy timeout for zero-collision concurrency
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout=10000;")

    # 1. Real-Time Packaging Telemetry
    cursor.execute("DROP TABLE IF EXISTS packaging_telemetry;")
    cursor.execute("""
    CREATE TABLE packaging_telemetry (
        recorded_at TEXT NOT NULL,
        line_id TEXT NOT NULL,
        vial_counter INTEGER NOT NULL,
        planned_vials INTEGER NOT NULL,
        line_speed_vpm REAL NOT NULL,
        changeover_active INTEGER NOT NULL,
        changeover_duration_min REAL NOT NULL,
        alarm_code INTEGER NOT NULL
    );
    """)

    # 2. Local Incident Queue
    cursor.execute("DROP TABLE IF EXISTS local_incident_queue;")
    cursor.execute("""
    CREATE TABLE local_incident_queue (
        incident_id TEXT PRIMARY KEY,
        detected_at TEXT NOT NULL,
        line_id TEXT NOT NULL,
        alarm_code INTEGER NOT NULL,
        qualification_reason TEXT NOT NULL,
        vial_count_snapshot INTEGER NOT NULL,
        status TEXT NOT NULL
    );
    """)

    # 3. Deviation Records (AI Investigation Storage)
    cursor.execute("DROP TABLE IF EXISTS deviation_records;")
    cursor.execute("""
    CREATE TABLE deviation_records (
        deviation_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        line_id TEXT NOT NULL,
        alarm_code INTEGER NOT NULL,
        deviation_summary TEXT NOT NULL,
        agent_raw_transcript TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """)

    # 4. 21 CFR Part 11 Electronic Signature Audit Trail
    cursor.execute("DROP TABLE IF EXISTS gxp_audit_trail;")
    cursor.execute("""
    CREATE TABLE gxp_audit_trail (
        audit_id TEXT PRIMARY KEY,
        deviation_id TEXT NOT NULL,
        signed_at TEXT NOT NULL,
        signer_name TEXT NOT NULL,
        signer_role TEXT NOT NULL,
        signature_intent TEXT NOT NULL,
        sha256_checksum TEXT NOT NULL
    );
    """)

    # 5. CMMS Maintenance & Failure Mode History
    cursor.execute("DROP TABLE IF EXISTS cmms_history;")
    cursor.execute("""
    CREATE TABLE cmms_history (
        record_id TEXT PRIMARY KEY,
        alarm_code INTEGER NOT NULL,
        subsystem TEXT NOT NULL,
        historical_root_cause TEXT NOT NULL,
        recommended_action TEXT NOT NULL
    );
    """)

    # Seed failure modes
    cursor.executemany("""
    INSERT INTO cmms_history VALUES (?, ?, ?, ?, ?)
    """, [
        ('CMMS-301', 301, 'Vision Inspection & Labeler', 'High-speed camera strobe light misalignment or optical lens fogging causing false OCR rejections on 2D DataMatrix/Lot codes.', 'Clean camera optical lens with lint-free alcohol wipe, re-zero focal distance calibration target, and perform 10-vial test challenge.'),
        ('CMMS-302', 302, 'Vial Crimp & Sealing Station', 'Pneumatic crimp-head pressure drop below 4.5 bar or worn aluminum tear-off skirt crimping knife edge causing loose closures.', 'Inspect pneumatic pressure regulator line, check crimping spring tension gauge, and execute container closure integrity (CCI) gauge check on 5 consecutive samples.'),
        ('CMMS-303', 303, 'Format Tooling & Starwheel', 'Guide rail binding or mechanical pocket spacing misalignment when changing from 2 mL to 10 mL changeover pucks exceeding 45-min SOP limit.', 'Verify torque tolerance on guide rail hand knobs, lubricate starwheel indexing drive spline, and inspect rail levelers using digital gauge.'),
        ('CMMS-304', 304, 'Cartoner Infeed & Blister Pusher', 'Push-rod mechanical safety slip clutch triggered due to bent carton flap obstruction in carton magazine throat.', 'De-energize machine, clear jammed carton stock, inspect push-rod timing sensor alignment, and execute complete line clearance before resetting safety clutch.')
    ])

    conn.commit()
    conn.close()
    print("✅ All tables cleanly created in plant_data.db with WAL mode enabled.")

if __name__ == "__main__":
    initialize_database()