from typing import List
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QToolButton, QPlainTextEdit, \
    QGridLayout, QSizePolicy
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from UI.ProgramViews.DataValueWidget import DataValueWidget
from Model.Program.ProgramInstance import ProgramInstance, Parameter
from Model.Program.Data import DataType
from UI.AppGlobals import AppGlobals


class ProgramInstanceWidget(QFrame):
    def __init__(self, programInstance: ProgramInstance):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.UpdateParameterItems)
        AppGlobals.ProgramRunner().onInstanceChange.connect(self.UpdateInstanceView)
        AppGlobals.Instance().onChipDataModified.connect(self.UpdateInstanceView)

        self._showAllParameters = False
        self._editParameterVisibility = False

        self.programInstance = programInstance
        self.ownsInstance = False

        self.programNameWidget = QLabel()
        self.programNameWidget.setAlignment(Qt.AlignCenter)

        titleLayout = QHBoxLayout()
        titleLayout.addWidget(self.programNameWidget)

        self._description = QPlainTextEdit(programInstance.program.description)
        self._description.setReadOnly(True)

        outerLayout = QHBoxLayout()
        outerLayout.setContentsMargins(0, 0, 0, 0)
        outerLayout.setSpacing(0)

        innerLayout = QVBoxLayout()
        innerLayout.setContentsMargins(0, 0, 0, 0)
        innerLayout.setSpacing(0)

        self.runButton = QPushButton("Run")
        self.runButton.setProperty("Attention", True)
        self.runButton.clicked.connect(self.RunProgram)

        self._stopButton = QPushButton("Stop")
        self._stopButton.setProperty("BadAttention", True)
        self._stopButton.clicked.connect(self.StopProgram)

        self.parameterItems: List[ProgramParameterItem] = []

        self._parameterWidget = QFrame()
        self._parametersLayout = QGridLayout()
        self._parametersLayout.setAlignment(Qt.AlignTop)
        self._parametersLayout.setSpacing(0)
        self._parametersLayout.setContentsMargins(0, 0, 0, 0)
        self._parameterWidget.setLayout(self._parametersLayout)

        innerLayout.addLayout(titleLayout)
        innerLayout.addWidget(self._parameterWidget)
        innerLayout.addWidget(self.runButton)
        innerLayout.addWidget(self._stopButton)
        innerLayout.addStretch(1)

        outerLayout.addLayout(innerLayout)
        outerLayout.addWidget(self._description)

        self.setLayout(outerLayout)

        self.UpdateParameterItems()

    def SetTitleVisible(self, visible):
        self.programNameWidget.setVisible(visible)

    def SetDescriptionVisible(self, visisble):
        self._description.setVisible(visisble)

    def DescriptionVisible(self):
        return self._description.isVisible()

    def SetShowAllParameters(self, showAll):
        self._showAllParameters = showAll
        self.UpdateInstanceView()

    def SetEditParameterVisibility(self, edit):
        self._editParameterVisibility = edit
        self.UpdateInstanceView()

    def UpdateParameterItems(self):
        [item.deleteLater() for item in self.parameterItems]
        self.parameterItems = []

        i = 0
        for parameter in self.programInstance.program.parameters:
            if parameter.dataType is not DataType.OTHER:
                newItem = ProgramParameterItem(parameter, self.programInstance)
                self._parametersLayout.addWidget(newItem.visibilityToggle, i, 0)
                self._parametersLayout.addWidget(newItem.parameterName, i, 1)
                self._parametersLayout.addWidget(newItem.valueField, i, 2)
                self.parameterItems.append(newItem)
                i += 1

        self.UpdateInstanceView()

    def UpdateInstanceView(self):
        if not self.programInstance.program.description:
            text = "No description provided."
        else:
            text = self.programInstance.program.description
        if self._description.toPlainText() != text:
            self._description.setPlainText(text)

        self.programNameWidget.setText(self.programInstance.program.name)

        if self.ownsInstance:
            self.runButton.setVisible(not AppGlobals.ProgramRunner().IsRunning(self.programInstance))
            self._stopButton.setVisible(AppGlobals.ProgramRunner().IsRunning(self.programInstance))
        else:
            self.runButton.setVisible(True)
            self._stopButton.setVisible(False)

        for item in self.parameterItems:
            item.UpdateFields()
            if self._showAllParameters:
                item.setVisible(True)
                item.visibilityToggle.setVisible(self._editParameterVisibility)
            else:
                item.setVisible(self.programInstance.parameterVisibility[item.parameter])
                item.visibilityToggle.setVisible(False)

    def RunProgram(self):
        if self.ownsInstance:
            AppGlobals.ProgramRunner().Run(self.programInstance, None)
        else:
            AppGlobals.ProgramRunner().Run(self.programInstance.Clone(), None)

    def StopProgram(self):
        AppGlobals.ProgramRunner().Stop(self.programInstance)


class ProgramParameterItem:
    def __init__(self, parameter: Parameter, instance: ProgramInstance):
        self.parameter = parameter
        self._programInstance = instance
        self.parameterName = QLabel()

        self.visibilityToggle = VisibilityToggle()
        self.visibilityToggle.clicked.connect(self.ToggleVisibility)

        self.valueField = DataValueWidget(self.parameter.dataType, self.parameter.listType)
        self.valueField.dataChanged.connect(self.UpdateParameterValue)

        self.UpdateFields()

    def deleteLater(self):
        self.visibilityToggle.deleteLater()
        self.valueField.deleteLater()
        self.parameterName.deleteLater()

    def setVisible(self, visible):
        self.visibilityToggle.setVisible(visible)
        self.valueField.setVisible(visible)
        self.parameterName.setVisible(visible)

    def ToggleVisibility(self):
        self._programInstance.parameterVisibility[self.parameter] = not self._programInstance.parameterVisibility[
            self.parameter]
        AppGlobals.Instance().onChipDataModified.emit()
        self.UpdateFields()

    def UpdateParameterValue(self):
        lastValue = self._programInstance.parameterValues[self.parameter]

        if self.parameter.dataType is DataType.INTEGER:
            value = self.parameter.ClampInteger(self.valueField.GetData())
        elif self.parameter.dataType is DataType.FLOAT:
            value = self.parameter.ClampFloat(self.valueField.GetData())
        else:
            value = self.valueField.GetData()
        self._programInstance.parameterValues[self.parameter] = value

        if self._programInstance.parameterValues[self.parameter] != lastValue:
            AppGlobals.Instance().onChipDataModified.emit()

    def UpdateFields(self):
        self.parameterName.setText(self.parameter.name)

        if self._programInstance.parameterVisibility[self.parameter]:
            self.visibilityToggle.setIcon(QIcon("Assets/Images/eyeOpen.png"))
        else:
            self.visibilityToggle.setIcon(QIcon("Assets/Images/eyeClosed.png"))

        self.valueField.Update(self._programInstance.parameterValues[self.parameter])


class VisibilityToggle(QToolButton):
    pass
