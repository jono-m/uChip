from typing import List

from PySide6.QtWidgets import QTabWidget, QMessageBox, QMainWindow, QSplitter, QFileDialog
from UI.ProgramEditor.ProgramEditorTab import ProgramEditorTab, Program
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from UI.StylesheetLoader import StylesheetLoader
from UI.ProgramEditor.MenuBar import MenuBar
from UI.ProgramEditor.Instructions import Instructions
from UI.AppGlobals import AppGlobals


class ProgramEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        AppGlobals.Instance().onChipAddRemove.connect(self.UpdateDisplay)
        StylesheetLoader.RegisterWidget(self)
        self.setWindowIcon(QIcon("Assets/Images/icon.png"))
        self._tabWidget = QTabWidget()

        self.setCentralWidget(self._tabWidget)

        menuBar = MenuBar()
        self.setMenuBar(menuBar)

        menuBar.saveProgram.connect(self.SaveProgram)
        menuBar.exportProgram.connect(self.ExportProgram)
        menuBar.closeProgram.connect(lambda: self.RequestCloseTab(self._tabWidget.currentIndex()))
        menuBar.helpAction.connect(self.ShowInstructions)

        self._instructionsWindow = Instructions(self)
        self._instructionsWindow.setVisible(False)

        self._tabWidget.tabCloseRequested.connect(self.RequestCloseTab)
        self._tabWidget.currentChanged.connect(self.UpdateDisplay)
        self._tabWidget.setTabsClosable(True)

    def SaveProgram(self):
        self._tabWidget.currentWidget().SaveProgram()
        self.UpdateDisplay()

    def ExportProgram(self):
        filename, filterType = QFileDialog.getSaveFileName(self, "Export Program", filter="μChip Program File (*.ucp)")
        if filename:
            self._tabWidget.currentWidget().ExportProgram(filename)

    def ShowInstructions(self):
        self._instructionsWindow.show()

    def OpenProgram(self, program: Program):
        for tab in self.tabs():
            if tab.program is program:
                self._tabWidget.setCurrentWidget(tab)
                return
        newTab = ProgramEditorTab(program)
        newTab.onModified.connect(self.UpdateDisplay)
        self._tabWidget.addTab(newTab, program.name)
        self._tabWidget.setCurrentIndex(self._tabWidget.count() - 1)

    def RequestCloseTab(self, index):
        tab: ProgramEditorTab = self._tabWidget.widget(index)
        self._tabWidget.setCurrentWidget(tab)
        if tab.modified:
            ret = QMessageBox.warning(self, "Confirm",
                                      "'" + tab.program.name + "' has been modified.\nDo you want to save changes?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if ret is QMessageBox.Save:
                tab.SaveProgram()
            elif ret is QMessageBox.Cancel:
                return False
        self._tabWidget.removeTab(index)
        if not self._tabWidget.count():
            self.close()
        return True

    def closeEvent(self, event) -> None:
        if not self.RequestCloseAll():
            event.ignore()

    def RequestCloseAll(self):
        while self._tabWidget.count():
            if not self.RequestCloseTab(0):
                return False
        return True

    def tabs(self) -> List[ProgramEditorTab]:
        return [self._tabWidget.widget(i) for i in range(self._tabWidget.count())]

    def UpdateDisplay(self):
        modified = False
        for tab in self.tabs():
            title = tab.program.name
            if tab.modified:
                modified = True
                title += "*"
            self._tabWidget.setTabText(self._tabWidget.indexOf(tab), title)

        current: ProgramEditorTab = self._tabWidget.currentWidget()
        if current:
            title = current.program.name
            if modified:
                title += " *"
            title += " | μChip Program Editor"
            self.setWindowTitle(title)
        else:
            self.close()
from PySide6.QtWidgets import QFrame, QSplitter, QHBoxLayout, QLineEdit, QVBoxLayout, QLabel, QPlainTextEdit
from PySide6.QtCore import Signal, Qt
from Data.Program.Program import Program
from UI.AppGlobals import AppGlobals
from UI.ProgramEditor.CodeTextEditor import CodeTextEditor
from UI.ProgramEditor.ParameterEditor import ParameterEditor
from pathlib import Path


class ProgramEditorTab(QFrame):
    onModified = Signal()

    def __init__(self, program: Program):
        super().__init__()

        AppGlobals.Instance().onChipAddRemove.connect(self.CheckForProgram)

        self.program = program
        self.modified = False
        self.codeEditor = CodeTextEditor()

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(splitter)

        self._programNameField = QLineEdit(program.name)
        self._programNameField.textChanged.connect(self.UpdateProgramName)

        descriptionLabel = QLabel("Description")
        descriptionLabel.setObjectName("DescriptionLabel")
        descriptionLabel.setAlignment(Qt.AlignCenter)
        self._descriptionField = QPlainTextEdit(program.description)
        self._descriptionField.textChanged.connect(self.UpdateProgramName)

        self._parameterEditor = ParameterEditor(program)
        self._parameterEditor.onParametersChanged.connect(self.ProgramEdited)

        sideLayout = QVBoxLayout()
        sideLayout.setContentsMargins(0, 0, 0, 0)
        sideLayout.setSpacing(0)
        sideLayout.addWidget(self._programNameField)
        sideLayout.addWidget(self._parameterEditor, stretch=1)
        sideLayout.addWidget(descriptionLabel)
        sideLayout.addWidget(self._descriptionField, stretch=0)
        sideWidget = QFrame()
        sideWidget.setLayout(sideLayout)

        splitter.addWidget(sideWidget)
        splitter.addWidget(self.codeEditor)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.handle(1).setAttribute(Qt.WA_Hover, True)

        self.codeEditor.SetCode(self.program.script)

        self.codeEditor.codeChanged.connect(self.ProgramEdited)

    def UpdateProgramName(self):
        self.ProgramEdited()

    def SaveProgram(self):
        self.program.script = self.codeEditor.Code()
        self.program.name = self._programNameField.text()
        self.program.description = self._descriptionField.toPlainText()
        self._parameterEditor.Save()
        self.modified = False
        AppGlobals.Instance().onChipAddRemove.emit()

    def ExportProgram(self, path: Path):
        self.SaveProgram()
        self.program.Export(path)

    def ProgramEdited(self):
        self.modified = True
        self.onModified.emit()

    def CheckForProgram(self):
        if self.program not in AppGlobals.Chip().programs:
            self.deleteLater()
from typing import List

from Data.Program.Program import Program
from Data.Program.Parameter import Parameter
from Data.Program.Data import DataType

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton, QLineEdit, \
    QComboBox, QSpinBox, QDoubleSpinBox, QToolButton, QGridLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, Qt


class ParameterEditor(QFrame):
    onParametersChanged = Signal()

    def __init__(self, program: Program):
        super().__init__()
        self._program = program

        parametersLabel = QLabel("Parameters")
        parametersLabel.setAlignment(Qt.AlignCenter)
        newParameterButton = QPushButton("Add Parameter")
        newParameterButton.setProperty("Attention", True)
        newParameterButton.clicked.connect(self.AddParameter)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(parametersLabel)

        self._listArea = QScrollArea()
        self._listArea.setWidgetResizable(True)
        self._listArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._listArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self._listArea, stretch=1)
        layout.addWidget(newParameterButton)
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

        self.Populate()

    def AddParameter(self):
        newParameter = Parameter()
        self._temporaryParameters.append(newParameter)
        self.onParametersChanged.emit()
        self.AddToList(newParameter)

    def Populate(self):
        for parameter in self._temporaryParameters:
            self.AddToList(parameter)
        self._listArea.updateGeometry()

    def AddToList(self, parameter: Parameter):
        newItem = ParameterEditorItem(parameter)
        newItem.onRemoveParameter.connect(self.RemoveParameter)
        newItem.onMoveParameterUp.connect(self.MoveParameterUp)
        newItem.onMoveParameterDown.connect(self.MoveParameterDown)
        newItem.onChanged.connect(self.onParametersChanged.emit)
        self._itemLayout.addWidget(newItem)
        self.items.append(newItem)

    def RemoveFromList(self, parameter: Parameter):
        item = [item for item in self.items if item.parameter is parameter]
        item[0].deleteLater()
        self.items.remove(item[0])

    def RemoveParameter(self, parameter: Parameter):
        self._temporaryParameters.remove(parameter)
        self.onParametersChanged.emit()
        self.RemoveFromList(parameter)

    def Reorder(self, parameter: Parameter, newPosition: int):
        item = [item for item in self.items if item.parameter is parameter][0]
        self._itemLayout.removeWidget(item)
        self._itemLayout.insertWidget(newPosition, item)
        self.items.remove(item)
        self.items.insert(newPosition, item)
        self._temporaryParameters.remove(parameter)
        self._temporaryParameters.insert(newPosition, parameter)
        self.onParametersChanged.emit()

    def MoveParameterUp(self, parameter: Parameter):
        index = self._temporaryParameters.index(parameter)
        self.Reorder(parameter, index - 1)

    def MoveParameterDown(self, parameter: Parameter):
        index = self._temporaryParameters.index(parameter)
        self.Reorder(parameter, index + 1)

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
        deleteButton.setIcon(QIcon("Assets/Images/trashIcon.png"))
        deleteButton.clicked.connect(lambda: self.onRemoveParameter.emit(self.parameter))
        upButton = QToolButton()
        upButton.setText("\u2191")
        upButton.clicked.connect(lambda: self.onMoveParameterUp.emit(self.parameter))
        downButton = QToolButton()
        downButton.setText("\u2193")
        downButton.clicked.connect(lambda: self.onMoveParameterDown.emit(self.parameter))

        buttonsLayout = QVBoxLayout()
        buttonsLayout.setContentsMargins(0, 0, 0, 0)
        buttonsLayout.setSpacing(0)
        buttonsLayout.setAlignment(Qt.AlignTop)
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

        self._listDataTypeLabel = QLabel("List Type")
        self._listDataTypeField = QComboBox()
        for dataType in DataType:
            if dataType != DataType.LIST:
                self._listDataTypeField.addItem(dataType.ToString(), userData=dataType)
        self._listDataTypeField.currentIndexChanged.connect(self.OnChanged)

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
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.setSpacing(0)
        gridLayout.setAlignment(Qt.AlignTop)
        gridLayout.addWidget(self._nameLabel, 0, 0)
        gridLayout.addWidget(self._nameField, 0, 1)
        gridLayout.addWidget(self._dataTypeLabel, 1, 0)
        gridLayout.addWidget(self._dataTypeField, 1, 1)

        gridLayout.addWidget(self._listDataTypeLabel, 2, 0)
        gridLayout.addWidget(self._listDataTypeField, 2, 1)

        gridLayout.addWidget(self._defaultValueLabel, 2, 0)

        for defaultField in [self._defaultInteger, self._defaultFloat, self._defaultBoolean, self._defaultString]:
            gridLayout.addWidget(defaultField, 2, 1)

        gridLayout.addWidget(self._minimumLabel, 3, 0)
        gridLayout.addWidget(self._minimumInteger, 3, 1)
        gridLayout.addWidget(self._minimumFloat, 3, 1)
        gridLayout.addWidget(self._maximumLabel, 4, 0)
        gridLayout.addWidget(self._maximumInteger, 4, 1)
        gridLayout.addWidget(self._maximumFloat, 4, 1)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(buttonsLayout)
        layout.addLayout(gridLayout)
        self.setLayout(layout)

        self.SetFieldsFromParameter()

    def SetFieldsFromParameter(self):
        self._nameField.setText(self.parameter.name)

        self._dataTypeField.setCurrentText(self.parameter.dataType.ToString())
        self._listDataTypeField.setCurrentText(self.parameter.listType.ToString())

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

        self.UpdateVisibility()

    def UpdateVisibility(self):
        self._defaultInteger.setVisible(self._dataTypeField.currentData() is DataType.INTEGER)
        self._defaultFloat.setVisible(self._dataTypeField.currentData() is DataType.FLOAT)
        self._defaultBoolean.setVisible(self._dataTypeField.currentData() is DataType.BOOLEAN)
        self._defaultString.setVisible(self._dataTypeField.currentData() is DataType.STRING)

        self._minimumLabel.setVisible(self._dataTypeField.currentData() in [DataType.INTEGER, DataType.FLOAT])
        self._maximumLabel.setVisible(self._dataTypeField.currentData() in [DataType.INTEGER, DataType.FLOAT])
        self._minimumInteger.setVisible(self._dataTypeField.currentData() is DataType.INTEGER)
        self._maximumInteger.setVisible(self._dataTypeField.currentData() is DataType.INTEGER)
        self._minimumFloat.setVisible(self._dataTypeField.currentData() is DataType.FLOAT)
        self._maximumFloat.setVisible(self._dataTypeField.currentData() is DataType.FLOAT)
        self._minimumLabel.setVisible(self._dataTypeField.currentData() in [DataType.INTEGER, DataType.FLOAT])
        self._maximumLabel.setVisible(self._dataTypeField.currentData() in [DataType.INTEGER, DataType.FLOAT])

        self._defaultValueLabel.setVisible(
            self._dataTypeField.currentData() not in [DataType.VALVE, DataType.LIST, DataType.PROGRAM_PRESET])

        self._listDataTypeLabel.setVisible(self._dataTypeField.currentData() is DataType.LIST)
        self._listDataTypeField.setVisible(self._dataTypeField.currentData() is DataType.LIST)

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

        self.parameter.listType = self._listDataTypeField.currentData()

        self.parameter.defaultValueDict[DataType.INTEGER] = self._defaultInteger.value()
        self.parameter.defaultValueDict[DataType.FLOAT] = self._defaultFloat.value()
        self.parameter.defaultValueDict[DataType.BOOLEAN] = self._defaultBoolean.currentData()
        self.parameter.defaultValueDict[DataType.STRING] = self._defaultString.text()

        self.parameter.minimumInteger = self._minimumInteger.value()
        self.parameter.maximumInteger = self._maximumInteger.value()
        self.parameter.minimumFloat = self._minimumFloat.value()
        self.parameter.maximumFloat = self._maximumFloat.value()

        self.parameter.ValidateDefaultValues()

        self.SetFieldsFromParameter()
