"""Convenience entry point. Run with: python run.py"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from guandan.main import main

if __name__ == "__main__":
    main()
