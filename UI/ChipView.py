import pathlib
import typing

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFormLayout, \
    QLineEdit, QSpinBox, QFileDialog, QColorDialog, QPlainTextEdit, QDoubleSpinBox, QComboBox
from PySide6.QtGui import QIcon, QImage, QPixmap, QColor
from PySide6.QtCore import QPoint, Qt, QSize, QTimer, QRectF, Signal, QObject

import types
from UI.CustomGraphicsView import CustomGraphicsView, CustomGraphicsViewItem
from UI.UIMaster import UIMaster
from UI import Utilities
from ucscript import Trigger
from Data.Chip import Valve, Image, Text, Program
from Data.ProgramCompilation import CompiledProgram, CompiledValve, CompiledProgramReference
import re


class ChipView(QWidget):
    def __init__(self):
        super().__init__()
        self.graphicsView = CustomGraphicsView()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.layout().addWidget(self.graphicsView)

        self.toolPanel = QWidget(self)
        self.finishEditsButton = QPushButton()
        self.finishEditsButton.setFocusPolicy(Qt.NoFocus)
        self.finishEditsButton.setToolTip("Finish editing")
        self.finishEditsButton.setIcon(
            ColoredIcon("Assets/Images/checkIcon.png", QColor(100, 100, 100)))
        self.finishEditsButton.setFixedSize(50, 50)
        self.finishEditsButton.setIconSize(QSize(30, 30))
        self.finishEditsButton.clicked.connect(lambda: self.SetEditing(False))

        self.editButton = QPushButton()
        self.editButton.setFocusPolicy(Qt.NoFocus)
        self.editButton.setIcon(
            ColoredIcon("Assets/Images/Edit.png", QColor(100, 100, 100)))
        self.editButton.setToolTip("Edit chip")
        self.editButton.setFixedSize(50, 50)
        self.editButton.setIconSize(QSize(30, 30))
        self.editButton.clicked.connect(lambda: self.SetEditing(True))

        self.addValveButton = QPushButton()
        self.addValveButton.setFocusPolicy(Qt.NoFocus)
        self.addValveButton.setToolTip("Add valve")
        self.addValveButton.setIcon(
            ColoredIcon("Assets/Images/plusIcon.png", QColor(100, 100, 100)))
        self.addValveButton.setFixedSize(30, 30)
        self.addValveButton.setIconSize(QSize(20, 20))
        self.addValveButton.clicked.connect(self.AddNewValve)

        self.addImageButton = QPushButton()
        self.addImageButton.setFocusPolicy(Qt.NoFocus)
        self.addImageButton.setToolTip("Add image")
        self.addImageButton.setIcon(
            ColoredIcon("Assets/Images/plusIcon.png", QColor(100, 100, 100)))
        self.addImageButton.setFixedSize(30, 30)
        self.addImageButton.setIconSize(QSize(20, 20))
        self.addImageButton.clicked.connect(self.AddNewImage)

        self.addProgramButton = QPushButton()
        self.addProgramButton.setFocusPolicy(Qt.NoFocus)
        self.addProgramButton.setToolTip("Add program")
        self.addProgramButton.setIcon(
            ColoredIcon("Assets/Images/plusIcon.png", QColor(100, 100, 100)))
        self.addProgramButton.setFixedSize(30, 30)
        self.addProgramButton.setIconSize(QSize(20, 20))
        self.addProgramButton.clicked.connect(self.AddNewProgram)

        self.addTextButton = QPushButton()
        self.addTextButton.setFocusPolicy(Qt.NoFocus)
        self.addTextButton.setToolTip("Add text")
        self.addTextButton.setIcon(
            ColoredIcon("Assets/Images/plusIcon.png", QColor(100, 100, 100)))
        self.addTextButton.setFixedSize(30, 30)
        self.addTextButton.setIconSize(QSize(20, 20))
        self.addTextButton.clicked.connect(self.AddNewText)

        toolPanelLayout = QVBoxLayout()
        toolPanelLayout.setContentsMargins(0, 0, 0, 0)
        toolPanelLayout.setSpacing(0)
        self.toolPanel.setLayout(toolPanelLayout)

        toolPanelLayout.addWidget(self.finishEditsButton, alignment=Qt.AlignHCenter)
        toolPanelLayout.addWidget(self.editButton)

        self.toolOptions = QWidget()
        toolOptionsLayout = QVBoxLayout()
        toolOptionsLayout.addWidget(self.addValveButton, alignment=Qt.AlignHCenter)
        toolOptionsLayout.addWidget(self.addImageButton, alignment=Qt.AlignHCenter)
        toolOptionsLayout.addWidget(self.addTextButton, alignment=Qt.AlignHCenter)
        toolOptionsLayout.addWidget(self.addProgramButton, alignment=Qt.AlignHCenter)
        self.toolOptions.setLayout(toolOptionsLayout)
        toolPanelLayout.addWidget(self.toolOptions)

        self.SetEditing(True)

    def resizeEvent(self, event):
        self.UpdateToolPanelPosition()
        super().resizeEvent(event)

    def UpdateToolPanelPosition(self):
        r = self.rect()

        padding = 20
        self.toolPanel.adjustSize()
        self.toolPanel.move(r.topLeft() + QPoint(padding, padding))

    def SetEditing(self, isEditing: bool):
        self.graphicsView.SetInteractive(isEditing)
        self.editButton.setVisible(not isEditing)
        self.finishEditsButton.setVisible(isEditing)
        self.toolOptions.setVisible(isEditing)

        for item in self.graphicsView.allItems:
            if isinstance(item, ValveItem):
                item.valveWidget.setEnabled(not isEditing)

        self.UpdateToolPanelPosition()

    def AddNewValve(self):
        highestValveNumber = max(
            [x.solenoidNumber for x in UIMaster.Instance().currentChip.valves] + [-1])
        newValve = Valve()
        newValve.name = "Valve " + str(highestValveNumber + 1)
        newValve.solenoidNumber = highestValveNumber + 1
        UIMaster.Instance().currentChip.valves.append(newValve)
        newValveItem = ValveItem(newValve)
        newValveItem.valveWidget.setEnabled(not self.graphicsView.isInteractive)
        self.graphicsView.AddItems([newValveItem])
        self.graphicsView.CenterItem(newValveItem)
        self.graphicsView.SelectItems([newValveItem])

    def AddNewImage(self):
        imageToAdd = QFileDialog.getOpenFileName(self, "Browse for image",
                                                 filter="Images (*.png *.bmp *.gif *.jpg *.jpeg)")
        if imageToAdd[0]:
            newImage = Image()
            newImage.path = pathlib.Path(imageToAdd[0])
            UIMaster.Instance().currentChip.images.append(newImage)
            newImageItem = ImageItem(newImage)
            newImageItem.SetRect(
                QRectF(newImageItem.GetRect().topLeft(),
                       QSize(newImageItem.imageData.size())))
            self.graphicsView.AddItems([newImageItem])
            self.graphicsView.CenterItem(newImageItem)
            self.graphicsView.SelectItems([newImageItem])

    def AddNewText(self):
        newText = Text()
        newText.text = "New text"
        UIMaster.Instance().currentChip.text.append(newText)
        newTextItem = TextItem(newText)
        self.graphicsView.AddItems([newTextItem])
        self.graphicsView.CenterItem(newTextItem)
        self.graphicsView.SelectItems([newTextItem])

    def AddNewProgram(self):
        programToAdd = QFileDialog.getOpenFileName(self, "Browse for program",
                                                   filter="uChip program (*.py)")
        if programToAdd[0]:
            newProgram = Program()
            newProgram.path = pathlib.Path(programToAdd[0])
            newProgram.name = newProgram.path.stem
            UIMaster.Instance().currentChip.programs.append(newProgram)
            newProgramItem = ProgramItem(newProgram)
            self.graphicsView.AddItems([newProgramItem])
            self.graphicsView.CenterItem(newProgramItem)
            self.graphicsView.SelectItems([newProgramItem])

    def CloseChip(self):
        self.graphicsView.Clear()

    def OpenChip(self):
        valveItems = [ValveItem(valve) for valve in UIMaster.Instance().currentChip.valves]
        [v.SetRect(QRectF(*valve.rect)) for v, valve in
         zip(valveItems, UIMaster.Instance().currentChip.valves)]
        [v.valveWidget.setEnabled(not self.graphicsView.isInteractive) for v in valveItems]
        self.graphicsView.AddItems(valveItems)

        imageItems = [ImageItem(image) for image in UIMaster.Instance().currentChip.images]
        [i.SetRect(QRectF(*image.rect)) for i, image in
         zip(imageItems, UIMaster.Instance().currentChip.images)]
        self.graphicsView.AddItems(imageItems)

        textItems = [TextItem(text) for text in UIMaster.Instance().currentChip.text]
        [i.SetRect(QRectF(*text.rect)) for i, text in
         zip(textItems, UIMaster.Instance().currentChip.text)]
        self.graphicsView.AddItems(textItems)

        programItems = [ProgramItem(program) for program in
                        UIMaster.Instance().currentChip.programs]
        [i.SetRect(QRectF(*program.rect)) for i, program in
         zip(programItems, UIMaster.Instance().currentChip.programs)]
        self.graphicsView.AddItems(programItems)


