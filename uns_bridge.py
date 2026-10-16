import json
import time
import threading
from collections import deque
import duckdb
import paho.mqtt.client as mqtt

BUFFER = deque()
BUFFER_LOCK = threading.Lock()
DB_FILE = "plant_data.duckdb"
TOPIC = "pharma/line1/telemetry"

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        record = (
            data["recorded_at"],
            data["machine_id"],
            data["temp_c"],
            data["speed_cpm"],
            data["error_code"]
        )
        with BUFFER_LOCK:
            BUFFER.append(record)
    except Exception as err:
        print(f"Parse error: {err}")

def flush_to_duckdb():
    while True:
        time.sleep(2.0)
        with BUFFER_LOCK:
            if not BUFFER:
                continue
            batch = list(BUFFER)
            BUFFER.clear()

        # Open connection, insert, and close immediately to release the lock
        try:
            con = duckdb.connect(DB_FILE, read_only=False)
            con.executemany("INSERT INTO raw_telemetry VALUES (?, ?, ?, ?, ?)", batch)
            con.close()
            print(f"[Bridge] Committed {len(batch)} records to DuckDB.")
        except Exception as err:
            print(f"[Bridge Error] DB insert failure: {err}")

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect("127.0.0.1", 1883, 60)
    client.subscribe(TOPIC)

    # Start background batch flusher
    threading.Thread(target=flush_to_duckdb, daemon=True).start()

    print(f"Bridge listening on '{TOPIC}'...")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nBridge stopped.")
        client.disconnect()

if __name__ == "__main__":
    main()