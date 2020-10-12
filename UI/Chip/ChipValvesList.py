from UI.LogicBlock.LogicBlockItem import *
from ChipController.ChipController import *


class ChipValvesList(QFrame):
    def __init__(self):
        super().__init__()

        self.setObjectName("valvesList")

        self.label = QLabel("Valve Mappings")
        self.label.setAlignment(Qt.AlignCenter)

        self.scrollArea = QScrollArea()
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.valvesContainer = QFrame()
        self.valvesContainer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.label)
        layout.addWidget(self.scrollArea, stretch=1)
        self.setLayout(layout)

        valvesLayout = QVBoxLayout()
        valvesLayout.setContentsMargins(0, 0, 0, 0)
        valvesLayout.setSpacing(10)
        valvesLayout.setAlignment(Qt.AlignTop)
        self.valvesContainer.setLayout(valvesLayout)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.valvesContainer)

        self.chipController: typing.Optional[ChipController] = None

        self.setMinimumWidth(300)

    def CloseChipController(self):
        if self.chipController is not None:
            self.chipController.OnModified.Unregister(self.UpdateValvesList)
        self.chipController = None
        self.Clear()

    def SetChipController(self, cc: ChipController):
        self.CloseChipController()
        self.chipController = cc

        self.chipController.OnModified.Register(self.UpdateValvesList, True)

        self.UpdateValvesList()

    def Clear(self):
        for child in reversed(self.valvesContainer.children()):
            if isinstance(child, QWidget):
                child.deleteLater()

    def UpdateValvesList(self):
        valves = [valvesField.valveBlock for valvesField in self.valvesContainer.children() if
                  isinstance(valvesField, ValveField)]

        for valveBlock in sorted(self.chipController.valveBlocks, key=lambda x: x.GetPosition().y()):
            if valveBlock not in valves:
                newValveBlock = ValveField(valveBlock)
                self.valvesContainer.layout().addWidget(newValveBlock)
                newValveBlock.setVisible(True)

        self.scrollArea.setMinimumWidth(
            self.valvesContainer.sizeHint().width() + self.scrollArea.horizontalScrollBar().sizeHint().width())


class ValveField(QFrame):
    def __init__(self, valveBlock: ValveLogicBlock):
        super().__init__()
        self.valveBlock = valveBlock

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.parameterSetting = ParameterWidget(valveBlock.solenoidNumberInput.dataType)
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
        self.valveBlock.solenoidNumberInput.SetDefaultData(data)

    def Update(self):
        self.parameterSetting.Update("<b><u>" + self.valveBlock.GetName() + "</b></u><br>Solenoid Number:",
                                     self.valveBlock.solenoidNumberInput.GetDefaultData())
