"""Compatibility entrypoint for Opus; use python -m atlas for new automation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from atlas.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main(['build', '--topic', 'opus-5-5', '--render-card'] + sys.argv[1:]))
