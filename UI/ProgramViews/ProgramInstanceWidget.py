from typing import List, Union

from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QToolButton
from PySide6.QtCore import QTimer, Qt
from UI.ProgramViews.DataValueWidget import DataValueWidget
from Model.Program.ProgramInstance import ProgramInstance, Parameter
from Model.Program.Data import DataType
from UI.AppGlobals import AppGlobals


class ProgramInstanceWidget(QFrame):
    def __init__(self, programInstance: ProgramInstance, uniqueRun):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.UpdateParameterItems)

        self.editingParameterVisibility = False

        self.programInstance = programInstance
        self.uniqueRun = uniqueRun

        self.programNameWidget = QLabel()
        self.programNameWidget.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.runButton = QPushButton("Run")
        self.runButton.setProperty("Attention", True)
        self.runButton.clicked.connect(self.RunProgram)

        self._stopButton = QPushButton("Stop")
        self._stopButton.setProperty("Attention", True)
        self._stopButton.clicked.connect(self.StopProgram)

        self.parameterItems: List[ProgramParameterItem] = []

        parameterWidget = QFrame()
        self._parametersLayout = QVBoxLayout()
        self._parametersLayout.setSpacing(0)
        self._parametersLayout.setContentsMargins(0, 0, 0, 0)
        parameterWidget.setLayout(self._parametersLayout)
        layout.addWidget(self.programNameWidget)
        layout.addWidget(parameterWidget)
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
            if parameter.dataType is not DataType.OTHER:
                newItem = ProgramParameterItem(parameter, self.programInstance)
                self._parametersLayout.addWidget(newItem)
                self.parameterItems.append(newItem)

        self.UpdateParameterVisibility()
        self.adjustSize()

    def UpdateInstanceView(self):
        self.programNameWidget.setText(self.programInstance.program.name)
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


class ProgramParameterItem(QFrame):
    def __init__(self, parameter: Parameter, instance: ProgramInstance):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.parameter = parameter
        self._programInstance = instance
        self._parameterName = QLabel()

        self.visibilityToggle = QToolButton()
        self.visibilityToggle.clicked.connect(self.ToggleVisibility)

        self._valueField = DataValueWidget(self.parameter.dataType, self.parameter.listType)
        self._valueField.dataChanged.connect(self.UpdateParameterValue)

        layout.addWidget(self.visibilityToggle)
        layout.addWidget(self._parameterName)
        layout.addWidget(self._valueField)

        self.UpdateFields()

    def ToggleVisibility(self):
        self._programInstance.parameterVisibility[self.parameter] = not self._programInstance.parameterVisibility[
            self.parameter]
        AppGlobals.Instance().onChipDataModified.emit()

    def UpdateParameterValue(self):
        lastValue = self._programInstance.parameterValues[self.parameter]

        if self.parameter.dataType is DataType.INTEGER:
            value = self.parameter.ClampInteger(self._valueField.GetData())
        elif self.parameter.dataType is DataType.FLOAT:
            value = self.parameter.ClampFloat(self._valueField.GetData())
        else:
            value = self._valueField.GetData()
        self._programInstance.parameterValues[self.parameter] = value

        if self._programInstance.parameterValues[self.parameter] != lastValue:
            AppGlobals.Instance().onChipDataModified.emit()

    def UpdateFields(self):
        self._parameterName.setText(self.parameter.name)

        if self._programInstance.parameterVisibility[self.parameter]:
            self.visibilityToggle.setText("O")
        else:
            self.visibilityToggle.setText("X")

        self._valueField.Update(self._programInstance.parameterValues[self.parameter])
