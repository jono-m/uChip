from UI.LogicBlock.LogicBlockItem import *
from ChipController.ChipController import *


class ChipValvesList(QFrame):
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

        self.setObjectName("valvesList")

        self.label = QLabel("Valve Mappings")
        self.label.setAlignment(Qt.AlignCenter)

        self.scrollArea = QScrollArea()
        self.scrollArea.setStyleSheet("""background-color: rgba(0, 0, 0, 0.2)""")
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

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
        self.parameterSetting.Update("<b><u>" + self.valveBlock.GetName() + "</b></u> - Solenoid Number:",
                                     self.valveBlock.solenoidNumberInput.GetDefaultData())
