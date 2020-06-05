from UI.FileViewerFrame import *
from UI.LogicBlock.LogicBlockEditor import *


class LogicBlockFrame(FileViewerFrame):
    def __init__(self, logicBlock: CompoundLogicBlock):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.logicBlock = logicBlock

        self.logicBlockEditor = LogicBlockEditor()

        layout.addWidget(self.logicBlockEditor)

        self.logicBlock.OnModified.Register(self.FileModified, True)
        self.logicBlock.OnSaved.Register(self.FileSaved, True)

        self.logicBlockEditor.LoadBlock(self.logicBlock)

        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.TimerUpdate)
        self.updateTimer.start(100)

    def TimerUpdate(self):
        if self.logicBlock is not None:
            self.logicBlock.UpdateOutputs()

    def RequestAddBlock(self, lb: LogicBlock):
        lb.SetPosition(self.logicBlockEditor.worldBrowser.GetCenterPoint())
        if isinstance(lb, CompoundLogicBlock) and self.logicBlock.CreatesLoop(lb):
            QMessageBox.warning(self, "Element addition failed",
                                "The current logic block is used in the logic block that you are trying to "
                                "add. This would create a never-ending loop! Cannot add.")
        else:
            self.logicBlock.AddSubBlock(lb)

    def RequestAddImage(self, image: Image):
        self.logicBlock.AddImage(image)

    def OnTabChanged(self):
        self.logicBlockEditor.worldBrowser.SelectItem(None)

    def closeEvent(self, event: QCloseEvent):
        self.logicBlock.OnModified.Unregister(self.FileModified)
        self.logicBlock.OnModified.Unregister(self.FileSaved)
        self.logicBlock.Destroy()

    def FullFileName(self) -> typing.Optional[str]:
        return self.logicBlock.GetFilename()

    def FormattedFilename(self) -> str:
        return self.logicBlock.GetName()

    def TrySave(self):
        self.logicBlock.Save()
        return True

    def TrySaveAs(self):
        dialog = SaveAsDialog(self)
        if dialog.exec_():
            filename = dialog.selectedFiles()

            if filename is not None:
                self.logicBlock.Save(filename[0])
                return True
            else:
                return False
        return False

    def UpdateFromSave(self):
        self.logicBlock.ReloadFileSubBlocks()


class SaveAsDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Save logic block")
        self.setFileMode(QFileDialog.AnyFile)
        self.setAcceptMode(QFileDialog.AcceptSave)
        self.setNameFilters(["μChip Logic Block (*.ulb)"])
