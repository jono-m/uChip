from ChipController.ChipController import *
from Procedures.ProcedureRunner import *


class ChipUpdateWorker(QRunnable):
    def __init__(self, rig: Rig, procedureRunner: ProcedureRunner):
        super().__init__()

        self.chipController = None
        self.rig = rig
        self.procedureRunner = procedureRunner

        self._isRunning = False

    def SetChipController(self, cc):
        self.chipController = cc

    def run(self):
        self._isRunning = True

        while self._isRunning:
            if self.chipController is not None:
                self.chipController.GetLogicBlock().UpdateOutputs()
                self.chipController.SendToRig(self.rig)
            if self.procedureRunner.IsRunning():
                self.procedureRunner.Step()
            QThread.msleep(10)

    def stop(self):
        self._isRunning = False
        self.rig.DisconnectAll()