class ValveItem(CustomGraphicsViewItem):
    valveClosedStyle = """
    QPushButton {
    background-color: #f03535; 
    border: 1px solid black;
    }
    QPushButton::hover {
    background-color: #cc2d2d;
    }
    QPushButton::pressed {
    background-color: #b52828;
    }
    """

    valveOpenStyle = """
    QPushButton {
    background-color: #aeeb34; 
    border: 1px solid black;
    }
    QPushButton::hover {
    background-color: #99cf2d;
    }
    QPushButton::pressed {
    background-color: #86b528;
    }
    """

    def __init__(self, valve: Valve):
        super().__init__("Valve")
        self.valveWidget = QPushButton("Test")
        self.valveWidget.clicked.connect(self.Toggle)
        self.valveWidget.setMinimumSize(100, 100)
        self.valve = valve
        self.timer = QTimer(self.valveWidget)
        self.timer.timeout.connect(self.Update)
        self.timer.start(30)
        self._displayState = None

        self.nameField = QLineEdit()
        self.nameField.textEdited.connect(self.PushToValve)
        self.numberField = QSpinBox()
        self.numberField.valueChanged.connect(self.PushToValve)
        self.numberField.setMinimum(0)
        self.numberField.setMaximum(1000)
        self.SetWidget(self.valveWidget)
        inspectorWidget = QWidget()
        form = QFormLayout()
        form.addRow("Name", self.nameField)
        form.addRow("Solenoid", self.numberField)
        inspectorWidget.setLayout(form)
        self._updating = False
        self.SetInspector(inspectorWidget)

        self.Update()

    def SetRect(self, rect):
        super().SetRect(rect)
        self.PushToValve()

    def OnRemoved(self) -> bool:
        UIMaster.Instance().currentChip.valves.remove(self.valve)
        UIMaster.Instance().modified = True
        return True

    def Duplicate(self):
        highestValveNumber = max(
            [x.solenoidNumber for x in UIMaster.Instance().currentChip.valves] + [-1])
        newValve = Valve()
        reMatch = re.match(r"(.*?)(\d+)", self.valve.name)
        if reMatch:
            nextNumber = int(reMatch.group(2)) + 1
            newValve.name = reMatch.group(1) + str(nextNumber)
            newValve.solenoidNumber = self.valve.solenoidNumber + 1
        else:
            newValve.name = self.valve.name
            newValve.solenoidNumber = highestValveNumber + 1
        UIMaster.Instance().currentChip.valves.append(newValve)
        UIMaster.Instance().modified = True
        return ValveItem(newValve)

    def Toggle(self):
        r = UIMaster.Instance().rig
        r.SetSolenoidState(self.valve.solenoidNumber,
                           not r.GetSolenoidState(self.valve.solenoidNumber))

    def PushToValve(self):
        if self._updating:
            return
        self.valve.name = self.nameField.text()
        self.valve.solenoidNumber = self.numberField.value()
        self.valve.rect = [self.GetRect().x(), self.GetRect().y(),
                           self.GetRect().width(), self.GetRect().height()]
        UIMaster.Instance().modified = True

    def Update(self):
        self._updating = True
        if self.numberField.value() != self.valve.solenoidNumber:
            self.numberField.setValue(self.valve.solenoidNumber)
        if self.nameField.text() != self.valve.name:
            self.nameField.setText(self.valve.name)

        text = self.valve.name + "\n(" + str(self.valve.solenoidNumber) + ")"
        if self.valveWidget.text() != text:
            self.valveWidget.setText(text)

        r = self.valveWidget.rect().size()
        r.setHeight(r.height() / 2)
        font = Utilities.ComputeAutofit(self.valveWidget.font(), r, self.valveWidget.text())
        if self.valveWidget.font().pixelSize() != font.pixelSize():
            self.valveWidget.setFont(font)
        currentState = UIMaster.Instance().rig.GetSolenoidState(self.valve.solenoidNumber)
        if currentState != self._displayState:
            self._displayState = currentState
            self.valveWidget.setStyleSheet(
                self.valveOpenStyle if currentState else self.valveClosedStyle)
        self._updating = False


