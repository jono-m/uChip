"""Runs uChip. Usage: python uChip.py [project.uchip]"""
import sys
from pathlib import Path

from gui.app import run

DEFAULT_CHIP = Path("examples/PluriDrop.uchip")

if __name__ == '__main__':
    sys.exit(run(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CHIP))
