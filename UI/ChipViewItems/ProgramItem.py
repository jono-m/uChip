import traceback
import typing
import pathlib
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFormLayout, QLineEdit, \
    QSpinBox, QDoubleSpinBox, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QScrollArea, QFrame
from PySide6.QtCore import QRectF, Signal, Qt

import ucscript
from UI.UIMaster import UIMaster
from UI.CustomGraphicsView import CustomGraphicsViewItem
from Data.Chip import Program
from Data.ProgramCompilation import IsTypeValidList, IsTypeValidOptions, DoTypesMatch, \
    NoneValueForType


# The most complicated/involved chip item. Lots of components!
class ProgramItem(CustomGraphicsViewItem):
    def __init__(self, program: Program):
        self.program = program

        # Set up the inspector for this item:
        inspectorWidget = QWidget()
        inspectorWidgetLayout = QVBoxLayout()
        inspectorWidget.setLayout(inspectorWidgetLayout)

        # Program name field
        nameAndSourceLayout = QFormLayout()
        inspectorWidget.layout().addLayout(nameAndSourceLayout)
        self.nameField = QLineEdit()
        self.nameField.textChanged.connect(self.RecordChanges)
        nameAndSourceLayout.addRow("Name", self.nameField)

        # Program source field with browse button.
        self.pathWidget = QLineEdit()
        self.pathWidget.textChanged.connect(self.RecordChanges)
        self.browseButton = QPushButton("...")
        self.browseButton.clicked.connect(self.BrowseForProgram)
        sourceLayout = QHBoxLayout()
        sourceLayout.addWidget(self.pathWidget, stretch=1)
        sourceLayout.addWidget(self.browseButton, stretch=0)
        nameAndSourceLayout.addRow("Path", sourceLayout)

        # Program scale field
        self.scaleWidget = QDoubleSpinBox()
        self.scaleWidget.setMinimum(0.1)
        self.scaleWidget.setMaximum(10.0)
        self.scaleWidget.setSingleStep(0.1)
        self.scaleWidget.valueChanged.connect(self.RecordChanges)
        nameAndSourceLayout.addRow("Display scale", self.scaleWidget)

        # Parameters will be kept in this layout for the inspector. All parameters are shown here.
        self.parametersLayout = QGridLayout()
        self.parametersLayout.setContentsMargins(0, 0, 0, 0)
        self.parametersLayout.setSpacing(0)
        parametersWidget = QFrame()
        parametersWidget.setFrameShape(QFrame.Shape.Panel)
        parametersWidget.setFrameShadow(QFrame.Sunken)
        parametersWidget.setLineWidth(2)
        parametersWidget.setStyleSheet("""
        QLabel {
        padding: 5px;
        }""")
        parametersWidget.setLayout(self.parametersLayout)
        inspectorWidget.layout().addWidget(parametersWidget)

        # Parameters will be kept in this layout for the item. Only visible parameters will be
        # shown.
        self.visibleParametersLayout = QGridLayout()
        self.visibleParametersLayout.setContentsMargins(0, 0, 0, 0)
        self.visibleParametersLayout.setSpacing(0)
        visibleParametersWidget = QFrame()
        visibleParametersWidget.setFrameShape(QFrame.Shape.Panel)
        visibleParametersWidget.setFrameShadow(QFrame.Sunken)
        visibleParametersWidget.setLineWidth(2)
        visibleParametersWidget.setStyleSheet("""
        QLabel {
        padding: 5px;
        }""")
        visibleParametersWidget.setLayout(self.visibleParametersLayout)
        inspectorWidget.layout().addWidget(visibleParametersWidget)

        # Functions will be kept in this layout for the item. All zero-argument functions will be
        # shown here as buttons.
        self.functionsLayout = QGridLayout()
        self.functionsLayout.setContentsMargins(0, 0, 0, 0)
        functionsWidget = QWidget()
        functionsWidget.setLayout(self.functionsLayout)

        # Widget sets for each parameter.
        self.parameterWidgetSets: typing.List[ParameterWidgetSet] = []

        # Widget sets for each function
        self.functionWidgetSets: typing.List[FunctionWidgetSet] = []

        # Actual item widget
        itemWidget = QWidget()
        self.nameWidget = QLabel()
        self.nameWidget.setAlignment(Qt.AlignCenter)
        itemLayout = QVBoxLayout()
        itemWidget.setLayout(itemLayout)
        itemWidget.layout().addWidget(self.nameWidget)
        itemWidget.layout().addWidget(visibleParametersWidget)
        itemWidget.layout().addWidget(functionsWidget)

        # Compilation/program error reporting
        self.messageArea = MessageArea()
        self.clearMessagesButton = QPushButton("Clear Messages")
        self.clearMessagesButton.clicked.connect(self.ClearMessages)
        spacerWidget = QLabel()
        spacerWidget.setStyleSheet("background-color: #999999;")
        spacerWidget.setFixedHeight(1)
        itemWidget.layout().addWidget(spacerWidget)
        itemWidget.layout().addWidget(self.messageArea)
        itemWidget.layout().addWidget(self.clearMessagesButton)

        super().__init__("Program", itemWidget, inspectorWidget)
        super().SetRect(QRectF(*program.position, 0, 0))
        self.isResizable = False

    def ClearMessages(self):
        compiled = UIMaster.GetCompiledProgram(self.program)
        compiled.messages.clear()

    def SetEnabled(self, state):
        for c in self.itemProxy.widget().children():
            if isinstance(c, QWidget) and c != self.messageArea and c != self.clearMessagesButton:
                c.setEnabled(state)

    @staticmethod
    def Browse(parent: QWidget):
        programToAdd = QFileDialog.getOpenFileName(parent, "Browse for program",
                                                   filter="uChip program (*.py)")
        if programToAdd[0]:
            return pathlib.Path(programToAdd[0])

    def BrowseForProgram(self):
        path = self.Browse(self.pathWidget)
        if path:
            self.program.path = path

    # Called whenever the user changes the program parameters/name/visibility etc.
    def RecordChanges(self):
        if self.isUpdating:
            return

        # Store the program path, name, and widget size.
        self.program.path = pathlib.Path(self.pathWidget.text())
        self.program.name = self.nameField.text()
        rect = self.GetRect()
        self.program.position = [rect.x(), rect.y()]

        # Record visibility changes
        for parameterSymbol, parameterWidgetSet in zip(self.program.parameterValues,
                                                       self.parameterWidgetSets):
            self.program.parameterVisibility[
                parameterSymbol] = parameterWidgetSet.inspectorVisibilityToggle.isChecked()

        self.program.scale = self.scaleWidget.value()

        UIMaster.Instance().modified = True

    def Update(self):
        # Called regularly to make sure that the fields match the backing program.
        if self.program.name != self.nameField.text():
            self.nameField.setText(self.program.name)
        if self.program.name != self.nameWidget.text():
            self.nameWidget.setText("<b>%s</b>" % self.program.name)
        path = str(self.program.path.absolute())
        if path != self.pathWidget.text():
            self.pathWidget.setText(path)

        compiled = UIMaster.GetCompiledProgram(self.program)
        self.messageArea.Update(compiled.messages)
        if self.scaleWidget.value() != self.program.scale:
            self.scaleWidget.setValue(self.program.scale)

        # Update the parameter and function widgets. These are complicated, so they have their own
        # methods for clarity.
        self.UpdateParameters()
        self.UpdateFunctions()

        self.itemProxy.adjustSize()
        self.itemProxy.setScale(self.program.scale)
        self.UpdateGeometry()

    def UpdateParameters(self):
        # Get the latest compiled program version
        compiled = UIMaster.GetCompiledProgram(self.program)

        # Make sure we have the right number of parameter widget sets in the layout. First, add
        # needed widget sets.
        for i in range(len(self.parameterWidgetSets), len(compiled.parameters)):
            newSet = ParameterWidgetSet()
            self.parameterWidgetSets.append(newSet)
            newSet.inspectorNameLabel.setStyleSheet(
                "background-color: " + (
                    "rgba(0, 0, 0, 0.2)" if i % 2 == 0 else "rgba(0, 0, 0, 0.1)"))
            self.parametersLayout.addWidget(newSet.inspectorNameLabel, i, 0)
            self.parametersLayout.addWidget(newSet.inspectorVisibilityToggle, i, 2)
            self.visibleParametersLayout.addWidget(newSet.itemNameLabel, i, 0)
            newSet.itemNameLabel.setStyleSheet(
                "background-color: " + (
                    "rgba(0, 0, 0, 0.2)" if i % 2 == 0 else "rgba(0, 0, 0, 0.1)"))
            newSet.inspectorVisibilityToggle.setCheckable(True)
            newSet.inspectorVisibilityToggle.toggled.connect(self.RecordChanges)

        # Then, remove excessive widget sets
        for i in range(len(compiled.parameters), len(self.parameterWidgetSets)):
            self.parameterWidgetSets[i - 1].inspectorNameLabel.deleteLater()
            self.parameterWidgetSets[i - 1].inspectorVisibilityToggle.deleteLater()
            self.parameterWidgetSets[i - 1].itemNameLabel.deleteLater()
            self.parameterWidgetSets[i - 1].inspectorValueWidget.deleteLater()
            self.parameterWidgetSets[i - 1].itemValueWidget.deleteLater()
        self.parameterWidgetSets = self.parameterWidgetSets[:len(compiled.parameters)]

        # Update widget sets. Enumerated so that we know where each widget is in the layout in case
        # they need to be replaced.
        for i, (parameterSymbol, parameterWidgetSet) in enumerate(
                zip(compiled.parameters, self.parameterWidgetSets)):
            # Ensure that the value fields match the type given.
            parameterType = compiled.parameters[parameterSymbol].parameterType
            if not DoTypesMatch(parameterWidgetSet.inspectorValueWidget.parameterType,
                                parameterType):
                # If the types don't match (or they haven't been set, i.e. parameterType is None),
                # we need to rebuild the value fields.
                self.parameterWidgetSets[i].inspectorValueWidget.deleteLater()
                self.parameterWidgetSets[i].itemValueWidget.deleteLater()

                # Inspector value field is the master. Changes to the item value field instead
                # change the inspector value field, which is what actually reports the change to
                # the backing program.
                inspectorWidget = ParameterValueWidget(parameterType)

                def RecordValueChange(ps=parameterSymbol, w=inspectorWidget):
                    self.program.parameterValues[ps] = w.GetValue()

                inspectorWidget.OnValueChanged.connect(RecordValueChange)
                itemWidget = ParameterValueWidget(parameterType)

                def RecordValueChange(ps=parameterSymbol, w=itemWidget):
                    self.program.parameterValues[ps] = w.GetValue()

                itemWidget.OnValueChanged.connect(RecordValueChange)

                # Add them to the layouts.
                self.parameterWidgetSets[i].inspectorValueWidget = inspectorWidget
                self.parameterWidgetSets[i].itemValueWidget = itemWidget
                self.parametersLayout.addWidget(inspectorWidget, i, 1)
                self.visibleParametersLayout.addWidget(itemWidget, i, 1)

            # Set the values to be the current value.
            parameterWidgetSet.inspectorValueWidget.SetValue(
                self.program.parameterValues[parameterSymbol])
            parameterWidgetSet.itemValueWidget.SetValue(
                self.program.parameterValues[parameterSymbol])

            # Set name fields and visibility
            parameterWidgetSet.itemNameLabel.setText(
                compiled.parameters[parameterSymbol].displayName)
            parameterWidgetSet.inspectorNameLabel.setText(
                compiled.parameters[parameterSymbol].displayName)
            parameterWidgetSet.inspectorVisibilityToggle.setText(
                "O" if self.program.parameterVisibility[parameterSymbol] else "X")
            parameterWidgetSet.inspectorVisibilityToggle.setChecked(
                self.program.parameterVisibility[parameterSymbol])
            parameterWidgetSet.itemNameLabel.setVisible(
                self.program.parameterVisibility[parameterSymbol])
            parameterWidgetSet.itemValueWidget.setVisible(
                self.program.parameterVisibility[parameterSymbol])

    def UpdateFunctions(self):
        # Get the latest compiled program version
        compiled = UIMaster.GetCompiledProgram(self.program)

        # Make sure we have the right number of function widget sets in the layout. First, add
        # needed widget sets.
        def AddFunctionWidgetSet(index: int):
            newSet = FunctionWidgetSet()
            self.functionWidgetSets.append(newSet)
            self.functionsLayout.addWidget(newSet.startButton, index, 0, 1, 6)
            self.functionsLayout.addWidget(newSet.stopButton, index, 6)
            self.functionsLayout.addWidget(newSet.pauseButton, index, 7)
            self.functionsLayout.addWidget(newSet.resumeButton, index, 7)
            newSet.startButton.clicked.connect(lambda: self.StartFunction(index))
            newSet.stopButton.clicked.connect(
                lambda: compiled.programFunctions[compiled.showableFunctions[index]].Stop())
            newSet.pauseButton.clicked.connect(
                lambda: compiled.programFunctions[compiled.showableFunctions[index]].Pause())
            newSet.resumeButton.clicked.connect(
                lambda: compiled.programFunctions[compiled.showableFunctions[index]].Resume())

        for i in range(len(self.functionWidgetSets), len(compiled.showableFunctions)):
            AddFunctionWidgetSet(i)

        # Remove excessive widget sets
        for i in range(len(compiled.showableFunctions), len(self.functionWidgetSets)):
            self.functionWidgetSets[i - 1].startButton.deleteLater()
            self.functionWidgetSets[i - 1].stopButton.deleteLater()
            self.functionWidgetSets[i - 1].pauseButton.deleteLater()
            self.functionWidgetSets[i - 1].resumeButton.deleteLater()
        self.functionWidgetSets = self.functionWidgetSets[:len(self.functionWidgetSets)]

        # Update widget sets
        for functionSymbol, functionWidgetSet in zip(compiled.showableFunctions,
                                                     self.functionWidgetSets):
            functionWidgetSet.startButton.setText(
                compiled.programFunctions[functionSymbol].functionName)
            functionWidgetSet.startButton.setEnabled(functionSymbol not in compiled.asyncFunctions)
            functionWidgetSet.stopButton.setVisible(functionSymbol in compiled.asyncFunctions)
            functionWidgetSet.pauseButton.setVisible(functionSymbol in compiled.asyncFunctions and
                                                     not compiled.asyncFunctions[
                                                         functionSymbol].paused)
            functionWidgetSet.resumeButton.setVisible(functionSymbol in compiled.asyncFunctions and
                                                      compiled.asyncFunctions[
                                                          functionSymbol].paused)

    def StartFunction(self, index):
        compiled = UIMaster.GetCompiledProgram(self.program)
        compiled.programFunctions[compiled.showableFunctions[index]]()

    def Duplicate(self):
        newProgram = Program()
        newProgram.name = self.program.name
        newProgram.path = self.program.path
        newProgram.parameterValues = self.program.parameterValues.copy()
        newProgram.parameterVisibility = self.program.parameterVisibility.copy()
        UIMaster.Instance().currentChip.programs.append(newProgram)
        UIMaster.Instance().modified = True
        return ProgramItem(newProgram)

    def SetRect(self, rect: QRectF):
        super().SetRect(QRectF(rect))
        self.RecordChanges()

    def OnRemoved(self):
        UIMaster.Instance().currentChip.programs.remove(self.program)
        UIMaster.Instance().RemoveProgram(self.program)
        UIMaster.Instance().modified = True


