from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QThread, QTimer
from UI.AppGlobals import AppGlobals


class ProgramRunnerWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self._runMultiThreaded = True
        self._disable = False

        self._isRunning = False

        if self._disable:
            return

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
        if self._runMultiThreaded and not self._disable:
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
