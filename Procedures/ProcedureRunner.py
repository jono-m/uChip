from Procedures.Procedure import *


class ProcedureRunner:
    def __init__(self):
        self.currentProcedure: typing.Optional[Procedure] = None

        self.OnBegin = Event()
        self.OnDone = Event()

        self.isRunning = False

    def IsRunning(self):
        return self.isRunning

    def Step(self):
        if self.currentProcedure.Update():
            self.StopProcedure(False)

    def RunProcedure(self, procedure: Procedure):
        if self.IsRunning():
            return
        self.OnBegin.Invoke()
        self.currentProcedure = procedure

        self.currentProcedure.Start()
        self.isRunning = True

    def StopProcedure(self, interrupt=True):
        if self.IsRunning():
            if interrupt:
                msgBox = QMessageBox()
                msgBox.setWindowTitle("Confirm Stop")
                msgBox.setText("There is a procedure running")
                msgBox.setInformativeText("Are you sure that you want to stop?")
                msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msgBox.setDefaultButton(QMessageBox.No)
                ret = msgBox.exec()
                if ret != QMessageBox.Yes:
                    return False
                else:
                    self.currentProcedure.Stop()

            self.isRunning = False
            self.currentProcedure = None
            self.OnDone.Invoke()
            return True