from PySide6.QtWidgets import QMenuBar
from PySide6.QtGui import QKeySequence
from PySide6.QtCore import Signal


class MenuBar(QMenuBar):
    saveProgram = Signal()
    closeProgram = Signal()
    exportProgram = Signal()
    helpAction = Signal()

    def __init__(self):
        super().__init__()

        self._fileMenu = self.addMenu("&File")
        saveAction = self._fileMenu.addAction("Save")
        saveAction.triggered.connect(self.saveProgram.emit)
        saveAction.setShortcut(QKeySequence("Ctrl+S"))
        self._fileMenu.addAction("Export").triggered.connect(self.exportProgram.emit)
        self._fileMenu.addAction("Close").triggered.connect(self.closeProgram.emit)

        self._helpMenu = self.addMenu("&Help")
        helpAction = self._helpMenu.addAction("Reference...")
        helpAction.triggered.connect(self.helpAction.emit)from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QScrollArea, QDialog, QPushButton
from PySide6.QtCore import Qt

instructions = """
<u><b>Built-ins</b></u>

    <i>Parameter(name: str)</i>
            Returns the current value of the parameter with the name <i>name</i>.
    <i>Valve(name: str)</i>
            Returns the <i>Valve</i> object for the valve name <i>name</i>.
    <i>Program(programName: str, parameters: Dict[str, Any])</i>
            Returns a new <i>Program instance</i> object to run the program named 
            <i>programName</i> with parameters <i>parameters</i>. <i>parameters</i> 
            is a dictionary mapping from the parameter name to its value. 
    <i>Preset(name: str)</i>
            Returns the <i>Program instance</i> for the program preset named <i>name</i>.
    <i>SetValve(valve: Valve object, state: [OPEN, CLOSED])</i>
            Sets the state of valve <i>valve</i> to <i>state</i>.
    <i>GetValve(valve: Valve object)</i>
            Returns the current state (OPEN or CLOSED) for valve <i>valve</i>.
    <i>Start(instance: Program instance)</i>
            Starts the program instance <i>instance</i>.
    <i>IsRunning(instance: Program instance object)</i>
            Checks if the program instance <i>instance</i> is running.
    <i>Stop(instance: Program instance object)</i>
            Stops execution of the program instance <i>instance</i>.
    <i>Pause(instance: Program instance object)</i>
            Pauses the program instance <i>instance</i>.
    <i>IsPaused(instance: Program instance object)</i>
            Checks if the program instance <i>instance</i> is paused.
    <i>Resume(instance: Program instance object)</i>
            Resumes the program instance <i>instance</i>.
    <i>print(text: str)</i>
            Prints <i>text</i> to the μChip console.
    <i>WaitForSeconds(seconds: float)</i>
            To be used in a <i>yield</i> statement. Will pause execution for 
            <i>seconds</i> seconds.
    <i>OPEN</i>
            Valve state macro for an open valve 
    <i>CLOSED</i>
            Valve state macro for a closed valve

<u><b>Program Control</b></u>

    Use <i>yield</i> to pause program execution. This can be used to wait for 
    a certain amount of time, until a different program is finished, or until 
    the next program tick (to allow other programs to run concurrently).
    
    <i>yield WaitForSeconds(seconds: float)</i> 
            Pause the program for <i>seconds</i> seconds.
    <i>yield [PROGRAM INSTANCE]</i> 
            Pause the program until the given program instance is finished.
    <i>yield</i> 
            Pause the program for one tick, to let other programs update.  
"""[1:].replace("\n", "<br>").replace(" ", "&nbsp;")


