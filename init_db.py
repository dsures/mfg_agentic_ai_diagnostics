import duckdb

def init_database():
    con = duckdb.connect("plant_data.duckdb")
    print("Initializing DuckDB schema on plant_data.duckdb...")

    # 1. Industrial Telemetry Historian
    con.execute("""
    CREATE TABLE IF NOT EXISTS raw_telemetry (
        recorded_at TIMESTAMP NOT NULL,
        machine_id VARCHAR NOT NULL,
        temp_c DOUBLE NOT NULL,
        speed_cpm DOUBLE NOT NULL,
        error_code INTEGER NOT NULL
    );
    """)

    # 2. CMMS Maintenance History (for Agent RCA grounding)
    con.execute("""
    CREATE TABLE IF NOT EXISTS cmms_history (
        error_code INTEGER PRIMARY KEY,
        failure_mode VARCHAR NOT NULL,
        root_cause VARCHAR NOT NULL,
        resolution VARCHAR NOT NULL
    );
    """)

    # Seed CMMS records if empty
    res = con.execute("SELECT COUNT(*) FROM cmms_history").fetchone()[0]
    if res == 0:
        con.execute("""
        INSERT INTO cmms_history VALUES
        (104, 'Sealing Heat Excursion / Thermocouple Fault', 
              'Thermocouple drift causing false low readings and automatic heater shutoff', 
              'Inspect thermocouple lead B; verify heater band continuity; replace if drift exceeds +/- 3 C');
        """)
        print("[+] Seeded CMMS failure records.")

    # 3. Incident Execution Queue (Decoupled FIFO Buffer)
    con.execute("""
    CREATE TABLE IF NOT EXISTS incident_queue (
        incident_id VARCHAR PRIMARY KEY,
        detected_at TIMESTAMP NOT NULL,
        machine_id VARCHAR NOT NULL,
        error_code INTEGER NOT NULL,
        qualification_reason VARCHAR NOT NULL,
        status VARCHAR DEFAULT 'QUEUED', -- QUEUED, PROCESSING, PENDING_REVIEW, RESOLVED
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. GxP Deviation Records (Persistent Agent Output)
    con.execute("""
    CREATE TABLE IF NOT EXISTS deviation_records (
        deviation_id VARCHAR PRIMARY KEY,
        incident_id VARCHAR,
        generated_at TIMESTAMP NOT NULL,
        machine_id VARCHAR NOT NULL,
        error_code INTEGER NOT NULL,
        deviation_summary TEXT NOT NULL,
        agent_raw_transcript TEXT NOT NULL,
        status VARCHAR DEFAULT 'PENDING_REVIEW' -- PENDING_REVIEW, APPROVED
    );
    """)

    # 5. 21 CFR Part 11 Electronic Signature Ledger
    con.execute("""
    CREATE TABLE IF NOT EXISTS gxp_audit_trail (
        audit_id VARCHAR PRIMARY KEY,
        deviation_id VARCHAR,
        signed_at TIMESTAMP NOT NULL,
        signer_id VARCHAR NOT NULL,
        signer_role VARCHAR NOT NULL,
        signature_meaning VARCHAR NOT NULL,
        record_sha256 VARCHAR NOT NULL
    );
    """)

    con.close()
    print("All plant, queue, and audit tables verified.")

if __name__ == "__main__":
    init_database()