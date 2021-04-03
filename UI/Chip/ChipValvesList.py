from UI.LogicBlock.LogicBlockItem import *
from BlockSystem.ChipController.Chip import *


class ChipValvesList(QFrame):
    def __init__(self):
        super().__init__()
        self.label = QLabel(text="Valve-Solenoid Mappings")

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.valvesContainer = QFrame()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.label)

        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(0)
        nameHeading = QLabel("Name")
        nameHeading.setObjectName("NameHeading")
        solenoidHeading = QLabel("Number")
        solenoidHeading.setObjectName("SolenoidHeading")
        headerLayout.addWidget(nameHeading, stretch=1)
        headerLayout.addWidget(solenoidHeading, stretch=0)

        layout.addLayout(headerLayout)
        layout.addWidget(self.scrollArea)
        self.setLayout(layout)

        valvesLayout = QVBoxLayout()
        valvesLayout.setContentsMargins(0, 0, 0, 0)
        valvesLayout.setSpacing(0)
        valvesLayout.setAlignment(Qt.AlignTop)
        self.valvesContainer.setLayout(valvesLayout)

        self.scrollArea.setWidget(self.valvesContainer)

        self.chipController: typing.Optional[Chip] = None

    def CloseChipController(self):
        if self.chipController is not None:
            self.chipController.OnModified.Unregister(self.UpdateValvesList)
        self.chipController = None
        self.Clear()

    def SetChipController(self, cc: Chip):
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
                newValveBlock = ValveField(valveBlock, self.SortList)
                newValveBlock.setProperty("IsEven", self.valvesContainer.layout().count() % 2 == 0)
                self.valvesContainer.layout().addWidget(newValveBlock)
                newValveBlock.setVisible(True)

        self.SortList()

    def SortList(self):
        fields = [valveField for valveField in self.valvesContainer.children() if isinstance(valveField, ValveField)]
        fields.sort(key=lambda valveField: valveField.valveBlock.GetSolenoidNumber())
        while self.valvesContainer.layout().count() > 0:
            self.valvesContainer.layout().takeAt(0)
        for field in fields:
            field.setProperty("IsEven", self.valvesContainer.layout().count() % 2 == 0)
            self.valvesContainer.layout().addWidget(field)
            field.setStyleSheet(field.styleSheet())


class ValveField(QFrame):
    def __init__(self, valveBlock: ValveLogicBlock, changeDelegate):
        super().__init__()
        self.valveBlock = valveBlock

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.nameField = QLabel()
        layout.addWidget(self.nameField, stretch=1)
        self.parameterSetting = ParameterWidget(valveBlock.solenoidNumberInput.dataType)
        self.parameterSetting.OnParameterChanged.Register(self.OnParameterChanged, True)
        layout.addWidget(self.parameterSetting, stretch=0)

        self.valveBlock.OnConnectionsChanged.Register(self.Update, True)
        self.valveBlock.OnPortsChanged.Register(self.Update, True)
        self.valveBlock.OnOutputsUpdated.Register(self.Update, True)
        self.valveBlock.OnDestroyed.Register(self.Remove, True)

        self.changeDelegate = changeDelegate
        self.Update()

    def Remove(self):
        self.valveBlock.OnConnectionsChanged.Unregister(self.Update)
        self.valveBlock.OnPortsChanged.Unregister(self.Update)
        self.valveBlock.OnOutputsUpdated.Unregister(self.Update)
        self.valveBlock.OnDestroyed.Unregister(self.Remove)
        self.deleteLater()

    def OnParameterChanged(self, data):
        self.valveBlock.solenoidNumberInput.SetDefaultValue(data)

    def Update(self):
        self.nameField.setText(self.valveBlock.GetName())
        self.parameterSetting.nameLabel.setVisible(False)

        if self.parameterSetting.control.value() != self.valveBlock.solenoidNumberInput.GetDefaultValue():
            self.changeDelegate()
        self.parameterSetting.Update("", self.valveBlock.solenoidNumberInput.GetDefaultValue())