class Instructions(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        instructionsArea = QScrollArea()
        instructionsLabel = QLabel(instructions)
        instructionsArea.setWidget(instructionsLabel)
        instructionsArea.setWidgetResizable(True)
        instructionsArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        instructionsArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.layout().addWidget(instructionsArea)
from PySide6.QtWidgets import QFrame, QPlainTextEdit, QHBoxLayout, QTextEdit
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, Qt, QBrush, QKeyEvent, QColor, QPaintEvent, \
    QPainter, QTextFormat
from PySide6.QtCore import Signal, QRegularExpression, Qt, QRect, QSize
import keyword
import re


class CodeTextEditor(QFrame):
    codeChanged = Signal()

    def __init__(self):
        super().__init__()

        self.textEdit = CodeTextEditorWidget()
        self.textEdit.setTabStopDistance(20)
        self.textEdit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.textEdit.textChanged.connect(self.codeChanged.emit)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(self.textEdit)

        self._highlighter = PythonSyntaxHighlighter(self.textEdit.document())

    def SetCode(self, code: str):
        self.textEdit.setPlainText(code)

    def Code(self):
        return self.textEdit.toPlainText()


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        keywordFormat = QTextCharFormat()
        macroFormat = QTextCharFormat()
        commentFormat = QTextCharFormat()
        stringFormat = QTextCharFormat()
        numberFormat = QTextCharFormat()
        singleQuotedStringFormat = QTextCharFormat()

        self.highlightingRules = []

        # keyword
        brush = QBrush(QColor(255, 154, 59), Qt.SolidPattern)
        keywordFormat.setForeground(brush)
        keywordFormat.setFontWeight(QFont.Bold)
        keywords = keyword.kwlist

        for word in keywords:
            pattern = QRegularExpression("\\b" + word + "\\b")
            rule = HighlightingRule(pattern, keywordFormat)
            self.highlightingRules.append(rule)

        # macro
        brush = QBrush(QColor(187, 101, 207), Qt.SolidPattern)
        macroFormat.setForeground(brush)
        macroFormat.setFontWeight(QFont.Bold)
        macros = ['Parameter', "Valve", "Program", "Preset", "SetValve", "GetValve", "Start", "IsRunning", "Stop",
                  "Pause", "IsPaused", "Resume", "print", "WaitForSeconds", "OPEN", "CLOSED"]

        for word in macros:
            pattern = QRegularExpression("\\b" + word + "\\b")
            rule = HighlightingRule(pattern, macroFormat)
            self.highlightingRules.append(rule)

        # comment
        brush = QBrush(QColor(166, 166, 166), Qt.SolidPattern)
        pattern = QRegularExpression("#[^\n]*")
        commentFormat.setForeground(brush)
        rule = HighlightingRule(pattern, commentFormat)
        self.highlightingRules.append(rule)

        # string
        brush = QBrush(QColor(147, 201, 105), Qt.SolidPattern)
        pattern = QRegularExpression("\".*\"")
        pattern.setPatternOptions(QRegularExpression.InvertedGreedinessOption)
        stringFormat.setForeground(brush)
        rule = HighlightingRule(pattern, stringFormat)
        self.highlightingRules.append(rule)

        # singleQuotedString
        pattern = QRegularExpression("\'.*\'")
        pattern.setPatternOptions(QRegularExpression.InvertedGreedinessOption)
        singleQuotedStringFormat.setForeground(brush)
        rule = HighlightingRule(pattern, singleQuotedStringFormat)
        self.highlightingRules.append(rule)

        # number
        brush = QBrush(QColor(100, 184, 217), Qt.SolidPattern)
        pattern = QRegularExpression(r"\b\d+")
        numberFormat.setForeground(brush)
        rule = HighlightingRule(pattern, numberFormat)
        self.highlightingRules.append(rule)

    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = rule.pattern
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), rule.format)


