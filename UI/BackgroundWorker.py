from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QThread, QTimer
from UI.UIMaster import UIMaster

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QThread, QTimer
from UI.AppGlobals import AppGlobals
import sys
from Data.Rig.Rig import Rig


class RigWatchdogWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self._runMultiThreaded = True

        self._isRunning = False

        if self._runMultiThreaded:
            self.start()
        else:
            runTimer = QTimer(self._parent)
            runTimer.timeout.connect(self.Tick)
            runTimer.start(3000)

    def run(self) -> None:
        self._isRunning = True
        while self._isRunning:
            # self.Tick()
            self.msleep(3000)

    def stop(self):
        self._isRunning = False

    def terminate(self) -> None:
        if self._runMultiThreaded:
            super().terminate()
        else:
            return

    def Tick(self):
        try:
            AppGlobals.UpdateRig()
        except Exception as e:
            QMessageBox.critical(self._parent, "Rig error!", str(e))

class BackgroundWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self._runMultiThreaded = True

        self._isRunning = False

        if self._runMultiThreaded:
            killTimer = QTimer(self._parent)
            killTimer.timeout.connect(self.CheckForKill)
            killTimer.start(2000)
            self.start()
        else:
            runTimer = QTimer(self._parent)
            runTimer.timeout.connect(lambda: AppGlobals.ProgramRunner().Tick())
            runTimer.start(50)

    def run(self) -> None:
        self._isRunning = True
        while self._isRunning:
            AppGlobals.ProgramRunner().Tick()
            self.msleep(50)

    def stop(self):
        self._isRunning = False

    def terminate(self) -> None:
        if self._runMultiThreaded:
            super().terminate()
        else:
            return

    def CheckForKill(self):
        if AppGlobals.ProgramRunner().GetTickDelta() > 2:
            self.terminate()
            self.wait()
            AppGlobals.ProgramRunner().StopAll()
            self.start()
            QMessageBox.critical(self._parent, "Timeout", "Program timed out.")
