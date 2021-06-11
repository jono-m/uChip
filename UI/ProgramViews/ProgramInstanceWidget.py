from typing import List

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QComboBox, \
    QLineEdit, QPushButton, QToolButton
from PySide6.QtCore import QTimer
from UI.ProgramViews.ChipDataSelection import ChipDataSelection
from Model.Program.ProgramInstance import ProgramInstance, Parameter
from Model.Program.Data import DataType
from UI.AppGlobals import AppGlobals


class ProgramInstanceWidget(QWidget):
    def __init__(self, programInstance: ProgramInstance, uniqueRun):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.UpdateParameterItems)

        self.editingParameterVisibility = False

        self.programInstance = programInstance
        self.uniqueRun = uniqueRun

        self._programNameWidget = QLabel()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.runButton = QPushButton("Run")
        self.runButton.clicked.connect(self.RunProgram)

        self._stopButton = QPushButton("Stop")
        self._stopButton.clicked.connect(self.StopProgram)

        self.parameterItems: List[ProgramParameterItem] = []

        self._parametersLayout = QVBoxLayout()

        layout.addWidget(self._programNameWidget)
        layout.addLayout(self._parametersLayout)
        layout.addWidget(self.runButton)
        layout.addWidget(self._stopButton)
        timer = QTimer(self)
        timer.timeout.connect(self.UpdateInstanceView)
        timer.start(30)

        self.UpdateInstanceView()
        self.UpdateParameterItems()

    def UpdateParameterItems(self):
        [item.deleteLater() for item in self.parameterItems]
        self.parameterItems = []

        for parameter in self.programInstance.program.parameters:
            newItem = ProgramParameterItem(parameter, self.programInstance)
            self._parametersLayout.addWidget(newItem)
            self.parameterItems.append(newItem)

    def UpdateInstanceView(self):
        self._programNameWidget.setText(self.programInstance.program.name)
        if self.uniqueRun:
            self.runButton.setVisible(not AppGlobals.ProgramRunner().IsRunning(self.programInstance))
            self._stopButton.setVisible(AppGlobals.ProgramRunner().IsRunning(self.programInstance))
        else:
            self.runButton.setVisible(True)
            self._stopButton.setVisible(False)

        for item in self.parameterItems:
            item.UpdateFields()

    def UpdateParameterVisibility(self):
        for item in self.parameterItems:
            if self.editingParameterVisibility or self.programInstance.parameterVisibility[item.parameter]:
                item.setVisible(True)
            else:
                item.setVisible(False)
            item.visibilityToggle.setVisible(self.editingParameterVisibility)

        self.adjustSize()

    def RunProgram(self):
        if self.uniqueRun:
            AppGlobals.ProgramRunner().Run(self.programInstance, None)
        else:
            AppGlobals.ProgramRunner().Run(self.programInstance.Clone(), None)

    def StopProgram(self):
        AppGlobals.ProgramRunner().Stop(self.programInstance)


class ProgramParameterItem(QWidget):
    def __init__(self, parameter: Parameter, instance: ProgramInstance, withVisToggle=False):
        super().__init__()

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.parameter = parameter
        self._programInstance = instance
        self._parameterName = QLabel()

        self.visibilityToggle = QToolButton()
        self.visibilityToggle.setCheckable(True)
        self.visibilityToggle.clicked.connect(self.UpdateParameterValue)

        if self.parameter.dataType is DataType.INTEGER:
            self._valueField = QSpinBox()
            self._valueField.valueChanged.connect(self.UpdateParameterValue)
        elif self.parameter.dataType is DataType.FLOAT:
            self._valueField = QDoubleSpinBox()
            self._valueField.valueChanged.connect(self.UpdateParameterValue)
        elif self.parameter.dataType is DataType.BOOLEAN:
            self._valueField = QComboBox()
            self._valueField.addItem("True", True)
            self._valueField.addItem("False", False)
            self._valueField.currentIndexChanged.connect(self.UpdateParameterValue)
        elif self.parameter.dataType is DataType.STRING:
            self._valueField = QLineEdit()
            self._valueField.textChanged.connect(self.UpdateParameterValue)
        elif self.parameter.dataType is not DataType.OTHER:
            self._valueField = ChipDataSelection(self.parameter.dataType)
            self._valueField.currentIndexChanged.connect(self.UpdateParameterValue)

        if self.parameter.dataType is not DataType.OTHER:
            layout.addWidget(self.visibilityToggle)
            layout.addWidget(self._parameterName)
            layout.addWidget(self._valueField)

        self.UpdateFields()

    def UpdateParameterValue(self):
        lastValue = self._programInstance.parameterValues[self.parameter]

        if self.parameter.dataType is DataType.INTEGER:
            self._programInstance.parameterValues[self.parameter] = self._valueField.value()
        elif self.parameter.dataType is DataType.FLOAT:
            self._programInstance.parameterValues[self.parameter] = self._valueField.value()
        elif self.parameter.dataType is DataType.BOOLEAN:
            self._programInstance.parameterValues[self.parameter] = self._valueField.currentData()
        elif self.parameter.dataType is DataType.STRING:
            self._programInstance.parameterValues[self.parameter] = self._valueField.text()
        elif self.parameter.dataType is not DataType.OTHER:
            self._programInstance.parameterValues[self.parameter] = self._valueField.currentData()

        self._programInstance.parameterVisibility[self.parameter] = self.visibilityToggle.isChecked()

        if self._programInstance.parameterValues[self.parameter] != lastValue:
            AppGlobals.Instance().onChipModified.emit()

    def UpdateFields(self):
        self._parameterName.setText(self.parameter.name)

        if self._programInstance.parameterVisibility[self.parameter]:
            self.visibilityToggle.setText("O")
            self.visibilityToggle.setChecked(True)
        else:
            self.visibilityToggle.setText("X")
            self.visibilityToggle.setChecked(False)

        if self.parameter.dataType is DataType.INTEGER:
            self._valueField.setValue(self._programInstance.parameterValues[self.parameter])
            self._valueField.setRange(self.parameter.minimumInteger, self.parameter.maximumInteger)
        elif self.parameter.dataType is DataType.FLOAT:
            self._valueField.setValue(self._programInstance.parameterValues[self.parameter])
            self._valueField.setRange(self.parameter.minimumFloat, self.parameter.maximumFloat)
        elif self.parameter.dataType is DataType.BOOLEAN:
            self._valueField.setCurrentText(str(self._programInstance.parameterValues[self.parameter]))
        elif self.parameter.dataType is DataType.STRING:
            self._valueField.setText(self._programInstance.parameterValues[self.parameter])
        elif self.parameter.dataType is not DataType.OTHER:
            self._valueField.Select(self._programInstance.parameterValues[self.parameter])
