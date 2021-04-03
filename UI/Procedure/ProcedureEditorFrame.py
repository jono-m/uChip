from UI.Procedure.ProcedureEditor import *
from UI.BaseEditorFrame import *
from UI.Chip.ChipValvesList import *


class ProcedureEditorFrame(BaseEditorFrame):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.currentProcedure: typing.Optional[Procedure] = None

        self.editor = ProcedureEditor()

        layout.addWidget(self.editor)

    def GetFrameTitle(self):
        if self.currentProcedure is None:
            return "No Procedure Selected."
        return self.currentProcedure.GetName()

    def AddLogicBlock(self, lb: BaseConnectableBlock):
        lb.SetPosition(self.editor.worldBrowser.GetCenterPoint())
        self.currentProcedure.AddSubBlock(lb)

    def AddImage(self, image: Image):
        self.currentProcedure.AddImage(image)

    def UpdateFromSave(self):
        self.currentProcedure.ReloadFileSubBlocks()

    def CloseProcedure(self):
        if self.currentProcedure is not None:
            self.currentProcedure.OnClosed.Unregister(self.CloseProcedure)
        self.currentProcedure = None
        self.editor.Clear()

    def OpenProcedure(self, procedure: Procedure):
        self.CloseProcedure()
        self.currentProcedure = procedure
        self.currentProcedure.OnClosed.Register(self.CloseProcedure, True)
        self.editor.LoadProcedure(self.currentProcedure)
        self.OnTitleUpdated.Invoke()