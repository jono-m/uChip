from PySide6.QtCore import QThread
from UI.AppGlobals import AppGlobals


class ProgramRunnerWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self._isRunning = False

    def run(self) -> None:
        self._isRunning = True
        while self._isRunning:
            AppGlobals.ProgramRunner().Tick()
            self.msleep(10)

    def stop(self):
        self._isRunning = False