class ImageItem(CustomGraphicsViewItem):
    def __init__(self, image: Image):
        super().__init__("Image")
        self.image = image
        self.lastModifiedTime = None
        self.lastPath = None
        self.imageData: typing.Optional[QImage] = None
        self.imageWidget = QLabel()
        # TODO: Image browse field
        self.timer = QTimer(self.imageWidget)
        self.timer.timeout.connect(self.Update)
        self.timer.start(30)
        self.SetWidget(self.imageWidget)
        self.Update()

    def Update(self):
        if self.image.path != self.lastPath or self.image.path.stat().st_mtime != self.lastModifiedTime:
            # TODO: Throw an error if image is not found now.
            self.imageData = QImage(str(self.image.path))
            self.lastPath = self.image.path
            self.lastModifiedTime = self.image.path.stat().st_mtime
            self.RefreshImage()

    def RefreshImage(self):
        pixmap = QPixmap(self.imageData).scaled(self.GetRect().size().toSize())
        self.imageWidget.setPixmap(pixmap)

    def Duplicate(self):
        newImage = Image()
        newImage.path = self.image.path
        UIMaster.Instance().currentChip.images.append(newImage)
        UIMaster.Instance().modified = True
        return ImageItem(newImage)

    def SetRect(self, rect: QRectF):
        self.imageWidget.setFixedSize(rect.size().toSize())
        super().SetRect(rect)
        self.RefreshImage()
        self.image.rect = [rect.x(), rect.y(), rect.width(), rect.height()]
        UIMaster.Instance().modified = True

    def OnRemoved(self):
        UIMaster.Instance().currentChip.images.remove(self.image)
        UIMaster.Instance().modified = True


