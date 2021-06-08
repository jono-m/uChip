from typing import List

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QComboBox, \
    QLineEdit, QPushButton
from PySide6.QtCore import QTimer
from UI.ProgramViews.ChipDataSelection import ChipDataSelection
from Model.Program.ProgramInstance import ProgramInstance, Parameter
from Model.Program.Data import DataType
from UI.AppGlobals import AppGlobals


class ProgramInstanceWidget(QWidget):
    def __init__(self, programInstance: ProgramInstance, uniqueRun):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.UpdateParameterItems)

        self._programInstance = programInstance
        self._uniqueRun = uniqueRun

        self._programNameWidget = QLabel()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.runButton = QPushButton("Run")
        self.runButton.clicked.connect(self.RunProgram)

        self._stopButton = QPushButton("Stop")
        self._stopButton.clicked.connect(self.StopProgram)

        self._parameterItems: List[ProgramParameterItem] = []

        self._parametersLayout = QVBoxLayout()
        self._parametersLayout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._programNameWidget)
        layout.addLayout(self._parametersLayout)
        layout.addWidget(self.runButton)
        layout.addWidget(self._stopButton)
        timer = QTimer(self)
        timer.timeout.connect(self.UpdateProgramName)
        timer.start(30)

        self.UpdateProgramName()
        self.UpdateParameterItems()

    def UpdateParameterItems(self):
        [item.deleteLater() for item in self._parameterItems]
        self._parameterItems = []

        for parameter in self._programInstance.program.parameters:
            newItem = ProgramParameterItem(parameter, self._programInstance)
            self._parametersLayout.addWidget(newItem)
            self._parameterItems.append(newItem)

    def UpdateProgramName(self):
        self._programNameWidget.setText(self._programInstance.program.name)
        if self._uniqueRun:
            self.runButton.setVisible(not AppGlobals.ProgramRunner().IsRunning(self._programInstance))
            self._stopButton.setVisible(AppGlobals.ProgramRunner().IsRunning(self._programInstance))
        else:
            self.runButton.setVisible(True)
            self._stopButton.setVisible(False)

    def RunProgram(self):
        if self._uniqueRun:
            AppGlobals.ProgramRunner().Run(self._programInstance, None)
        else:
            AppGlobals.ProgramRunner().Run(self._programInstance.Clone(), None)

    def StopProgram(self):
        AppGlobals.ProgramRunner().Stop(self._programInstance)


class ProgramParameterItem(QWidget):
    def __init__(self, parameter: Parameter, programInstance: ProgramInstance):
        super().__init__()

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._parameter = parameter
        self._programInstance = programInstance
        self._parameterName = QLabel()

        if self._parameter.dataType is DataType.INTEGER:
            self._valueField = QSpinBox()
            self._valueField.valueChanged.connect(self.UpdateParameterValue)
        elif self._parameter.dataType is DataType.FLOAT:
            self._valueField = QDoubleSpinBox()
            self._valueField.valueChanged.connect(self.UpdateParameterValue)
        elif self._parameter.dataType is DataType.BOOLEAN:
            self._valueField = QComboBox()
            self._valueField.addItem("True", True)
            self._valueField.addItem("False", False)
            self._valueField.currentIndexChanged.connect(self.UpdateParameterValue)
        elif self._parameter.dataType is DataType.STRING:
            self._valueField = QLineEdit()
            self._valueField.textChanged.connect(self.UpdateParameterValue)
        else:
            self._valueField = ChipDataSelection(self._parameter.dataType)
            self._valueField.currentIndexChanged.connect(self.UpdateParameterValue)

        layout.addWidget(self._parameterName)
        layout.addWidget(self._valueField)

        timer = QTimer(self)
        timer.timeout.connect(self.UpdateFields)
        timer.start(30)

        self.UpdateFields()

    def UpdateParameterValue(self):
        if self._parameter.dataType is DataType.INTEGER:
            self._programInstance.parameterValues[self._parameter] = self._valueField.value()
        elif self._parameter.dataType is DataType.FLOAT:
            self._programInstance.parameterValues[self._parameter] = self._valueField.value()
        elif self._parameter.dataType is DataType.BOOLEAN:
            self._programInstance.parameterValues[self._parameter] = self._valueField.currentData()
        elif self._parameter.dataType is DataType.STRING:
            self._programInstance.parameterValues[self._parameter] = self._valueField.text()
        else:
            self._programInstance.parameterValues[self._parameter] = self._valueField.currentData()

    def UpdateFields(self):
        self._parameterName.setText(self._parameter.name)

        if self._parameter.dataType is DataType.INTEGER:
            self._valueField.setValue(self._programInstance.parameterValues[self._parameter])
            self._valueField.setRange(self._parameter.minimumInteger, self._parameter.maximumInteger)
        elif self._parameter.dataType is DataType.FLOAT:
            self._valueField.setValue(self._programInstance.parameterValues[self._parameter])
            self._valueField.setRange(self._parameter.minimumFloat, self._parameter.maximumFloat)
        elif self._parameter.dataType is DataType.BOOLEAN:
            self._valueField.setCurrentText(str(self._programInstance.parameterValues[self._parameter]))
        elif self._parameter.dataType is DataType.STRING:
            self._valueField.setText(self._programInstance.parameterValues[self._parameter])
        else:
            self._valueField.Select(self._programInstance.parameterValues[self._parameter])
