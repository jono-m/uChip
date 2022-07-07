from Data.Rig import Rig
from Data.Chip import Chip
from typing import Optional
from pathlib import Path


class UIMaster:
    _instance = None

    def __init__(self):
        super().__init__()
        self.rig = Rig()
        self.currentChip = Chip()
        self.modified = False
        self.currentChipPath: Optional[Path] = None

    @staticmethod
    def Instance():
        if UIMaster._instance is None:
            UIMaster._instance = UIMaster()
        return UIMaster._instance
