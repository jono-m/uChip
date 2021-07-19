from PySide6.QtWidgets import QFrame, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit, QVBoxLayout, QLabel, QHBoxLayout, \
    QSizePolicy
from PySide6.QtCore import Signal
from Model.Program.Data import DataType, DataValueType
from UI.ProgramViews.ChipDataSelection import ChipDataSelection
from typing import List


class DataValueWidget(QFrame):
    dataChanged = Signal()

    def __init__(self, dataType: DataType, listType: DataType = None):
        super().__init__()

        self.dataType = dataType

        if self.dataType is DataType.INTEGER:
            self.field = QSpinBox()
            self.field.valueChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.FLOAT:
            self.field = QDoubleSpinBox()
            self.field.valueChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.BOOLEAN:
            self.field = QComboBox()
            self.field.addItem("True", True)
            self.field.addItem("False", False)
            self.field.currentIndexChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.STRING:
            self.field = QLineEdit()
            self.field.textChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.VALVE or self.dataType is DataType.PROGRAM_PRESET:
            self.field = ChipDataSelection(self.dataType)
            self.field.currentIndexChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.LIST and listType:
            self.field = ListDataSelection(listType)
            self.field.dataChanged.connect(lambda: self.dataChanged.emit())
        else:
            return
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.field)

        self.field.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setLayout(layout)

    def GetData(self):
        if self.dataType is DataType.INTEGER or self.dataType is DataType.FLOAT:
            return self.field.value()
        elif self.dataType is DataType.BOOLEAN or self.dataType is DataType.VALVE or self.dataType is DataType.PROGRAM_PRESET:
            return self.field.currentData()
        elif self.dataType is DataType.STRING:
            return self.field.text()
        elif self.dataType is DataType.LIST:
            return self.field.GetList()

    def Update(self, data: DataValueType):
        if self.dataType is DataType.INTEGER:
            self.field.setValue(data)
        elif self.dataType is DataType.FLOAT:
            self.field.setValue(data)
        elif self.dataType is DataType.BOOLEAN:
            self.field.setCurrentText(str(data))
        elif self.dataType is DataType.STRING:
            self.field.setText(data)
        elif self.dataType is DataType.VALVE or self.dataType is DataType.PROGRAM_PRESET:
            self.field.Select(data)
        elif self.dataType is DataType.LIST:
            self.field.Prepare(data)


class ListDataSelection(QFrame):
    dataChanged = Signal()

    def __init__(self, listDataType: DataType):
        super().__init__()
        self.listDataType = listDataType
        countLabel = QLabel("Count: ")
        self.countField = QSpinBox()
        self.countField.setMinimum(0)
        self.countField.setMaximum(200)
        self.countField.valueChanged.connect(lambda: self.dataChanged.emit())

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        titleLayout = QHBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)
        titleLayout.setSpacing(0)
        titleLayout.addWidget(countLabel)
        titleLayout.addWidget(self.countField)
        layout.addLayout(titleLayout)
        self.setLayout(layout)

        self._fields: List[DataValueWidget] = []

    def Prepare(self, data: List[DataValueType]):
        self.countField.setValue(len(data))

        pool = len(self._fields)
        needed = len(data)
        delta = needed - pool

        for i in range(abs(delta)):
            if delta > 0:
                valueWidget = DataValueWidget(self.listDataType)
                valueWidget.dataChanged.connect(lambda: self.dataChanged.emit())
                self.layout().addWidget(valueWidget)
                self._fields.append(valueWidget)
            else:
                self._fields.pop().deleteLater()

        for i in range(needed):
            self._fields[i].Update(data[i])

    def GetList(self):
        count = self.countField.value()
        mainList = [field.GetData() for field in self._fields] + \
                   [self.listDataType.GetDefaultValue()] * (count - len(self._fields))
        return mainList[:count]
