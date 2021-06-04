from PySide6.QtCore import QThread
from Model.Program.ProgramRunner import ProgramRunner


class ProgramRunnerWorker(QThread):
    def __init__(self, parent, programRunner: ProgramRunner):
        super().__init__(parent, )

        self._programRunner = programRunner
        self._isRunning = False

    def run(self) -> None:
        self._isRunning = True
        while self._isRunning:
            self._programRunner.Tick()
            self.msleep(10)

    def stop(self):
        self._isRunning = False
