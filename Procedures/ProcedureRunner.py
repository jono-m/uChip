from Procedures.Procedure import *
import PySide2.QtCore


class ProcedureRunner(QObject):
    onBegin = Signal()
    onDone = Signal()
    onCompleted = Signal()
    onInterruptRequest = Signal()

    def __init__(self, parent: QWidget):
        super().__init__()
        self.currentProcedure: typing.Optional[Procedure] = None

        self._parent = parent
        self.isRunning = False

    def IsRunning(self):
        return self.isRunning

    def Step(self):
        if self.currentProcedure.Update():
            self.StopProcedure(False)

    def SetProcedure(self, procedure: Procedure):
        self.currentProcedure = procedure

    def RunProcedure(self):
        if self.IsRunning() or self.currentProcedure is None:
            return
        self.onBegin.emit()

        self.currentProcedure.Start()
        self.isRunning = True

    def StopProcedure(self, interrupt=True):
        if self.IsRunning():
            if interrupt:
                self.onInterruptRequest.emit()
            else:
                self.ProcedureFinished()
                self.onCompleted.emit()
        else:
            self.onDone.emit()

    def ProcedureFinished(self, force=False):
        if force:
            self.currentProcedure.Stop()
        self.isRunning = False
        self.onDone.emit()