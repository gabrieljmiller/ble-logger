import asyncio
import requests
from bleak import BleakScanner
from datetime import datetime
import time
from dotenv import load_dotenv
import os
import csv

# Load environment variables from .env file
load_dotenv()

LOGFILE = "ble_log.csv"
SCAN_INTERVAL = 300  # seconds (5 min)

def load_known_devices(filename):
    known = {}
    try:
        with open(filename, newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:
                    mac, tag = row
                    known[mac.strip().upper()] = tag.strip()
    except FileNotFoundError:
        print(f"File {filename} not found. Using empty known devices list.")
    return known

def send_telegram(message):
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

KNOWN_DEVICES = load_known_devices("known_devices.csv")

async def scan_ble():
    devices = await BleakScanner.discover()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOGFILE, "a") as f:
        for d in devices:
            mac = d.address.upper()
            name = d.name if d.name else "Unknown"
            rssi = d.rssi
            tag = KNOWN_DEVICES.get(mac, "Unknown")
            metadata = d.metadata if hasattr(d, "metadata") else {}

            # Attempt to log metadata details
            details = "; ".join(f"{k}={v}" for k, v in metadata.items())

            f.write(f"{now},{mac},{name},{rssi},{tag},{details}\n")

    print(f"[{now}] Logged {len(devices)} devices.")

# Infinite scan loop
while True:
    try:
        asyncio.run(scan_ble())
        time.sleep(SCAN_INTERVAL)
    except Exception as e:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] Error: {e}")
        time.sleep(60)