class HighlightingRule:
    def __init__(self, pattern: QRegularExpression, patternFormat: QTextCharFormat):
        self.pattern = pattern
        self.format = patternFormat


class CodeTextEditorWidget(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        self._lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self._leftPadding = 5
        self._rightPadding = 20

        self.updateLineNumberAreaWidth()
        self.highlightCurrentLine()

    def lineNumberAreaPaintEvent(self, event: QPaintEvent):
        painter = QPainter(self._lineNumberArea)
        painter.fillRect(event.rect(), QColor(40, 40, 40))
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = blockNumber + 1
                if number == self.lineNumber():
                    painter.setPen(QColor(180, 180, 180))
                else:
                    painter.setPen(QColor(120, 120, 120))
                self.setFont(self.font())
                painter.drawText(0, top, self._lineNumberArea.width() - self._rightPadding, self.fontMetrics().height(), Qt.AlignRight, str(number))

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            blockNumber += 1

    def lineNumberAreaWidth(self) -> int:
        digits = 1
        maximum = max(1, self.blockCount())
        while maximum >= 10:
            maximum /= 10
            digits += 1

        space = self._leftPadding + self.fontMetrics().horizontalAdvance("9") * digits + self._rightPadding

        return space

    def resizeEvent(self, e):
        super().resizeEvent(e)

        rect = self.contentsRect()
        self._lineNumberArea.setGeometry(QRect(rect.left(), rect.top(), self.lineNumberAreaWidth(), rect.height()))

    def updateLineNumberAreaWidth(self):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(40, 40, 40)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def lineNumber(self):
        cursor = self.textCursor()
        text = self.toPlainText()
        end = cursor.position()
        preText = text[:end]
        lines = len(preText.split("\n"))
        return lines

    def updateLineNumberArea(self, rect: QRect, dy: int):
        if dy:
            self._lineNumberArea.scroll(0, dy)
        else:
            self._lineNumberArea.update(0, rect.y(), self._lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key.Key_Backtab:
            self.HandleTab(False)
        elif e.key() == Qt.Key.Key_Tab:
            self.HandleTab(True)
        else:
            super().keyPressEvent(e)

    def HandleTab(self, indent):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            if indent:
                currentPosition = cursor.position()
                cursor.movePosition(cursor.StartOfLine)
                cursor.setPosition(currentPosition, cursor.KeepAnchor)
                text = cursor.selectedText()
                cursor.setPosition(currentPosition)
                if text.strip() != '':
                    cursor.insertText("    ")
                    return

        beginning = min(cursor.anchor(), cursor.position())
        end = max(cursor.anchor(), cursor.position())

        cursor.setPosition(beginning)
        cursor.movePosition(cursor.StartOfLine)
        cursor.setPosition(end, cursor.KeepAnchor)
        cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)

        selectedText = cursor.selectedText()
        originalLines = selectedText.split("\u2029")
        lines = originalLines.copy()
        for lineNo in range(len(lines)):
            if indent:
                count = len(re.match(r"\A *", lines[lineNo])[0])
                toAdd = 4 - (count % 4)
                lines[lineNo] = " " * toAdd + lines[lineNo]
            else:
                lines[lineNo] = re.sub(r"\A {1,4}", "", lines[lineNo])
        newText = "\u2029".join(lines)

        cursor.removeSelectedText()
        cursor.insertText(newText)

        deltaFirstLine = len(lines[0]) - len(originalLines[0])
        cursor.setPosition(beginning + deltaFirstLine)

        deltaLastLine = sum([len(lines[i]) - len(originalLines[i]) for i in range(len(originalLines))])
        cursor.setPosition(end + deltaLastLine, cursor.KeepAnchor)

        self.setTextCursor(cursor)


class LineNumberArea(QFrame):
    def __init__(self, editor: CodeTextEditorWidget):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self._editor.lineNumberAreaPaintEvent(event)
