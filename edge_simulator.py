import json
import time
import random
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
TOPIC = "pharma/line1/telemetry"

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    print(f"Connected to MQTT broker. Streaming to '{TOPIC}'...")

    cycle = 0
    try:
        while True:
            cycle += 1
            temp = round(random.normalvariate(125.0, 1.0), 2)
            speed = round(random.normalvariate(180.0, 2.0), 1)
            error_code = 0

            # Deterministic fault trigger after cycle 15
            if cycle > 15:
                temp = round(125.0 - (cycle - 15) * 3.0, 2)
                speed = max(0.0, round(180.0 - (cycle - 15) * 15.0, 1))
                if temp < 110.0:
                    error_code = 104  # Heat excursion fault

            payload = {
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "machine_id": "BLISTER-01",
                "temp_c": temp,
                "speed_cpm": speed,
                "error_code": error_code
            }

            client.publish(TOPIC, json.dumps(payload))
            print(f"[Cycle {cycle:02d}] Temp: {temp}°C | Speed: {speed} cpm | Error: {error_code}")
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\nSimulator stopped.")
        client.disconnect()

if __name__ == "__main__":
    main()