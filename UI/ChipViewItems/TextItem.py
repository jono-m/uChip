from PySide6.QtWidgets import QLabel, QPlainTextEdit, QSpinBox, QWidget, QVBoxLayout, QFormLayout, \
    QPushButton, QColorDialog
from PySide6.QtGui import QColor
from PySide6.QtCore import QRectF
from UI.CustomGraphicsView import CustomGraphicsViewItem
from Data.Chip import Text
from UI.UIMaster import UIMaster


class TextItem(CustomGraphicsViewItem):
    def __init__(self, text: Text):
        self.text = text

        # The text widget is just a label
        self.textWidget = QLabel()
        self.textWidget.setWordWrap(True)

        # The inspector has a textedit field as well as boxes to chose color and size of the text.
        inspectorWidget = QWidget()
        inspectorWidget.setLayout(QVBoxLayout())

        self.textField = QPlainTextEdit()
        self.textField.textChanged.connect(self.RecordChanges)
        inspectorWidget.layout().addWidget(self.textField)

        formLayout = QFormLayout()
        inspectorWidget.layout().addLayout(formLayout)
        self.fontColorButton = QPushButton()
        self.fontColorButton.clicked.connect(self.PickColor)
        self.fontSizeField = QSpinBox()
        self.fontSizeField.valueChanged.connect(self.RecordChanges)
        formLayout.addRow("Font Color", self.fontColorButton)
        formLayout.addRow("Font Size", self.fontSizeField)

        self.buttonColor = QColor()

        super().__init__("Text", self.textWidget, inspectorWidget)

    def RecordChanges(self):
        if self.isUpdating:
            return
        self.text.text = self.textField.toPlainText()
        self.text.fontSize = self.fontSizeField.value()
        c = self.buttonColor
        self.text.color = (c.red(), c.green(), c.blue())
        UIMaster.Instance().modified = True

    def PickColor(self):
        colorPicker = QColorDialog(QColor(*self.text.color),
                                   parent=UIMaster.Instance().topLevel)
        colorPicker.setModal(True)
        colorPicker.colorSelected.connect(self.SetColor)
        colorPicker.exec()

    def SetColor(self, c: QColor):
        self.buttonColor = c
        self.RecordChanges()

    def Update(self):
        self.fontColorButton.setStyleSheet("background-color: " + self.buttonColor.name())
        self.fontColorButton.setText(self.buttonColor.name())
        self.textWidget.setStyleSheet(
            "background-color: transparent; color: " + self.buttonColor.name())
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
