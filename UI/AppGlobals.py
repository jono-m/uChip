from Model.Rig.Rig import Rig
from Model.Chip import Chip
from PySide6.QtCore import QObject, Signal


class AppGlobals(QObject):
    _instance = None

    @staticmethod
    def Instance():
        if not AppGlobals._instance:
            AppGlobals._instance = AppGlobals()
        return AppGlobals._instance

    def __init__(self):
        super().__init__()
        self.rig = Rig()
        self.chip = None

    chipOpened = Signal(Chip)

    @staticmethod
    def Rig():
        return AppGlobals.Instance().rig

    @staticmethod
    def OpenChip(chip: Chip):
        AppGlobals.Instance().chip = chip
        AppGlobals.Instance().chipOpened.emit(chip)

    @staticmethod
    def onChipOpened():
        return AppGlobals.Instance().chipOpened

    @staticmethod
    def Chip():
        return AppGlobals.Instance().chip
