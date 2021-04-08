from UI.LogicBlock.LogicBlockItem import *
from BlockSystem.ChipController.Chip import *


class ChipParametersList(QFrame):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Chip Parameters")

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.container = QFrame()

        self.parametersWidget = QFrame()

        self.valvesWidget = QFrame()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.label)
        layout.addWidget(self.scrollArea)
        self.setLayout(layout)

        containerLayout = QVBoxLayout()
        containerLayout.setContentsMargins(0, 0, 0, 0)
        containerLayout.setSpacing(0)
        containerLayout.setAlignment(Qt.AlignTop)
        self.container.setLayout(containerLayout)

        parametersLayout = QVBoxLayout()
        parametersLayout.setContentsMargins(0, 0, 0, 0)
        parametersLayout.setSpacing(0)
        parametersLayout.setAlignment(Qt.AlignTop)
        self.parametersWidget.setLayout(parametersLayout)
        containerLayout.addWidget(self.parametersWidget)

        self.scrollArea.setWidget(self.container)

        self.chipController: typing.Optional[Chip] = None

    def CloseChipController(self):
        if self.chipController is not None:
            self.chipController.OnModified.Unregister(self.UpdateParametersList)
        self.chipController = None
        self.Clear()

    def SetChipController(self, cc: Chip):
        self.CloseChipController()
        self.chipController = cc

        self.chipController.OnModified.Register(self.UpdateParametersList, True)

        self.UpdateParametersList()

    def Clear(self):
        for child in reversed(self.parametersWidget.children()):
            if isinstance(child, QWidget):
                child.deleteLater()

    def UpdateParametersList(self):
        inputPorts = [chipParameterField.inputPort for chipParameterField in self.parametersWidget.children() if
                      isinstance(chipParameterField, ChipParameterField)]

        for inputPort in sorted(self.chipController.GetLogicBlock().GetInputPorts(),
                                key=lambda x: x.name):
            if inputPort not in inputPorts:
                newField = ChipParameterField(inputPort, self.SortList)
                self.parametersWidget.layout().addWidget(newField)

        valves = [valvesField.valveBlock for valvesField in self.parametersWidget.children() if
                  isinstance(valvesField, UnboundValveField)]

        for valveBlock in self.chipController.valveBlocks:
            if valveBlock not in valves:
                if valveBlock.openInput.connectedOutput is None:
                    newValveBlock = UnboundValveField(valveBlock, self.SortList)
                    self.parametersWidget.layout().addWidget(newValveBlock)

        self.SortList()

    def SortList(self):
        fields = [parameterField for parameterField in self.parametersWidget.children() if
                  isinstance(parameterField, ChipParameterField) or isinstance(parameterField, UnboundValveField)]
        fields.sort(key=ChipParametersList.GetKey)
        while self.parametersWidget.layout().count() > 0:
            self.parametersWidget.layout().takeAt(0)
        for field in fields:
            self.parametersWidget.layout().addWidget(field)

    @staticmethod
    def GetKey(field: QWidget):
        if isinstance(field, ChipParameterField):
            return field.inputPort.name.lower()
        if isinstance(field, UnboundValveField):
            return field.valveBlock.GetName().lower()


class ChipParameterField(QFrame):
    def __init__(self, inputPort: InputPort, changedNameDelegate):
        super().__init__()
        self.inputPort = inputPort

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.parameterSetting = ParameterWidget(inputPort.dataType)
        self.parameterSetting.OnParameterChanged.Register(self.OnParameterChanged, True)
        layout.addWidget(self.parameterSetting)

        self.inputPort.connectableBlock.OnConnectionsChanged.Register(self.Update, True)
        self.inputPort.connectableBlock.OnPortsChanged.Register(self.Update, True)
        self.inputPort.connectableBlock.OnOutputsUpdated.Register(self.Update, True)
        self.inputPort.connectableBlock.OnDestroyed.Register(self.Remove, True)

        self.changedNameDelegate = changedNameDelegate

        self.Update()

    def Remove(self):
        self.inputPort.connectableBlock.OnConnectionsChanged.Unregister(self.Update)
        self.inputPort.connectableBlock.OnPortsChanged.Unregister(self.Update)
        self.inputPort.connectableBlock.OnOutputsUpdated.Unregister(self.Update)
        self.inputPort.connectableBlock.OnDestroyed.Unregister(self.Remove)
        self.deleteLater()

    def OnParameterChanged(self, data):
        self.inputPort.SetDefaultValue(data)

    def Update(self):
        if self.inputPort not in self.inputPort.connectableBlock.GetInputPorts():
            self.Remove()
            return

        if self.parameterSetting.nameLabel.text() != self.inputPort.name:
            self.changedNameDelegate()
        self.parameterSetting.Update(self.inputPort.name, self.inputPort.GetDefaultValue())


class UnboundValveField(QFrame):
    def __init__(self, valveBlock: ValveLogicBlock, changedNameDelegate):
        super().__init__()
        self.valveBlock = valveBlock

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.parameterSetting = ParameterWidget(valveBlock.openInput.dataType)
        self.parameterSetting.OnParameterChanged.Register(self.OnParameterChanged, True)
        layout.addWidget(self.parameterSetting)

        self.valveBlock.OnConnectionsChanged.Register(self.Update, True)
        self.valveBlock.OnPortsChanged.Register(self.Update, True)
        self.valveBlock.OnOutputsUpdated.Register(self.Update, True)
        self.valveBlock.OnDestroyed.Register(self.Remove, True)

        self.changedNameDelegate = changedNameDelegate

        self.Update()

    def Remove(self):
        self.valveBlock.OnConnectionsChanged.Unregister(self.Update)
        self.valveBlock.OnPortsChanged.Unregister(self.Update)
        self.valveBlock.OnOutputsUpdated.Unregister(self.Update)
        self.valveBlock.OnDestroyed.Unregister(self.Remove)
        self.deleteLater()

    def OnParameterChanged(self, data):
        self.valveBlock.openInput.SetDefaultValue(data)

    def Update(self):
        if self.valveBlock.openInput.connectedOutput is not None:
            self.Remove()
            return

        if self.parameterSetting.nameLabel.text() != self.valveBlock.GetName():
            self.changedNameDelegate()
        self.parameterSetting.Update(self.valveBlock.GetName(), self.valveBlock.openInput.GetDefaultValue())
