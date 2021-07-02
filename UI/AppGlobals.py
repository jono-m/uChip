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
        self.programRunner.onValveChange.connect(self.onValveChanged.emit)
        self.programRunner.rig = self.rig
        self.chip = None
        self.onChipModified.connect(lambda: AppGlobals.Chip().Validate())
        self.onChipModified.connect(self.onChipDataModified.emit)
        self.onChipModified.connect(self.programRunner.CheckPrograms)

    onChipOpened = Signal()  # Invoked whenever a new chip is opened
    onChipModified = Signal()  # Invoked whenever the chip lists change
    onChipDataModified = Signal()  # Invoked whenever ANYTHING about the chip has been modified.
    onChipSaved = Signal()
    onValveChanged = Signal()

    @staticmethod
    def Rig() -> Rig:
        return AppGlobals.Instance().rig

    @staticmethod
    def OpenChip(chip: Chip):
        AppGlobals.Instance().chip = chip
        AppGlobals.Instance().programRunner.chip = chip
        AppGlobals.Instance().onChipDataModified.connect(chip.RecordModification)
        AppGlobals.Instance().onChipOpened.emit()

    @staticmethod
    def ProgramRunner() -> ProgramRunner:
        return AppGlobals.Instance().programRunner

    @staticmethod
    def Chip() -> Chip:
        return AppGlobals.Instance().chip
