from typing import List

from Model.Program.Program import Program
from Model.Program.Parameter import Parameter
from Model.Program.Data import DataType

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton, QLineEdit, \
    QComboBox, QSpinBox, QDoubleSpinBox, QToolButton, QGridLayout
from PySide6.QtCore import Signal, Qt
from UI.ProgramViews.ChipDataSelection import ChipDataSelection


class ParameterEditor(QFrame):
    onParametersChanged = Signal()

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

        self.items: List[ParameterEditorItem] = []

        self._temporaryParameters = program.parameters.copy()

        self.Update()

    def AddParameter(self):
        self._temporaryParameters.append(Parameter())
        self.onParametersChanged.emit()
        self.Update()

    def Update(self):
        lastPos = self._listArea.verticalScrollBar().sliderPosition()
        for item in self.items:
            item.deleteLater()
        self.items.clear()
        for parameter in self._temporaryParameters:
            newItem = ParameterEditorItem(parameter)
            newItem.onRemoveParameter.connect(self.RemoveParameter)
            newItem.onMoveParameterUp.connect(self.MoveParameterUp)
            newItem.onMoveParameterDown.connect(self.MoveParameterDown)
            newItem.onChanged.connect(self.onParametersChanged.emit)
            self._itemLayout.addWidget(newItem)
            self.items.append(newItem)
        self._listArea.verticalScrollBar().setSliderPosition(lastPos)
        self._listArea.updateGeometry()

    def RemoveParameter(self, parameter: Parameter):
        self._temporaryParameters.remove(parameter)
        self.onParametersChanged.emit()
        self.Update()

    def MoveParameterUp(self, parameter: Parameter):
        index = self._temporaryParameters.index(parameter)
        self._temporaryParameters.remove(parameter)
        self._temporaryParameters.insert(index - 1, parameter)
        self.onParametersChanged.emit()
        self.Update()

    def MoveParameterDown(self, parameter: Parameter):
        index = self._temporaryParameters.index(parameter)
        self._temporaryParameters.remove(parameter)
        self._temporaryParameters.insert(index + 1, parameter)
        self.onParametersChanged.emit()
        self.Update()

    def Save(self):
        self._program.parameters = self._temporaryParameters
        self._temporaryParameters = self._program.parameters.copy()
        for item in self.items:
            item.UpdateParameter()


class ParameterEditorItem(QFrame):
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

        self._defaultValve = ChipDataSelection(DataType.VALVE)
        self._defaultValve.currentIndexChanged.connect(self.OnChanged)

        self._defaultProgram = ChipDataSelection(DataType.PROGRAM)
        self._defaultProgram.currentIndexChanged.connect(self.OnChanged)

        self._defaultProgramPreset = ChipDataSelection(DataType.PROGRAM_PRESET)
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

        self.SetFieldsFromParameter()

    def SetFieldsFromParameter(self):
        self._nameField.setText(self.parameter.name)

        self._dataTypeField.setCurrentText(self.parameter.dataType.ToString())

        minFloat, maxFloat = self.parameter.minimumFloat, self.parameter.maximumFloat
        minInt, maxInt = self.parameter.minimumInteger, self.parameter.maximumInteger
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
        if self._defaultInteger.value() != self.parameter.defaultValueDict[DataType.INTEGER]:
            self._defaultInteger.setValue(self.parameter.defaultValueDict[DataType.INTEGER])
        if self._defaultFloat.value() != self.parameter.defaultValueDict[DataType.FLOAT]:
            self._defaultFloat.setValue(self.parameter.defaultValueDict[DataType.FLOAT])

        if self._defaultBoolean.currentData() != self.parameter.defaultValueDict[DataType.BOOLEAN]:
            self._defaultBoolean.setCurrentText(str(self.parameter.defaultValueDict[DataType.BOOLEAN]))

        if self._defaultString.text() != self.parameter.defaultValueDict[DataType.STRING]:
            self._defaultString.setText(self.parameter.defaultValueDict[DataType.STRING])

        self._defaultValve.Select(self.parameter.defaultValueDict[DataType.VALVE])
        self._defaultProgram.Select(self.parameter.defaultValueDict[DataType.PROGRAM])
        self._defaultProgramPreset.Select(self.parameter.defaultValueDict[DataType.PROGRAM_PRESET])

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
        self.parameter.name = self._nameField.text()
        self.parameter.dataType = self._dataTypeField.currentData()

        self.parameter.defaultValueDict[DataType.INTEGER] = self._defaultInteger.value()
        self.parameter.defaultValueDict[DataType.FLOAT] = self._defaultFloat.value()
        self.parameter.defaultValueDict[DataType.BOOLEAN] = self._defaultBoolean.currentData()
        self.parameter.defaultValueDict[DataType.STRING] = self._defaultString.text()
        self.parameter.defaultValueDict[DataType.VALVE] = self._defaultValve.currentData()
        self.parameter.defaultValueDict[DataType.PROGRAM] = self._defaultProgram.currentData()
        self.parameter.defaultValueDict[DataType.PROGRAM_PRESET] = self._defaultProgramPreset.currentData()

        self.parameter.minimumInteger = self._minimumInteger.value()
        self.parameter.maximumInteger = self._maximumInteger.value()
        self.parameter.minimumFloat = self._minimumFloat.value()
        self.parameter.maximumFloat = self._maximumFloat.value()

        self.parameter.ValidateDefaultValues()

        self.SetFieldsFromParameter()
