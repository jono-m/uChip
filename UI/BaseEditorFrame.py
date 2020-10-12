from UI.LogicBlock.LogicBlockEditor import *


class BaseEditorFrame(QFrame):
    def __init__(self):
        super().__init__()

        self.OnTitleUpdated = Event()

        self.isModified = False

        self.hasFilename = False

        self.editor: typing.Optional[LogicBlockEditor] = None

        self.nameFilters = None

    def UpdateForProcedureStatus(self, running):
        self.editor.worldBrowser.SetActionsEnabled(not running)

    def ClearFocus(self):
        self.editor.worldBrowser.ClearSelection()

    def DoSave(self, filename=None):
        pass

    def GetName(self) -> str:
        return ""

    def GetFrameTitle(self) -> str:
        if self.isModified:
            return self.GetName() + "*"
        else:
            return self.GetName()

    def FileModified(self):
        if not self.isModified:
            self.isModified = True
            self.OnTitleUpdated.Invoke(self.GetFrameTitle())

    def FileSaved(self):
        self.isModified = False
        self.hasFilename = True
        self.OnTitleUpdated.Invoke(self.GetFrameTitle())

    def AddImage(self, image: Image):
        pass

    def AddLogicBlock(self, lb: LogicBlock):
        pass

    def TrySaveAs(self):
        dialog = SaveAsDialog(self)
        if dialog.exec_():
            filename = dialog.selectedFiles()

            if filename is not None:
                self.DoSave(filename[0])
                return True
            else:
                return False
        return False

    def UpdateFromSave(self):
        pass

    def RequestSave(self, saveAs=False):
        if not self.hasFilename or saveAs:
            return self.TrySaveAs()
        else:
            return self.DoSave()

    def RequestClose(self):
        if self.isModified:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Confirm Close")
            msgBox.setText("'" + self.GetName() + "' has been modified.")
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


class SaveAsDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Save")
        self.setFileMode(QFileDialog.AnyFile)
        self.setAcceptMode(QFileDialog.AcceptSave)
        self.setNameFilters([self.nameFilters])
