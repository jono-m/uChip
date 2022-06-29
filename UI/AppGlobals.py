from Data.Rig.Rig import Rig
from Data.Chip import Chip
from Data.Program.ProgramRunner import ProgramRunner
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
        self.onChipAddRemove.connect(lambda: AppGlobals.Chip().Validate())
        self.onChipAddRemove.connect(self.onChipDataModified.emit)
        self.onChipAddRemove.connect(self.programRunner.CheckPrograms)

    onChipOpened = Signal()  # Invoked whenever a new chip is opened
    onChipAddRemove = Signal()  # Invoked whenever the chip data structure changes
    onChipDataModified = Signal()  # Invoked whenever chip values change
    onChipSaved = Signal()
    onValveChanged = Signal()
    onDevicesChanged = Signal()

    @staticmethod
    def Rig() -> Rig:
        return AppGlobals.Instance().rig

    @staticmethod
    def UpdateRig(force=False):
        lastAvailableDevices = AppGlobals.Rig().GetAvailableDevices()
        lastActiveDevices = AppGlobals.Rig().GetActiveDevices()
        AppGlobals.Rig().RescanPorts()
        newAvailableDevices = AppGlobals.Rig().GetAvailableDevices()
        newActiveDevices = AppGlobals.Rig().GetActiveDevices()

        if force or lastAvailableDevices != newAvailableDevices or lastActiveDevices != newActiveDevices:
            AppGlobals.Instance().onDevicesChanged.emit()

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