# Convenience structure that stores the widgets for a single parameter.
class ParameterWidgetSet:
    def __init__(self):
        self.inspectorValueWidget = ParameterValueWidget()
        self.inspectorNameLabel = QLabel()
        self.inspectorVisibilityToggle = QPushButton("O")
        self.inspectorVisibilityToggle.setFixedWidth(40)
        self.itemValueWidget = ParameterValueWidget()
        self.itemNameLabel = QLabel()


# Convenience structure that stores the widgets for a single program function.
class FunctionWidgetSet:
    def __init__(self):
        self.startButton = QPushButton()
        self.stopButton = QPushButton("Stop")
        self.resumeButton = QPushButton("Resume")
        self.pauseButton = QPushButton("Pause")


# Control widget for a UI-editable parameter.
class ParameterValueWidget(QWidget):
    OnValueChanged = Signal()

    def __init__(self, parameterType=None):
        super().__init__()
        self.parameterType = parameterType
        if parameterType is None:
            return
        controlWidget = None
        if self.parameterType in (int, float):
            controlWidget = QSpinBox() if self.parameterType == int else QDoubleSpinBox()
            controlWidget.setMinimum(-1000000)
            controlWidget.setMaximum(1000000)
            controlWidget.valueChanged.connect(self.OnChanged)
        elif self.parameterType == str:
            controlWidget = QLineEdit()
            controlWidget.textChanged.connect(self.OnChanged)
        elif self.parameterType in [bool, ucscript.ProgramFunction,
                                    ucscript.Valve] or IsTypeValidOptions(parameterType):
            controlWidget = QComboBox()
            if self.parameterType == bool:
                controlWidget.addItems(["Yes", "No"])
            if IsTypeValidOptions(self.parameterType):
                controlWidget.addItems(list(self.parameterType.options))
            controlWidget.currentIndexChanged.connect(self.OnChanged)
        elif IsTypeValidList(self.parameterType):
            controlWidget = QWidget()
            controlLayout = QVBoxLayout()
            controlLayout.setContentsMargins(0, 0, 0, 0)
            controlWidget.setLayout(controlLayout)

            self.listItemsLayout = QVBoxLayout()
            controlLayout.addLayout(self.listItemsLayout)

            countLayout = QHBoxLayout()
            countLayout.setSpacing(0)
            countLayout.addWidget(QLabel("Count"))
            self.listCountWidget = QSpinBox()
            self.listCountWidget.setMinimum(0)
            self.listCountWidget.setMaximum(1000)
            self.listCountWidget.valueChanged.connect(self.OnChanged)
            countLayout.addWidget(self.listCountWidget, stretch=1)
            controlLayout.addLayout(countLayout)

            self.listContents: typing.List[ParameterValueWidget] = []
        self._updating = False
        pLayout = QVBoxLayout()
        self.setLayout(pLayout)
        self.controlWidget: typing.Union[
            QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QWidget, None] = controlWidget
        self.layout().addWidget(self.controlWidget)

    def OnChanged(self):
        if self._updating:
            return
        else:
            self.OnValueChanged.emit()

    def GetValue(self):
        if self.parameterType == bool:
            return self.controlWidget.currentText() == "Yes"
        elif self.parameterType == ucscript.Program:
            if 0 <= self.controlWidget.currentIndex() < len(
                    UIMaster.Instance().currentChip.programs):
                return UIMaster.Instance().currentChip.programs[self.controlWidget.currentIndex()]
        elif self.parameterType == ucscript.Valve:
            if 0 <= self.controlWidget.currentIndex() < len(UIMaster.Instance().currentChip.valves):
                return UIMaster.Instance().currentChip.valves[self.controlWidget.currentIndex()]
        elif IsTypeValidOptions(self.parameterType):
            return self.controlWidget.currentText()
        elif self.parameterType in (int, float):
            return self.controlWidget.value()
        elif self.parameterType == str:
            return self.controlWidget.text()
        elif IsTypeValidList(self.parameterType):
            listCount = self.listCountWidget.value()
            extras = listCount - len(self.listContents)
            extras = [NoneValueForType(self.parameterType.listType) for _ in range(extras)]
            return [x.GetValue() for x in self.listContents][:listCount] + extras

    def SetValue(self, value):
        self._updating = True
        if self.parameterType == bool:
            self.controlWidget.setCurrentText("Yes" if value else "No")
        elif self.parameterType in (int, float):
            self.controlWidget.setValue(value)
        elif self.parameterType == str:
            self.controlWidget.setText(value)
        elif IsTypeValidOptions(self.parameterType):
            self.controlWidget.setCurrentText(value)
        elif self.parameterType == ucscript.Program:
            try:
                newI = UIMaster.Instance().currentChip.programs.index(value)
            except ValueError:
                newI = -1
            if len(UIMaster.Instance().currentChip.programs) != self.controlWidget.count():
                self.controlWidget.clear()
                self.controlWidget.addItems(["x" for _ in UIMaster.Instance().currentChip.programs])
            [self.controlWidget.setItemText(i, x.name) for i, x in
             enumerate(UIMaster.Instance().currentChip.programs)]
            self.controlWidget.setCurrentIndex(newI)
        elif self.parameterType == ucscript.Valve:
            try:
                newI = UIMaster.Instance().currentChip.valves.index(value)
            except ValueError:
                newI = -1
            if len(UIMaster.Instance().currentChip.valves) != self.controlWidget.count():
                self.controlWidget.clear()
                self.controlWidget.addItems(["x" for _ in UIMaster.Instance().currentChip.valves])
            [self.controlWidget.setItemText(i, x.name) for i, x in
             enumerate(UIMaster.Instance().currentChip.valves)]
            self.controlWidget.setCurrentIndex(newI)
        elif IsTypeValidList(self.parameterType):
            if self.listCountWidget.value() != len(value):
                self.listCountWidget.setValue(len(value))
            if len(value) != len(self.listContents):
                [x.deleteLater() for x in self.listContents]
                self.listContents = [ParameterValueWidget(self.parameterType.listType) for _ in
                                     range(len(value))]
                [x.OnValueChanged.connect(self.OnChanged) for x in self.listContents]
                [self.listItemsLayout.addWidget(x) for x in self.listContents]
                [x.show() for x in self.listContents]
                self.topLevelWidget().adjustSize()
            [x.SetValue(v) for x, v in zip(self.listContents, value)]
        self._updating = False


class MessageArea(QScrollArea):
    def __init__(self):
        super().__init__()

        scrollContents = QWidget()
        self.setWidget(scrollContents)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollLayout = QVBoxLayout()
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(0)
        self.setMinimumWidth(200)
        scrollContents.setLayout(self.scrollLayout)

        self.lastMessages = []
        self.labels = []

    def Update(self, messages):
        if messages == self.lastMessages:
            return

        [label.deleteLater() for label in self.labels]
        self.labels = []
        self.lastMessages = messages.copy()

        for i, message in enumerate(self.lastMessages):
            newEntry = QLabel(message)
            newEntry.setStyleSheet("""
            padding: 5px;
            background-color: """ + ("#FFFFFF" if i % 2 == 0 else "#CCCCCC"))
            newEntry.setWordWrap(True)
            newEntry.setFixedSize(newEntry.sizeHint())
            self.labels.append(newEntry)
            self.scrollLayout.addWidget(newEntry)
        self.updateGeometry()
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().maximum())
