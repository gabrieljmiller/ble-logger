import asyncio
from bleak import BleakScanner
from datetime import datetime
import time

LOGFILE = "ble_log.csv"
SCAN_INTERVAL = 300  # seconds between scans (5 minutes)

async def scan_ble():
    devices = await BleakScanner.discover()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGFILE, "a") as f:
        for d in devices:
            f.write(f"{now},{d.address},{d.name or 'Unknown'},{d.rssi}\n")
    print(f"[{now}] Logged {len(devices)} devices.")

while True:
    try:
        asyncio.run(scan_ble())
        time.sleep(SCAN_INTERVAL)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)
