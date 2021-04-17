from UI.ProjectWindow.BaseEditorFrame import *


class CustomLogicBlockEditorFrame(BaseEditorFrame):
    def __init__(self, logicBlock: CompoundLogicBlock):
        super().__init__()

        self.logicBlock = logicBlock

        self.editor = LogicBlockEditor()
        self.nameFilters = ["μChip Logic Block (*.ulb)"]

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(self.editor)

        self.logicBlock.OnModified.Register(self.FileModified, True)
        self.logicBlock.OnSaved.Register(self.FileSaved, True)

        self.editor.LoadBlock(self.logicBlock)

        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.TimerUpdate)
        self.updateTimer.start(100)

        self.hasFilename = logicBlock.absolutePath is not None

    def TimerUpdate(self):
        if self.logicBlock is not None:
            self.logicBlock.ComputeOutputs()

    def AddLogicBlock(self, lb: ConnectableBlock):
        lb.SetPosition(self.editor.worldBrowser.GetCenterPoint())
        if isinstance(lb, CompoundLogicBlock) and self.logicBlock.CreatesLoop(lb):
            QMessageBox.warning(parent=self, title="Element addition failed",
                                text="The current logic block is used in the logic block that you are trying to "
                                     "add. This would create a never-ending loop! Cannot add.")
        else:
            self.logicBlock.AddSubBlock(lb)

    def AddImage(self, image: Image):
        self.logicBlock.AddImage(image)

    def RequestClose(self):
        if super().RequestClose():
            self.logicBlock.OnModified.Unregister(self.FileModified)
            self.logicBlock.OnModified.Unregister(self.FileSaved)
            self.logicBlock.Destroy()
            return True
        return False

    def DoSave(self, filename=None):
        self.logicBlock.Save(filename)

    def GetName(self) -> str:
        return self.logicBlock.GetName()

    def UpdateFromSave(self):
        self.logicBlock.ReloadFileSubBlocks()
