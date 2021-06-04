from typing import List
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QVBoxLayout, \
    QLabel, QLineEdit, QFrame, QComboBox, QSpinBox, QDoubleSpinBox, QGridLayout, QScrollArea, QToolButton
from PySide6.QtCore import Qt, Signal
from Model.Program.Program import Program
from Model.Program.Parameter import Parameter, DataType
from UI.AppGlobals import AppGlobals
from UI.ProgramEditor.CodeTextEditor import CodeTextEditor


class ProgramEditorTab(QWidget):
    def __init__(self, program: Program):
        super().__init__()

        AppGlobals.Instance().onChipOpened.connect(self.CheckForProgram)
        AppGlobals.Instance().onChipModified.connect(self.CheckForProgram)

        self.program = program
        self.modified = False
        self.codeEditor = CodeTextEditor()

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._parametersPanel = ParametersPanel(program)
        self._parametersPanel.onChanged.connect(self.ProgramEdited)

        layout.addWidget(self._parametersPanel, stretch=0)
        layout.addWidget(self.codeEditor, stretch=1)

        self.codeEditor.SetCode(self.program.script)

        self.codeEditor.codeChanged.connect(self.ProgramEdited)

    def SaveProgram(self):
        self.program.script = self.codeEditor.Code()
        for item in self._parametersPanel.items:
            item.UpdateParameter()
        self.modified = False
        AppGlobals.Instance().onChipModified.emit()

    def ProgramEdited(self):
        self.modified = True

    def CheckForProgram(self):
        if self.program not in AppGlobals.Chip().programs:
            self.deleteLater()


class ParametersPanel(QFrame):
    onChanged = Signal()

    def __init__(self, program: Program):
        super().__init__()
        self._program = program

        parametersLabel = QLabel("Parameters")
        newParameterButton = QPushButton("Add Parameter")
        newParameterButton.clicked.connect(self.AddParameter)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        titleLayout = QHBoxLayout()
        titleLayout.addWidget(parametersLabel)
        titleLayout.addWidget(newParameterButton)
        layout.addLayout(titleLayout)

        self._listArea = QScrollArea()
        self._listArea.setWidgetResizable(True)
        self._listArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._listArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self._listArea, stretch=1)
        listWidget = QFrame()
        self._itemLayout = QVBoxLayout()
        self._itemLayout.setContentsMargins(0, 0, 0, 0)
        self._itemLayout.setSpacing(0)
        self._itemLayout.setAlignment(Qt.AlignTop)
        listWidget.setLayout(self._itemLayout)
        self.setLayout(layout)
        self._listArea.setWidget(listWidget)

        self.items: List[ParameterItem] = []

        self.Update()

    def AddParameter(self):
        self._program.parameters.append(Parameter())
        self.onChanged.emit()
        self.Update()

    def Update(self):
        lastPos = self._listArea.verticalScrollBar().sliderPosition()
        for item in self.items:
            item.deleteLater()
        self.items.clear()
        for parameter in self._program.parameters:
            newItem = ParameterItem(parameter)
            newItem.onRemoveParameter.connect(self.RemoveParameter)
            newItem.onMoveParameterUp.connect(self.MoveParameterUp)
            newItem.onMoveParameterDown.connect(self.MoveParameterDown)
            newItem.onChanged.connect(self.onChanged.emit)
            self._itemLayout.addWidget(newItem)
            self.items.append(newItem)
        self._listArea.verticalScrollBar().setSliderPosition(lastPos)
        self._listArea.updateGeometry()

    def RemoveParameter(self, parameter: Parameter):
        self._program.parameters.remove(parameter)
        self.onChanged.emit()
        self.Update()

    def MoveParameterUp(self, parameter: Parameter):
        index = self._program.parameters.index(parameter)
        self._program.parameters.remove(parameter)
        self._program.parameters.insert(index - 1, parameter)
        self.onChanged.emit()
        self.Update()

    def MoveParameterDown(self, parameter: Parameter):
        index = self._program.parameters.index(parameter)
        self._program.parameters.remove(parameter)
        self._program.parameters.insert(index + 1, parameter)
        self.onChanged.emit()
        self.Update()


