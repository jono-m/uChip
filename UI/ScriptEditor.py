import pathlib
import typing

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QTextFormat
from PySide6.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
                               QDialog, QPushButton, QSizePolicy, QScrollArea)

from UI.PythonEditor import PythonEditor
from Data.Chip import Script
from UI.UIMaster import UIMaster


class ScriptEditor(QDialog):
    def __init__(self, parent, OnClose):
        super().__init__(parent)
        self.pythonEditor = PythonEditor()
        self.pythonEditor.setMinimumWidth(500)

        self.toggleButton = QPushButton()
        self.toggleButton.clicked.connect(self.ToggleDocumentation)
        self.setModal(False)
        self.toggleButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.toggleButton.setStyleSheet("""
        QPushButton {
        background-color: rgba(0, 0, 0, 0.1);
        padding: 5px;
        font-weight: bold;
        }
        QPushButton:hover {
        background-color: rgba(0, 0, 0, 0.2);
        }
        """)

        layout = QHBoxLayout()
        layout.addWidget(self.pythonEditor, stretch=1)
        layout.addWidget(self.toggleButton, stretch=0)
        self.documentationWidget = DocumentationWidget()
        layout.addWidget(self.documentationWidget, stretch=0)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)
        self.enabled = True

        self.currentScript: typing.Optional[Script] = None
        self.resize(1200, 768)

        self.pythonEditor.modificationChanged.connect(self.UpdateTitle)
        self.ToggleDocumentation()
        self.OnClose = OnClose

    def ToggleDocumentation(self):
        v = self.documentationWidget.isVisible()
        self.documentationWidget.setVisible(not v)
        self.toggleButton.setText(">" if not v else "<")

    def UpdateTitle(self):
        fileName = str(self.currentScript.path.absolute()) if self.currentScript is not None else "New script"
        self.setWindowTitle(fileName + ("*" if self.pythonEditor.document().isModified() else "") + " - uChip Editor")

    def keyPressEvent(self, event) -> None:
        if not self.enabled:
            return
        if QGuiApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_S:
                self.Save()
                return
        super().keyPressEvent(event)

    def New(self):
        self.currentScript = None
        self.pythonEditor.setPlainText("")

    def Open(self, script: Script):
        self.currentScript = script
        self.pythonEditor.setPlainText(self.currentScript.Read())

    def closeEvent(self, event) -> None:
        if self.pythonEditor.document().isModified():
            if not self.PromptClose():
                event.ignore()
                return
        super().closeEvent(event)
        self.OnClose()

    def PromptClose(self):
        value = QMessageBox.critical(self, "Confirm Action",
                                     "This script has been modified. Do you want to discard changes?",
                                     QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard |
                                     QMessageBox.StandardButton.Cancel)
        if value == QMessageBox.StandardButton.Cancel:
            return False
        elif value == QMessageBox.StandardButton.Save:
            return self.Save()
        return True

    def Save(self):
        if self.currentScript is None:
            d = QFileDialog.getSaveFileName(self, "Save Path", filter="uChip script (*.py)")
            if d[0]:
                path = pathlib.Path(d[0])
            else:
                return False
        else:
            path = self.currentScript.path
        outputFile = open(path, "w+")
        outputFile.write(self.pythonEditor.toPlainText())
        outputFile.close()
        if self.currentScript is None:
            self.currentScript = Script(path)
            UIMaster.Instance().currentChip.scripts.append(self.currentScript)
        self.pythonEditor.document().setModified(False)
        return True


class DocumentationWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.documentationLabel = QLabel()
        f = open("Documentation.txt")
        self.documentationLabel.setText(f.read())
        f.close()
        self.documentationLabel.setTextFormat(Qt.TextFormat.RichText)
        self.documentationLabel.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.documentationLabel.setWordWrap(True)
        self.documentationLabel.setContentsMargins(20, 20, 20, 20)

        self.scrollArea = QScrollArea()
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea.setWidget(self.documentationLabel)

        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.addWidget(self.scrollArea)
        self.setLayout(mainLayout)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        f = open("Documentation.txt")
        self.documentationLabel.setText(f.read())