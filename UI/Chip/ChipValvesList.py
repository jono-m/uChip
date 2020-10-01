from UI.LogicBlock.LogicBlockItem import *
from ChipController.ChipController import *


class ChipValvesList(QFrame):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Valve Mappings")
        self.label.setAlignment(Qt.AlignCenter)

        self.scrollArea = QScrollArea()
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.label)
        layout.addWidget(self.scrollArea, stretch=1)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.chipController: typing.Optional[ChipController] = None

        self.setStyleSheet("""
        QLabel {
        background-color: rgba(255, 255, 255, 0.05);
        text-align: center;
        font-weight: bold;
        padding: 5px 20px 5px 20px;
        }
        """)

        self.container = QFrame(self.scrollArea)

        self.scrollArea.setWidget(self.container)
        self.scrollArea.setWidgetResizable(True)

        listLayout = QVBoxLayout()
        listLayout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        listLayout.setContentsMargins(0, 0, 0, 0)
        listLayout.setSpacing(0)
        self.container.setLayout(listLayout)

        self.valvesWidget = QFrame()
        self.valvesWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.valvesWidget.setLayout(QVBoxLayout())
        self.valvesWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.valvesWidget.layout().setSpacing(10)
        listLayout.addWidget(self.valvesWidget)

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
        for child in reversed(self.valvesWidget.children()):
            if isinstance(child, QWidget):
                child.deleteLater()

    def UpdateValvesList(self):
        valves = [valvesField.valveBlock for valvesField in self.valvesWidget.children() if
                  isinstance(valvesField, ValveField)]

        for valveBlock in sorted(self.chipController.valveBlocks, key=lambda x: x.GetPosition().y()):
            if valveBlock not in valves:
                newValveBlock = ValveField(valveBlock)
                self.valvesWidget.layout().addWidget(newValveBlock)


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
        self.parameterSetting.Update("<b><u>" + self.valveBlock.GetName() + "</b></u> - Solenoid Number:", self.valveBlock.solenoidNumberInput.GetDefaultData())

        self.topLevelWidget().update()