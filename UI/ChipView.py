from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFormLayout, \
    QLineEdit, QSpinBox, QFileDialog, QColorDialog, QPlainTextEdit
from PySide6.QtGui import QIcon, QImage, QPixmap, QColor
from PySide6.QtCore import QPoint, Qt, QSize, QTimer, QRectF
from UI.CustomGraphicsView import CustomGraphicsView, CustomGraphicsViewItem
from UI.UIMaster import UIMaster
from UI import Utilities
from Data.Chip import Valve, Image, Text
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
        self.UpdateToolPanelPosition()

    def AddNewValve(self):
        highestValveNumber = max(
            [x.solenoidNumber for x in UIMaster.Instance().currentChip.valves] + [-1])
        newValve = Valve()
        newValve.name = "Valve " + str(highestValveNumber + 1)
        newValve.solenoidNumber = highestValveNumber + 1
        UIMaster.Instance().currentChip.valves.append(newValve)
        newValveItem = ValveItem(newValve)
        self.graphicsView.AddItems([newValveItem])
        self.graphicsView.CenterItem(newValveItem)
        self.graphicsView.SelectItems([newValveItem])

    def AddNewImage(self):
        imageToAdd = QFileDialog.getOpenFileName(self, "Browse for image",
                                                 filter="Images (*.png *.bmp *.gif *.jpg *.jpeg)")
        if imageToAdd[0]:
            newImage = Image()
            newImage.original_image = QImage(imageToAdd[0])
            UIMaster.Instance().currentChip.images.append(newImage)
            newImageItem = ImageItem(newImage)
            newImageItem.imageWidget.setFixedSize(newImage.original_image.size() * 0.1)
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

    def CloseChip(self):
        self.graphicsView.Clear()

    def OpenChip(self):
        valveItems = [ValveItem(valve) for valve in UIMaster.Instance().currentChip.valves]
        [v.SetRect(QRectF(*valve.rect)) for v, valve in
         zip(valveItems, UIMaster.Instance().currentChip.valves)]
        self.graphicsView.AddItems(valveItems)

        imageItems = [ImageItem(image) for image in UIMaster.Instance().currentChip.images]
        [i.SetRect(QRectF(*image.rect)) for i, image in
         zip(imageItems, UIMaster.Instance().currentChip.images)]
        self.graphicsView.AddItems(imageItems)

        textItems = [TextItem(text) for text in UIMaster.Instance().currentChip.text]
        [i.SetRect(QRectF(*text.rect)) for i, text in
         zip(textItems, UIMaster.Instance().currentChip.text)]
        self.graphicsView.AddItems(imageItems)


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

        font = Utilities.ComputeAutofit(self.valveWidget)
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
        super().__init__()
        self.image = image
        self.imageWidget = QLabel()
        self.SetWidget(self.imageWidget)

    def Duplicate(self):
        newImage = Image()
        newImage.original_image = self.image.original_image.copy()
        UIMaster.Instance().currentChip.images.append(newImage)
        UIMaster.Instance().modified = True
        return ImageItem(newImage)

    def SetRect(self, rect: QRectF):
        rect = rect.toRect()
        pixmap = QPixmap(self.image.original_image).scaled(rect.size())
        self.imageWidget.setPixmap(pixmap)
        self.imageWidget.setFixedSize(rect.size())
        super().SetRect(QRectF(rect))
        self.image.rect = [rect.x(), rect.y(), rect.width(), rect.height()]
        UIMaster.Instance().modified = True

    def OnRemoved(self):
        UIMaster.Instance().currentChip.images.remove(self.image)
        UIMaster.Instance().modified = True


class TextItem(CustomGraphicsViewItem):
    def __init__(self, text: Text):
        super().__init__()
        self.text = text
        self.textWidget = QLabel()
        self.textField = QPlainTextEdit()
        self.textField.textChanged.connect(self.PushToText)
        self.textColorButton = QPushButton()
        self.textColorButton.clicked.connect(self.PickColor)
        inspectorWidget = QWidget()
        formLayout = QFormLayout()
        inspectorWidget.setLayout(formLayout)
        formLayout.addRow("Text", self.textField)
        formLayout.addRow("Font Color", self.textColorButton)
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
        if self.textColorButton.text() != c.name():
            self.textColorButton.setStyleSheet("background-color: " + c.name())
            self.textColorButton.setText(c.name())
            self.textWidget.setStyleSheet("background-color: transparent; color: " + c.name())
        if self.textField.toPlainText() != self.text.text:
            self.textField.setPlainText(self.text.text)
        if self.textWidget.text() != self.text.text:
            self.textWidget.setText(self.text.text)

        font = Utilities.ComputeAutofit(self.textWidget.font(),
                                        self.GetRect().size(),
                                        self.textWidget.text())
        if font.pixelSize() != self.textWidget.font().pixelSize():
            print(font.pixelSize())
            self.textWidget.setFont(font)
        self._updating = False

    def Duplicate(self):
        newText = Text()
        newText.text = self.text
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


class ColoredIcon(QIcon):
    def __init__(self, filename, color: QColor):
        pixmap = QPixmap(filename)
        replaced = QPixmap(pixmap.size())
        replaced.fill(color)
        replaced.setMask(pixmap.createMaskFromColor(Qt.transparent))
        super().__init__(replaced)
