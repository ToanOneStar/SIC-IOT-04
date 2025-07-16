import requests
import time
import subprocess

esp32_ip = "192.168.1.6"
PROGRAM = "main.py"
def is_esp32_ready():
    try:
        r = requests.get(f"http://{esp32_ip}/status", timeout=1)
        return r.status_code == 200
    except:
        return False

# Chờ đến khi ESP32 online
while not is_esp32_ready():
    print("Waiting for ESP32...")
    time.sleep(2)

print("ESP32 is online. Starting monitor...")
subprocess.Popen(['python', PROGRAM])  # chạy chương trình chính
