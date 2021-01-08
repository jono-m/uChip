from ChipController.ChipController import *


class GetMenu(QMenu):
    def __init__(self, parent):
        super().__init__(parent)
        self.chipController: typing.Optional[ChipController] = None

        self.OnAddGet = Event()

    def ClearChipController(self):
        if self.chipController is not None:
            self.chipController.GetLogicBlock().OnPortsChanged.Unregister(self.UpdateMenu)
            self.chipController.GetLogicBlock().OnBlockAdded.Unregister(self.UpdateMenu)
            self.chipController.OnModified.Unregister(self.UpdateMenu)

    def SetChipController(self, cc):
        self.ClearChipController()
        self.chipController = cc
        self.chipController.OnModified.Register(self.UpdateMenu, True)
        self.chipController.GetLogicBlock().OnPortsChanged.Register(self.UpdateMenu, True)
        self.chipController.GetLogicBlock().OnBlockAdded.Register(self.UpdateMenu, True)
        self.UpdateMenu()

    def UpdateMenu(self):
        self.clear()
        for inputPort in sorted(self.chipController.GetLogicBlock().GetInputs(),
                                key=lambda x: x.name):
            action = self.addAction(inputPort.name)
            action.triggered.connect(
                lambda checked=False, b=inputPort: self.OnAddGet.Invoke(CurrentSettingBlock(b)))

        for valveBlock in sorted(self.chipController.valveBlocks, key=lambda x: x.GetName()):
            if valveBlock.openInput.connectedOutput is None:
                action = self.addAction(valveBlock.GetName())
                action.triggered.connect(
                    lambda checked=False, b=valveBlock: self.OnAddGet.Invoke(CurrentValveBlock(b)))

        if len(self.actions()) == 0:
            self.addAction("No parameters found.")


class SetMenu(QMenu):
    def __init__(self, parent):
        super().__init__(parent)
        self.chipController: typing.Optional[ChipController] = None

        self.OnAddSet = Event()

    def ClearChipController(self):
        if self.chipController is not None:
            self.chipController.GetLogicBlock().OnPortsChanged.Unregister(self.UpdateMenu)
            self.chipController.GetLogicBlock().OnBlockAdded.Unregister(self.UpdateMenu)

    def SetChipController(self, cc):
        self.ClearChipController()
        self.chipController = cc
        self.chipController.GetLogicBlock().OnPortsChanged.Register(self.UpdateMenu, True)
        self.chipController.GetLogicBlock().OnBlockAdded.Register(self.UpdateMenu, True)
        self.UpdateMenu()

    def UpdateMenu(self):
        self.clear()
        for inputPort in sorted(self.chipController.GetLogicBlock().GetInputs(),
                                key=lambda x: x.name):
            action = self.addAction(inputPort.name)
            action.triggered.connect(
                lambda checked=False, b=inputPort: self.OnAddSet.Invoke(ChipSettingStep(b)))

        for valveBlock in sorted(self.chipController.valveBlocks, key=lambda x: x.GetName()):
            if valveBlock.openInput.connectedOutput is None:
                action = self.addAction(valveBlock.GetName())
                action.triggered.connect(
                    lambda checked=False, b=valveBlock: self.OnAddSet.Invoke(ValveSettingStep(b)))

        if len(self.actions()) == 0:
            self.addAction("No parameters found.")