import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    service = Path(__file__).parent / "service.py"
    if service.exists():
        subprocess.Popen(
            [sys.executable, str(service)],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    try:
        while True:
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        while True:
            time.sleep(60)