class ParameterItem(QFrame):
    onRemoveParameter = Signal(Parameter)
    onMoveParameterUp = Signal(Parameter)
    onMoveParameterDown = Signal(Parameter)
    onChanged = Signal()

    def __init__(self, parameter: Parameter):
        super().__init__()

        self.parameter = parameter

        deleteButton = QToolButton()
        deleteButton.setText("X")
        deleteButton.clicked.connect(lambda: self.onRemoveParameter.emit(self.parameter))
        upButton = QToolButton()
        upButton.setText("\u2191")
        upButton.clicked.connect(lambda: self.onMoveParameterUp.emit(self.parameter))
        downButton = QToolButton()
        downButton.setText("\u2193")
        downButton.clicked.connect(lambda: self.onMoveParameterDown.emit(self.parameter))

        buttonsLayout = QVBoxLayout()
        buttonsLayout.setAlignment(Qt.AlignTop)
        buttonsLayout.setSpacing(0)
        buttonsLayout.setContentsMargins(0, 0, 0, 0)
        buttonsLayout.addWidget(deleteButton)
        buttonsLayout.addWidget(upButton)
        buttonsLayout.addWidget(downButton)

        self._nameLabel = QLabel("Name")
        self._nameField = QLineEdit()
        self._nameField.textChanged.connect(self.OnChanged)

        self._dataTypeLabel = QLabel("Data Type")
        self._dataTypeField = QComboBox()
        for dataType in DataType:
            self._dataTypeField.addItem(dataType.ToString(), userData=dataType)
        self._dataTypeField.currentIndexChanged.connect(self.OnChanged)

        self._defaultValueLabel = QLabel("Default Value")
        self._defaultInteger = QSpinBox()
        self._defaultInteger.valueChanged.connect(self.OnChanged)

        self._defaultFloat = QDoubleSpinBox()
        self._defaultFloat.valueChanged.connect(self.OnChanged)

        self._defaultBoolean = QComboBox()
        self._defaultBoolean.addItem("True", True)
        self._defaultBoolean.addItem("False", False)
        self._defaultBoolean.currentIndexChanged.connect(self.OnChanged)

        self._defaultString = QLineEdit()
        self._defaultString.textChanged.connect(self.OnChanged)

        self._defaultValve = QComboBox()
        self._defaultValve.currentIndexChanged.connect(self.OnChanged)

        self._defaultProgram = QComboBox()
        self._defaultProgram.currentIndexChanged.connect(self.OnChanged)

        self._defaultProgramPreset = QComboBox()
        self._defaultProgramPreset.currentIndexChanged.connect(self.OnChanged)

        self._minimumLabel = QLabel("Minimum")
        self._minimumFloat = QDoubleSpinBox()
        self._minimumFloat.valueChanged.connect(self.OnChanged)
        self._minimumInteger = QSpinBox()
        self._minimumInteger.valueChanged.connect(self.OnChanged)

        self._maximumLabel = QLabel("Maximum")
        self._maximumFloat = QDoubleSpinBox()
        self._maximumFloat.valueChanged.connect(self.OnChanged)
        self._maximumInteger = QSpinBox()
        self._maximumInteger.valueChanged.connect(self.OnChanged)

        gridLayout = QGridLayout()
        gridLayout.setAlignment(Qt.AlignTop)
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.setSpacing(0)
        gridLayout.addWidget(self._nameLabel, 0, 0)
        gridLayout.addWidget(self._nameField, 0, 1)
        gridLayout.addWidget(self._dataTypeLabel, 1, 0)
        gridLayout.addWidget(self._dataTypeField, 1, 1)
        gridLayout.addWidget(self._defaultValueLabel, 2, 0)

        for defaultField in [self._defaultInteger, self._defaultFloat, self._defaultBoolean, self._defaultString,
                             self._defaultValve, self._defaultProgram, self._defaultProgramPreset]:
            gridLayout.addWidget(defaultField, 2, 1)

        gridLayout.addWidget(self._minimumLabel, 3, 0)
        gridLayout.addWidget(self._minimumInteger, 3, 1)
        gridLayout.addWidget(self._minimumFloat, 3, 1)
        gridLayout.addWidget(self._maximumLabel, 4, 0)
        gridLayout.addWidget(self._maximumInteger, 4, 1)
        gridLayout.addWidget(self._maximumFloat, 4, 1)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(buttonsLayout)
        layout.addLayout(gridLayout)
        self.setLayout(layout)

        self.UpdateFromParameter()

    def UpdateFromParameter(self):
        if self._nameField.text() != self.parameter.GetName():
            self._nameField.setText(self.parameter.GetName())

        if self._dataTypeField.currentData() != self.parameter.GetDataType():
            self._dataTypeField.setCurrentText(self.parameter.GetDataType().ToString())

        minFloat, maxFloat = self.parameter.GetFloatBounds()
        minInt, maxInt = self.parameter.GetIntegerBounds()
        self._minimumFloat.setRange(-2 ** 30, maxFloat)
        self._maximumFloat.setRange(minFloat, 2 ** 30)
        self._minimumInteger.setRange(-2 ** 30, maxInt)
        self._maximumInteger.setRange(minInt, 2 ** 30)
        if self._minimumFloat.value() != minFloat:
            self._minimumFloat.setValue(minFloat)
        if self._maximumFloat.value() != maxFloat:
            self._maximumFloat.setValue(maxFloat)
        if self._minimumInteger.value() != minInt:
            self._minimumInteger.setValue(minInt)
        if self._maximumInteger.value() != maxInt:
            self._maximumInteger.setValue(maxInt)

        self._defaultInteger.setRange(minInt, maxInt)
        self._defaultFloat.setRange(minFloat, maxFloat)
        if self._defaultInteger.value() != self.parameter.GetDefaultValue(DataType.INTEGER):
            self._defaultInteger.setValue(self.parameter.GetDefaultValue(DataType.INTEGER))
        if self._defaultFloat.value() != self.parameter.GetDefaultValue(DataType.FLOAT):
            self._defaultFloat.setValue(self.parameter.GetDefaultValue(DataType.FLOAT))

        if self._defaultBoolean.currentData() != self.parameter.GetDefaultValue(DataType.BOOLEAN):
            self._defaultBoolean.setCurrentText(str(self.parameter.GetDefaultValue(DataType.BOOLEAN)))

        if self._defaultString.text() != self.parameter.GetDefaultValue(DataType.STRING):
            self._defaultString.setText(self.parameter.GetDefaultValue(DataType.STRING))

        self._defaultValve.blockSignals(True)
        self._defaultValve.clear()
        self._defaultValve.addItem("None", None)
        for item in AppGlobals.Chip().valves:
            self._defaultValve.addItem(item.name, item)
        if self.parameter.GetDefaultValue(DataType.VALVE) not in AppGlobals.Chip().valves:
            self.parameter.SetDefaultValue(None, DataType.VALVE)
        for index in range(self._defaultValve.count()):
            if self._defaultValve.itemData(index) is self.parameter.GetDefaultValue(DataType.VALVE):
                self._defaultValve.setCurrentIndex(index)
                break
        self._defaultValve.blockSignals(False)

        self._defaultProgram.blockSignals(True)
        self._defaultProgram.clear()
        self._defaultProgram.addItem("None", None)
        for item in AppGlobals.Chip().programs:
            self._defaultProgram.addItem(item.name, item)
        if self.parameter.GetDefaultValue(DataType.PROGRAM) not in AppGlobals.Chip().programs:
            self.parameter.SetDefaultValue(None, DataType.PROGRAM)
        for index in range(self._defaultProgram.count()):
            if self._defaultProgram.itemData(index) is self.parameter.GetDefaultValue(DataType.PROGRAM):
                self._defaultProgram.setCurrentIndex(index)
                break
        self._defaultProgram.blockSignals(False)

        self._defaultProgramPreset.blockSignals(True)
        self._defaultProgramPreset.clear()
        self._defaultProgramPreset.addItem("None", None)
        for item in AppGlobals.Chip().programPresets:
            self._defaultProgramPreset.addItem(item.name, item)
        if self.parameter.GetDefaultValue(DataType.PROGRAM_PRESET) not in AppGlobals.Chip().programPresets:
            self.parameter.SetDefaultValue(None, DataType.PROGRAM_PRESET)
        for index in range(self._defaultProgramPreset.count()):
            if self._defaultProgramPreset.itemData(index) is self.parameter.GetDefaultValue(DataType.PROGRAM_PRESET):
                self._defaultProgramPreset.setCurrentIndex(index)
                break
        self._defaultProgramPreset.blockSignals(False)

        self.UpdateVisibility()

    def UpdateVisibility(self):
        self._defaultInteger.setVisible(self._dataTypeField.currentData() is DataType.INTEGER)
        self._defaultFloat.setVisible(self._dataTypeField.currentData() is DataType.FLOAT)
        self._defaultBoolean.setVisible(self._dataTypeField.currentData() is DataType.BOOLEAN)
        self._defaultString.setVisible(self._dataTypeField.currentData() is DataType.STRING)
        self._defaultValve.setVisible(self._dataTypeField.currentData() is DataType.VALVE)
        self._defaultProgram.setVisible(self._dataTypeField.currentData() is DataType.PROGRAM)
        self._defaultProgramPreset.setVisible(self._dataTypeField.currentData() is DataType.PROGRAM_PRESET)

        self._minimumLabel.setVisible(self._dataTypeField.currentData() in [DataType.INTEGER, DataType.FLOAT])
        self._maximumLabel.setVisible(self._dataTypeField.currentData() in [DataType.INTEGER, DataType.FLOAT])
        self._minimumInteger.setVisible(self._dataTypeField.currentData() is DataType.INTEGER)
        self._maximumInteger.setVisible(self._dataTypeField.currentData() is DataType.INTEGER)
        self._minimumFloat.setVisible(self._dataTypeField.currentData() is DataType.FLOAT)
        self._maximumFloat.setVisible(self._dataTypeField.currentData() is DataType.FLOAT)
        self._minimumLabel.setVisible(self._dataTypeField.currentData() in [DataType.INTEGER, DataType.FLOAT])
        self._maximumLabel.setVisible(self._dataTypeField.currentData() in [DataType.INTEGER, DataType.FLOAT])

    def OnChanged(self):
        self.UpdateVisibility()
        self._minimumFloat.setMaximum(self._maximumFloat.value())
        self._maximumFloat.setMinimum(self._minimumFloat.value())
        self._minimumInteger.setMaximum(self._maximumInteger.value())
        self._maximumInteger.setMinimum(self._minimumInteger.value())
        self._defaultInteger.setRange(self._minimumInteger.value(), self._maximumInteger.value())
        self._defaultFloat.setRange(self._minimumFloat.value(), self._maximumFloat.value())
        self.onChanged.emit()

    def UpdateParameter(self):
        self.parameter.SetName(self._nameField.text())
        self.parameter.SetDataType(self._dataTypeField.currentData())

        self.parameter.SetDefaultValue(self._defaultInteger.value(), DataType.INTEGER)
        self.parameter.SetDefaultValue(self._defaultFloat.value(), DataType.FLOAT)
        self.parameter.SetDefaultValue(self._defaultBoolean.currentData(), DataType.BOOLEAN)
        self.parameter.SetDefaultValue(self._defaultString.text(), DataType.STRING)
        self.parameter.SetDefaultValue(self._defaultValve.currentData(), DataType.VALVE)
        self.parameter.SetDefaultValue(self._defaultProgram.currentData(), DataType.PROGRAM)
        self.parameter.SetDefaultValue(self._defaultProgramPreset.currentData(), DataType.PROGRAM_PRESET)

        self.parameter.SetIntegerBounds(self._minimumInteger.value(),
                                        self._maximumInteger.value())
        self.parameter.SetFloatBounds(self._minimumFloat.value(),
                                      self._maximumFloat.value())

        self.UpdateFromParameter()