class TextItem(CustomGraphicsViewItem):
    def __init__(self, text: Text):
        super().__init__("Text")
        self.text = text
        self.textWidget = QLabel()
        self.textWidget.setWordWrap(True)
        self.textField = QPlainTextEdit()
        self.textField.textChanged.connect(self.PushToText)
        self.fontColorButton = QPushButton()
        self.fontColorButton.clicked.connect(self.PickColor)
        self.fontSizeField = QSpinBox()
        self.fontSizeField.valueChanged.connect(self.PushToText)
        inspectorWidget = QWidget()
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.textField)
        formLayout = QFormLayout()
        mainLayout.addLayout(formLayout)
        inspectorWidget.setLayout(mainLayout)
        formLayout.addRow("Font Color", self.fontColorButton)
        formLayout.addRow("Font Size", self.fontSizeField)
        self.timer = QTimer(self.textWidget)
        self.timer.timeout.connect(self.Update)
        self.timer.start(30)
        self.SetWidget(self.textWidget)
        self.SetInspector(inspectorWidget)
        self._updating = False
        self.Update()
        self.SetRect(QRectF(0, 0, 200, 100))

    def PushToText(self):
        if self._updating:
            return
        self.text.text = self.textField.toPlainText()
        self.text.fontSize = self.fontSizeField.value()

    def PickColor(self):
        colorPicker = QColorDialog(QColor(*self.text.color),
                                   parent=UIMaster.Instance().topLevel)
        colorPicker.setModal(True)
        colorPicker.currentColorChanged.connect(self.SetColor)
        colorPicker.exec()

    def SetColor(self, c: QColor):
        self.text.color = (c.red(), c.green(), c.blue())
        UIMaster.Instance().modified = True

    def Update(self):
        self._updating = True
        c = QColor(*self.text.color)
        if self.fontColorButton.text() != c.name():
            self.fontColorButton.setStyleSheet("background-color: " + c.name())
            self.fontColorButton.setText(c.name())
            self.textWidget.setStyleSheet("background-color: transparent; color: " + c.name())
        if self.textField.toPlainText() != self.text.text:
            self.textField.setPlainText(self.text.text)
        if self.textWidget.text() != self.text.text:
            self.textWidget.setText(self.text.text)
        if self.fontSizeField.value() != self.text.fontSize:
            self.fontSizeField.setValue(self.text.fontSize)
        if self.textWidget.font().pixelSize() != self.text.fontSize:
            f = self.textWidget.font()
            f.setPixelSize(self.text.fontSize)
            self.textWidget.setFont(f)

        self._updating = False

    def Duplicate(self):
        newText = Text()
        newText.text = self.text.text
        newText.fontSize = self.text.fontSize
        newText.color = self.text.color
        UIMaster.Instance().currentChip.text.append(newText)
        UIMaster.Instance().modified = True
        return TextItem(newText)

    def SetRect(self, rect: QRectF):
        super().SetRect(QRectF(rect))
        self.text.rect = [rect.x(), rect.y(), rect.width(), rect.height()]
        UIMaster.Instance().modified = True

    def OnRemoved(self):
        UIMaster.Instance().currentChip.text.remove(self.text)
        UIMaster.Instance().modified = True


