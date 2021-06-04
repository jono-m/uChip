from Model.Rig.Rig import Rig
from Model.Chip import Chip
from Model.Program.ProgramRunner import ProgramRunner
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
        self.programRunner = ProgramRunner()
        self.programRunner.rig = self.rig
        self.chip = None
        self.onChipModified.connect(lambda: AppGlobals.Chip().Validate())

    onChipOpened = Signal()  # Invoked whenever a new chip is opened
    onChipModified = Signal()  # Invoked whenever the chip lists change

    @staticmethod
    def Rig() -> Rig:
        return AppGlobals.Instance().rig

    @staticmethod
    def OpenChip(chip: Chip):
        AppGlobals.Instance().chip = chip
        AppGlobals.Instance().onChipOpened.emit()
        AppGlobals.Instance().programRunner.chip = chip

    @staticmethod
    def ProgramRunner() -> ProgramRunner:
        return AppGlobals.Instance().programRunner

    @staticmethod
    def Chip() -> Chip:
        return AppGlobals.Instance().chip
