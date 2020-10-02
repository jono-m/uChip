from UI.LogicBlock.LogicBlockItem import *
from ChipController.ChipController import *


class ChipParametersList(QFrame):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
        QLabel {
        background-color: rgba(255, 255, 255, 0.05);
        text-align: center;
        font-weight: bold;
        padding: 5px 20px 5px 20px;
        }
        """)

        self.label = QLabel("Chip Parameters")
        self.label.setAlignment(Qt.AlignCenter)

        self.scrollArea = QScrollArea()
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.container = QFrame()
        self.container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.parametersWidget = QFrame()
        self.parametersWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.valvesWidget = QFrame()
        self.valvesWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.label)
        layout.addWidget(self.scrollArea, stretch=1)
        self.setLayout(layout)

        containerLayout = QVBoxLayout()
        containerLayout.setAlignment(Qt.AlignTop)
        containerLayout.setContentsMargins(0, 0, 0, 0)
        containerLayout.setSpacing(0)
        self.container.setLayout(containerLayout)

        parametersLayout = QVBoxLayout()
        parametersLayout.setContentsMargins(0, 0, 0, 0)
        parametersLayout.setSpacing(10)
        parametersLayout.setAlignment(Qt.AlignTop)
        self.parametersWidget.setLayout(parametersLayout)
        containerLayout.addWidget(self.parametersWidget)

        valvesLayout = QVBoxLayout()
        valvesLayout.setContentsMargins(0, 0, 0, 0)
        valvesLayout.setSpacing(10)
        valvesLayout.setAlignment(Qt.AlignTop)
        self.valvesWidget.setLayout(valvesLayout)
        containerLayout.addWidget(self.valvesWidget)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.container)

        self.chipController: typing.Optional[ChipController] = None

    def CloseChipController(self):
        if self.chipController is not None:
            self.chipController.OnModified.Unregister(self.UpdateParametersList)
        self.chipController = None
        self.Clear()

    def SetChipController(self, cc: ChipController):
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
                newField.setVisible(True)

        valves = [valvesField.valveBlock for valvesField in self.valvesWidget.children() if
                  isinstance(valvesField, UnboundValveField)]

        for valveBlock in self.chipController.valveBlocks:
            if valveBlock not in valves:
                if valveBlock.openInput.connectedOutput is None:
                    newValveBlock = UnboundValveField(valveBlock)
                    self.valvesWidget.layout().addWidget(newValveBlock)
                    newValveBlock.setVisible(True)

        maxWidth = max(self.valvesWidget.sizeHint().width(), self.parametersWidget.sizeHint().width())
        self.scrollArea.setMinimumWidth(maxWidth + self.scrollArea.horizontalScrollBar().sizeHint().width())


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