class ProgramItem(CustomGraphicsViewItem):
    def __init__(self, program: Program):
        super().__init__("Program")
        self.program = program

        self.compiledProgram: typing.Optional[CompiledProgram] = None

        # Set up inspector widget
        self.nameField = QLineEdit()
        self.nameField.textChanged.connect(self.PushToProgram)
        self.parameterWidgets: typing.List[ParameterWidget] = []

        # TODO: browse source field

        inspectorWidget = QWidget()
        self.SetInspector(inspectorWidget)
        self.inspectorLayout = QFormLayout()
        inspectorWidget.setLayout(self.inspectorLayout)
        self.inspectorLayout.addRow("Name", self.nameField)

        # Set up item widget
        self.itemWidget = QWidget()
        self.timer = QTimer(self.itemWidget)
        self.timer.timeout.connect(self.Update)
        self.timer.start(30)
        self.SetWidget(self.itemWidget)
        self._updating = False
        self.Update()

    def RebuildInspectorLayout(self):
        for i in reversed(range(1, self.inspectorLayout.rowCount())):
            self.inspectorLayout.removeRow(i)
        self.parameterWidgets = []
        for parameter in self.compiledProgram.compiledParameters:
            widget = ParameterWidget(parameter.GetName(), parameter.type)
            widget.OnValueChanged.connect(self.PushToProgram)
            if widget.parameterWidget is not None:
                self.inspectorLayout.addRow(parameter.GetName(), widget.parameterWidget)
            self.parameterWidgets.append(widget)

    def PushToProgram(self):
        if self._updating:
            return

    def Update(self):
        self._updating = True
        if UIMaster.ShouldRecompile(self.program):
            UIMaster.Recompile(self.program)
            self.compiledProgram = UIMaster.GetCompiledProgram(self.program)
            self.RebuildInspectorLayout()
        if self.program.name != self.nameField.text():
            self.nameField.setText(self.program.name)
        for parameterWidget, parameter in zip(self.parameterWidgets,
                                              self.compiledProgram.compiledParameters):
            value = self.program.parameterValues[parameter.GetName()]
            try:
                parameterWidget.UpdateValue(value)
            except ParameterLostException:
                self.program.parameterValues[parameter.GetName()] = None
            self._updating = False

    def Duplicate(self):
        newProgram = Program()
        newProgram.name = self.program.name
        newProgram.path = self.program.path
        newProgram.parameterValues = self.program.parameterValues.copy()
        UIMaster.Instance().currentChip.programs.append(newProgram)
        UIMaster.Instance().modified = True
        return ProgramItem(newProgram)

    def SetRect(self, rect: QRectF):
        super().SetRect(QRectF(rect))
        self.program.rect = [rect.x(), rect.y(), rect.width(), rect.height()]
        UIMaster.Instance().modified = True

    def OnRemoved(self):
        UIMaster.Instance().currentChip.programs.remove(self.program)
        [UIMaster.Instance().compiledPrograms.remove(x) for x in
         UIMaster.Instance().compiledPrograms if x.program == self.program]
        UIMaster.Instance().modified = True


class ParameterLostException(Exception):
    pass


