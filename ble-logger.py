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

def ensure_csv_headers(filename, headers):
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

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

def load_unknown_devices(filename):
    unknown = set()
    try:
        with open(filename, newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:
                    unknown.add(row[0].strip().upper())
    except FileNotFoundError:
        open(filename, "w").close()  # Create the file if it doesn't exist
    return unknown

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
    UNKNOWN_FILE = "unknown_devices.csv"
    unknown_devices = load_unknown_devices(UNKNOWN_FILE)

    ensure_csv_headers(LOGFILE, ["Timestamp", "MAC", "Name", "RSSI", "Tag", "Metadata"])
    ensure_csv_headers(UNKNOWN_FILE, ["MAC", "Name"])
    
    devices = await BleakScanner.discover()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    UNKNOWN_FILE = "unknown_devices.csv"
    unknown_devices = load_unknown_devices(UNKNOWN_FILE)

    with open(LOGFILE, "a") as f:
        for d in devices:
            mac = d.address.upper()
            name = d.name if d.name else "Unknown"
            rssi = d.rssi
            tag = KNOWN_DEVICES.get(mac, "Unknown")
            metadata = d.metadata if hasattr(d, "metadata") else {}

            details = "; ".join(f"{k}={v}" for k, v in metadata.items())

            f.write(f"{now},{mac},{name},{rssi},{tag},{details}\n")

            if tag == "Unknown" and mac not in unknown_devices:
                with open(UNKNOWN_FILE, "a") as uf:
                    uf.write(f"{mac},{name}\n")
                unknown_devices.add(mac)

    print(f"[{now}] Logged {len(devices)} devices.")


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
