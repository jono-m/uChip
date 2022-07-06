from Data.Rig import Rig
from Data.Chip import Chip


class UIMaster:
    _instance = None

    def __init__(self):
        super().__init__()
        self.rig = Rig()
        self.currentChip = Chip()

    @staticmethod
    def Instance():
        if UIMaster._instance is None:
            UIMaster._instance = UIMaster()
        return UIMaster._instance
