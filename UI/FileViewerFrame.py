from Util import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *


class FileViewerFrame(QFrame):
    def __init__(self):
        super().__init__()

        self.OnNameChange = Event()

        self.isModified = False

    def FullFileName(self) -> typing.Optional[str]:
        return ""

    def FormattedFilename(self) -> str:
        return ""

    def GetFrameTitle(self) -> str:
        if self.isModified:
            return self.FormattedFilename() + "*"
        else:
            return self.FormattedFilename()

    def FileModified(self):
        if not self.isModified:
            self.isModified = True
            self.OnNameChange.Invoke(self.GetFrameTitle())

    def FileSaved(self):
        self.isModified = False
        self.OnNameChange.Invoke(self.GetFrameTitle())

    def TrySave(self):
        pass

    def TrySaveAs(self):
        pass

    def UpdateFromSave(self):
        pass

    def RequestSave(self, saveAs=False):
        if self.FullFileName() is None or saveAs:
            return self.TrySaveAs()
        else:
            return self.TrySave()

    def RequestClose(self):
        if self.isModified:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Confirm Close")
            msgBox.setText("'" + self.FormattedFilename() + "' has been modified.")
            msgBox.setInformativeText("Do you want to save your changes?")
            msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Save)
            msgBox.setWindowIcon(QIcon("Assets/icon.png"))
            ret = msgBox.exec()
            if ret == QMessageBox.Save:
                return self.RequestSave()
            elif ret == QMessageBox.Discard:
                return True
            else:
                return False
        return True
