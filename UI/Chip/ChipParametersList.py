from UI.LogicBlock.LogicBlockItem import *
from ChipController.ChipController import *


class ChipParametersList(QFrame):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.label = QLabel("Chip Parameters")
        layout.addWidget(self.label)

        self.scrollArea = QScrollArea()
        self.container = QFrame()
        self.scrollArea.setWidget(self.container)
        self.scrollArea.setWidgetResizable(True)

        layout.addWidget(self.scrollArea, stretch=1)

        self.chipController: typing.Optional[ChipController] = None

        self.setStyleSheet("""
        QLabel {
        background-color: rgba(255, 255, 255, 0.05);
        text-align: center;
        font-weight: bold;
        padding: 5px 20px 5px 20px;
        }
        """)

        listLayout = QVBoxLayout()
        listLayout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        listLayout.setContentsMargins(0, 0, 0, 0)
        listLayout.setSpacing(0)
        self.container.setLayout(listLayout)

        self.parametersWidget = QFrame()
        self.parametersWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parametersWidget.setLayout(QVBoxLayout())
        self.parametersWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.parametersWidget.layout().setSpacing(10)
        listLayout.addWidget(self.parametersWidget)

        self.valvesWidget = QFrame()
        self.valvesWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.valvesWidget.setLayout(QVBoxLayout())
        self.valvesWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.valvesWidget.layout().setSpacing(10)
        listLayout.addWidget(self.valvesWidget)

        self.setFixedWidth(200)

    def CloseChipController(self):
        if self.chipController is not None:
            self.chipController.OnModified.Unregister(self.UpdateParametersList)
        self.chipController = None

    def LoadChipController(self, cc: ChipController):
        self.CloseChipController()
        self.chipController = cc

        self.chipController.OnModified.Register(self.UpdateParametersList, True)

        self.UpdateParametersList()

    def Clear(self):
        for child in reversed(self.valvesWidget.children()):
            if isinstance(child, QWidget):
                child.deleteLater()
        for child in reversed(self.parametersWidget.children()):
            if isinstance(child, QWidget):
                child.deleteLater()

    def UpdateParametersList(self):
        inputPorts = [chipParameterField.inputPort for chipParameterField in self.parametersWidget.children() if
                      isinstance(chipParameterField, ChipParameterField)]

        for inputPort in sorted(self.chipController.GetLogicBlock().GetInputs(),
                                key=lambda x: x.name):
            if inputPort not in inputPorts:
                newField = ChipParameterField(inputPort)
                self.parametersWidget.layout().addWidget(newField)

        valves = [valvesField.valveBlock for valvesField in self.valvesWidget.children() if
                  isinstance(valvesField, UnboundValveField)]

        for valveBlock in self.chipController.valveBlocks:
            if valveBlock not in valves:
                if valveBlock.openInput.connectedOutput is None:
                    newValveBlock = UnboundValveField(valveBlock)
                    self.valvesWidget.layout().addWidget(newValveBlock)


class ChipParameterField(QFrame):
    def __init__(self, inputPort: InputPort):
        super().__init__()
        self.inputPort = inputPort

        self.setStyleSheet("""
        * {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 2px;
        }
        QLabel {
        background-color: rgba(255, 255, 255, 0.1);
        }
        QSpinBox, QDoubleSpinBox, QCheckBox {
        margin: 5px;
        border: 1px solid white;
        background-color: transparent;
        }
        QCheckBox {
        border: none;
        }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.parameterSetting = ParameterWidget(inputPort.dataType)
        self.parameterSetting.OnParameterChanged.Register(self.OnParameterChanged, True)
        self.parameterSetting.nameLabel.setAlignment(Qt.AlignLeft)
        self.parameterSetting.nameLabel.setVisible(True)
        self.parameterSetting.layout().setSpacing(0)
        layout.addWidget(self.parameterSetting)

        self.inputPort.block.OnConnectionsChanged.Register(self.Update, True)
        self.inputPort.block.OnPortsChanged.Register(self.Update, True)
        self.inputPort.block.OnOutputsUpdated.Register(self.Update, True)
        self.inputPort.block.OnDestroyed.Register(self.Remove, True)

        self.Update()

    def Remove(self):
        self.inputPort.block.OnConnectionsChanged.Unregister(self.Update)
        self.inputPort.block.OnPortsChanged.Unregister(self.Update)
        self.inputPort.block.OnOutputsUpdated.Unregister(self.Update)
        self.inputPort.block.OnDestroyed.Unregister(self.Remove)
        self.deleteLater()

    def OnParameterChanged(self, data):
        self.inputPort.SetDefaultData(data)

    def Update(self):
        if self.inputPort not in self.inputPort.block.GetInputs():
            self.Remove()
            return

        self.parameterSetting.Update(self.inputPort.name, self.inputPort.GetDefaultData())


class UnboundValveField(QFrame):
    def __init__(self, valveBlock: ValveLogicBlock):
        super().__init__()
        self.valveBlock = valveBlock

        self.setStyleSheet("""
        * {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 2px;
        }
        QLabel {
        background-color: rgba(255, 255, 255, 0.1);
        }
        QSpinBox, QDoubleSpinBox, QCheckBox {
        margin: 5px;
        border: 1px solid white;
        background-color: transparent;
        }
        QCheckBox {
        border: none;
        }""")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.parameterSetting = ParameterWidget(valveBlock.openInput.dataType)
        self.parameterSetting.OnParameterChanged.Register(self.OnParameterChanged, True)
        self.parameterSetting.nameLabel.setAlignment(Qt.AlignLeft)
        self.parameterSetting.nameLabel.setVisible(True)
        self.parameterSetting.layout().setSpacing(0)
        layout.addWidget(self.parameterSetting)

        self.valveBlock.OnConnectionsChanged.Register(self.Update, True)
        self.valveBlock.OnPortsChanged.Register(self.Update, True)
        self.valveBlock.OnOutputsUpdated.Register(self.Update, True)
        self.valveBlock.OnDestroyed.Register(self.Remove, True)

        self.Update()

    def Remove(self):
        self.valveBlock.OnConnectionsChanged.Unregister(self.Update)
        self.valveBlock.OnPortsChanged.Unregister(self.Update)
        self.valveBlock.OnOutputsUpdated.Unregister(self.Update)
        self.valveBlock.OnDestroyed.Unregister(self.Remove)
        self.deleteLater()

    def OnParameterChanged(self, data):
        self.valveBlock.openInput.SetDefaultData(data)

    def Update(self):
        if self.valveBlock.openInput.connectedOutput is not None:
            self.Remove()
            return

        self.parameterSetting.Update(self.valveBlock.GetName(), self.valveBlock.openInput.GetDefaultData())
