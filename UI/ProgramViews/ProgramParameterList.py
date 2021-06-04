from typing import Optional, List

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit
from Model.Program.ProgramInstance import ProgramInstance, Parameter
from Model.Program.Data import DataType
from UI.AppGlobals import AppGlobals


class ProgramParameterList(QWidget):
    def __init__(self, programInstance: ProgramInstance):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.RefreshView)

        self._programInstance = programInstance

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._parameterItems: List[ProgramParameterItem] = []

    def RefreshView(self):
        [item.deleteLater() for item in self._parameterItems]
        self._parameterItems = []

        for parameter in self._programInstance.program.parameters:
            newItem = ProgramParameterItem(parameter, self._programInstance)
            self.layout().addWidget(newItem)
            self._parameterItems.append(newItem)


class ProgramParameterItem(QWidget):
    def __init__(self, parameter: Parameter, programInstance: ProgramInstance):
        super().__init__()

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._parameter = parameter
        self._programInstance = programInstance
        self._parameterName = QLabel()

        if self._parameter.GetDataType() is DataType.INTEGER:
            self._valueField = QSpinBox()
            self._valueField.valueChanged.connect(self.OnChanged)
        elif self._parameter.GetDataType() is DataType.FLOAT:
            self._valueField = QDoubleSpinBox()
            self._valueField.valueChanged.connect(self.OnChanged)
        elif self._parameter.GetDataType() is DataType.BOOLEAN:
            self._valueField = QComboBox()
            self._valueField.addItem("True", True)
            self._valueField.addItem("False", False)
            self._valueField.currentIndexChanged.connect(self.OnChanged)
        elif self._parameter.GetDataType() is DataType.STRING:
            self._valueField = QLineEdit()
            self._valueField.textChanged.connect(self.OnChanged)
        elif self._parameter.GetDataType() is DataType.VALVE:
            self._valueField = QComboBox()
            self._valueField.currentIndexChanged.connect(self.OnChanged)
        elif self._parameter.GetDataType() is DataType.PROGRAM:
            self._valueField = QComboBox()
            self._valueField.currentIndexChanged.connect(self.OnChanged)
        else:
            self._valueField = QComboBox()
            self._valueField.currentIndexChanged.connect(self.OnChanged)

        layout.addWidget(self._parameterName)
        layout.addWidget(self._valueField)

        self.UpdateFromParameter()

    def OnChanged(self):
        if self._parameter.GetDataType() is DataType.INTEGER:
            self._programInstance.parameterValues[self._parameter] = self._valueField.value()
        elif self._parameter.GetDataType() is DataType.FLOAT:
            self._programInstance.parameterValues[self._parameter] = self._valueField.value()
        elif self._parameter.GetDataType() is DataType.BOOLEAN:
            self._programInstance.parameterValues[self._parameter] = self._valueField.currentData()
        elif self._parameter.GetDataType() is DataType.STRING:
            self._programInstance.parameterValues[self._parameter] = self._valueField.text()
        elif self._parameter.GetDataType() is DataType.VALVE:
            self._programInstance.parameterValues[self._parameter] = self._valueField.currentData()
        elif self._parameter.GetDataType() is DataType.PROGRAM:
            self._programInstance.parameterValues[self._parameter] = self._valueField.currentData()
        else:
            self._programInstance.parameterValues[self._parameter] = self._valueField.currentData()

    def UpdateFromParameter(self):
        if self._parameterName.text() != self._parameter.GetName():
            self._parameterName.setText(self._parameter.GetName())

        minFloat, maxFloat = self._parameter.GetFloatBounds()
        minInt, maxInt = self._parameter.GetIntegerBounds()

        if self._parameter.GetDataType() is DataType.INTEGER:
            self._valueField.setValue(self._programInstance.parameterValues[self._parameter])
            self._valueField.setRange(minInt, maxInt)
        elif self._parameter.GetDataType() is DataType.FLOAT:
            self._valueField.setValue(self._programInstance.parameterValues[self._parameter])
            self._valueField.setRange(minFloat, maxFloat)
        elif self._parameter.GetDataType() is DataType.BOOLEAN:
            self._valueField.setCurrentText(str(self._programInstance.parameterValues[self._parameter]))
        elif self._parameter.GetDataType() is DataType.STRING:
            self._valueField.setText(self._programInstance.parameterValues[self._parameter])
        elif self._parameter.GetDataType() is DataType.VALVE:
            self._valueField.blockSignals(True)
            self._valueField.clear()
            self._valueField.addItem("None", None)
            if self._programInstance.parameterValues[self._parameter] not in AppGlobals.Chip().valves:
                self._programInstance.parameterValues[self._parameter] = None
            for valve in AppGlobals.Chip().valves:
                self._valueField.addItem(valve.name, valve)
            for index in range(self._valueField.count()):
                if self._valueField.itemData(index) is self._programInstance.parameterValues[self._parameter]:
                    self._valueField.setCurrentIndex(index)
                    break
            self._valueField.blockSignals(False)
        elif self._parameter.GetDataType() is DataType.PROGRAM:
            self._valueField.blockSignals(True)
            self._valueField.clear()
            self._valueField.addItem("None", None)
            if self._programInstance.parameterValues[self._parameter] not in AppGlobals.Chip().programs:
                self._programInstance.parameterValues[self._parameter] = None
            for program in AppGlobals.Chip().programs:
                self._valueField.addItem(program.name, program)
            for index in range(self._valueField.count()):
                if self._valueField.itemData(index) is self._programInstance.parameterValues[self._parameter]:
                    self._valueField.setCurrentIndex(index)
                    break
            self._valueField.blockSignals(False)
        elif self._parameter.GetDataType() is DataType.PROGRAM_PRESET:
            self._valueField.blockSignals(True)
            self._valueField.clear()
            self._valueField.addItem("None", None)
            if self._programInstance.parameterValues[self._parameter] not in AppGlobals.Chip().programPresets:
                self._programInstance.parameterValues[self._parameter] = None
            for programPreset in AppGlobals.Chip().programPresets:
                self._valueField.addItem(programPreset.name, programPreset)
            for index in range(self._valueField.count()):
                if self._valueField.itemData(index) is self._programInstance.parameterValues[self._parameter]:
                    self._valueField.setCurrentIndex(index)
                    break
            self._valueField.blockSignals(False)
