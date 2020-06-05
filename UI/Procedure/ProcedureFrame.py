from UI.Procedure.ProcedureEditor import *

from UI.Chip.ChipParametersList import *
from UI.Chip.ChipValvesList import *


class ProcedureFrame(QFrame):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.currentProcedure: typing.Optional[Procedure] = None

        self.procedureEditor = ProcedureEditor()

        self.chipController: typing.Optional[ChipController] = None

        vLayout = QVBoxLayout()
        self.chipParametersList = ChipParametersList()
        vLayout.addWidget(self.chipParametersList)
        self.valvesList = ChipValvesList()
        vLayout.addWidget(self.valvesList)

        layout.addLayout(vLayout)
        layout.addWidget(self.procedureEditor, stretch=1)

        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.TimerUpdate)
        self.updateTimer.start(5)

    def OnTabChanged(self):
        self.procedureEditor.worldBrowser.SelectItem(None)

    def TimerUpdate(self):
        if self.currentProcedure is not None:
            self.currentProcedure.UpdateOutputs()

    def SetIsProcedureRunning(self, running):
        self.procedureEditor.worldBrowser.actionsEnabled = not running
        self.procedureEditor.worldBrowser.update()
        self.chipParametersList.setEnabled(not running)
        self.valvesList.setEnabled(not running)

    def GetFrameTitle(self):
        if self.currentProcedure is None:
            return "No Procedure Selected."
        return self.currentProcedure.GetName()

    def RequestAddBlock(self, lb: LogicBlock):
        lb.SetPosition(self.procedureEditor.worldBrowser.GetCenterPoint())
        self.currentProcedure.AddSubBlock(lb)

    def RequestAddImage(self, image: Image):
        self.currentProcedure.AddImage(image)

    def UpdateFromSave(self):
        self.currentProcedure.ReloadFileSubBlocks()

    def OpenChipController(self, chipController: ChipController):
        self.CloseProcedure()

        self.chipController = chipController

        self.OpenProcedure(self.chipController.GetProcedures()[0])
        self.chipParametersList.LoadChipController(self.chipController)
        self.valvesList.LoadChipController(self.chipController)

    def CloseProcedure(self):
        if self.currentProcedure is not None:
            self.chipController.GetLogicBlock().OnOutputsUpdated.Unregister(self.currentProcedure.UpdateOutputs)
            self.currentProcedure.OnDestroyed.Unregister(self.OnProcedureDestroyed)
        self.currentProcedure = None
        self.procedureEditor.Clear()
        self.valvesList.Clear()
        self.chipParametersList.Clear()

    def OnProcedureDestroyed(self):
        if len(self.chipController.GetProcedures()) > 0:
            self.OpenProcedure(self.chipController.GetProcedures()[0])

    def OpenProcedure(self, procedure: Procedure):
        self.CloseProcedure()

        self.currentProcedure = procedure

        self.currentProcedure.OnDestroyed.Register(self.OnProcedureDestroyed, True)

        self.chipController.GetLogicBlock().OnOutputsUpdated.Register(self.currentProcedure.UpdateOutputs,
                                                                      True)

        self.procedureEditor.LoadProcedure(self.currentProcedure)
