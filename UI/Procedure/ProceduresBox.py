from PySide2.QtWidgets import *
from ChipController.ChipController import *


class ProceduresBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.OnProcedureSelected = Event()
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Ignored)
        self.setFixedWidth(200)
        self.setView(QListView())

        self.chipController: typing.Optional[ChipController] = None

        self.activated.connect(self.HandleProcedureSelection)

        self.currentProcedure: typing.Optional[Procedure] = None

    def ClearChipController(self):
        if self.chipController is not None:
            self.chipController.OnProcedureAdded.Unregister(self.UpdateProceduresList)
            self.chipController.OnProcedureRemoved.Unregister(self.UpdateProceduresList)
            self.currentProcedure = None

    def SetChipController(self, cc: ChipController):
        self.ClearChipController()
        self.chipController = cc
        self.chipController.OnProcedureAdded.Register(self.UpdateProceduresList, True)
        self.chipController.OnProcedureRemoved.Register(self.UpdateProceduresList, True)
        self.currentProcedure = self.chipController.GetProcedures()[0]
        self.UpdateProceduresList()

    def UpdateProceduresList(self):
        proceduresList = sorted(self.chipController.GetProcedures(), key=lambda x: x.GetName())

        self.blockSignals(True)
        self.clear()
        for p in proceduresList:
            self.addItem(p.GetName(), userData=p)
            if p == self.currentProcedure:
                self.setCurrentIndex(self.count() - 1)

        if self.currentProcedure not in self.chipController.GetProcedures():
            self.setCurrentIndex(0)
        self.blockSignals(False)

    def HandleProcedureSelection(self):
        self.currentProcedure = self.currentData()
        self.OnProcedureSelected.Invoke(self.currentProcedure)