class ParameterWidget(QObject):
    OnValueChanged = Signal()

    def __init__(self, name: str, t):
        super().__init__()
        self.name = name
        self.type = t
        self.dataForComboBox = []
        self.parameterWidget: typing.Union[
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, None] = None
        if self.type == int or self.type == float:
            self.parameterWidget = QSpinBox() if self.type == int else QDoubleSpinBox()
            self.parameterWidget.setMinimum(-100000)
            self.parameterWidget.setMaximum(100000)
            self.parameterWidget.valueChanged.connect(self.OnChanged)
        elif self.type == str:
            self.parameterWidget = QLineEdit()
            self.parameterWidget.textChanged.connect(self.OnChanged)
        elif self.type == bool or self.type == CompiledValve or \
                self.type == CompiledProgramReference or \
                (isinstance(self.type, list) and isinstance(self.type[0], str)):
            self.parameterWidget = QComboBox()
            self.parameterWidget.currentIndexChanged.connect(self.OnChanged)
        elif isinstance(self.type, list) and isinstance(self.type[0], type):
            self.parameterWidget = QWidget()
            self.parameterWidget.setLayout(QVBoxLayout())
            # TODO: Include add button
        elif isinstance(self.type, Trigger):
            self.parameterWidget = QPushButton(self.type.label)
            self.parameterWidget.clicked.connect(self.type.onTriggered)
        self._updating = False

    def OnChanged(self):
        if self._updating:
            return
        else:
            self.OnValueChanged.emit()

    def GetValue(self):
        if isinstance(self.parameterWidget, QComboBox):
            if self.type == bool:
                return self.parameterWidget.currentText() == "Yes"
            elif self.type == CompiledValve or self.type == CompiledProgramReference:
                return self.dataForComboBox[self.parameterWidget.currentIndex()]
            elif isinstance(self.type, list) and isinstance(self.type[0], str):
                return self.parameterWidget.currentText()
        elif isinstance(self.parameterWidget, QSpinBox) or \
                isinstance(self.parameterWidget, QDoubleSpinBox):
            return self.parameterWidget.value()
        elif isinstance(self.parameterWidget, QLineEdit):
            return self.parameterWidget.text()
        elif isinstance(self.parameterWidget, QWidget):
            return [x.GetValue() for x in self.parameterWidget.children() if
                    isinstance(x, ParameterWidget)]

    def UpdateValue(self, value):
        self._updating = True
        if isinstance(self.parameterWidget, QComboBox):
            if self.type == bool:
                newVal = "Yes" if value else "No"
                if newVal != self.parameterWidget.currentText():
                    self.parameterWidget.setCurrentText(newVal)
            elif self.type == CompiledValve:
                if UIMaster.Instance().currentChip.valves != self.dataForComboBox:
                    self.dataForComboBox = UIMaster.Instance().currentChip.valves.copy()
                if any([valve.name != self.parameterWidget.itemText(i) for i, valve in
                        enumerate(self.dataForComboBox)]):
                    self.parameterWidget.clear()
                    [self.parameterWidget.addItem(x.name) for x in self.dataForComboBox]
                try:
                    i = self.dataForComboBox.index(value)
                except ValueError:
                    raise ParameterLostException()
                if self.parameterWidget.currentIndex() != i:
                    self.parameterWidget.setCurrentIndex(i)
            elif self.type == CompiledProgramReference:
                if UIMaster.Instance().currentChip.programs != self.dataForComboBox:
                    self.dataForComboBox = UIMaster.Instance().currentChip.programs.copy()
                if any([program.name != self.parameterWidget.itemText(i) for i, program in
                        enumerate(self.dataForComboBox)]):
                    self.parameterWidget.clear()
                    [self.parameterWidget.addItem(x.name) for x in self.dataForComboBox]
                try:
                    i = self.dataForComboBox.index(value)
                except ValueError:
                    raise ParameterLostException()
                if self.parameterWidget.currentIndex() != i:
                    self.parameterWidget.setCurrentIndex(i)
            elif isinstance(self.type, list) and isinstance(self.type[0], str):
                if value != self.parameterWidget.currentText():
                    self.parameterWidget.setCurrentText(value)
        elif isinstance(self.parameterWidget, QSpinBox) or \
                isinstance(self.parameterWidget, QDoubleSpinBox):
            if value != self.parameterWidget.value():
                self.parameterWidget.setValue(value)
        elif isinstance(self.parameterWidget, QLineEdit):
            if value != self.parameterWidget.text():
                self.parameterWidget.setText(value)
        elif isinstance(self.parameterWidget, QWidget):
            if value != [x.GetValue() for x in self.parameterWidget.children() if
                         isinstance(x, ParameterWidget)]:
                # TODO: Now need to clear the children, add more...
                pass
        self._updating = False


class ColoredIcon(QIcon):
    def __init__(self, filename, color: QColor):
        pixmap = QPixmap(filename)
        replaced = QPixmap(pixmap.size())
        replaced.fill(color)
        replaced.setMask(pixmap.createMaskFromColor(Qt.transparent))
        super().__init__(replaced)
