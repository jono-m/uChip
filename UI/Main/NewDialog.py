from PySide6.QtWidgets import QDialog, QPushButton, QLabel, QVBoxLayout, QButtonGroup, QLineEdit, QFileDialog, \
    QHBoxLayout, QRadioButton
from pathlib import Path
from enum import Enum, auto


class ProjectType(Enum):
    CHIP_PROJECT = auto()
    BLOCK_GRAPH = auto()
    BLOCK_SCRIPT = auto()

    def typeName(self):
        return {ProjectType.CHIP_PROJECT: "Chip Project",
                ProjectType.BLOCK_GRAPH: "Block Graph Project",
                ProjectType.BLOCK_SCRIPT: "Block Script Project"}[self]

    def description(self):
        return {ProjectType.CHIP_PROJECT: "A project to control a microfluidic chip with valves and procedures.",
                ProjectType.BLOCK_GRAPH: "A custom logic block based on a block graph.",
                ProjectType.BLOCK_SCRIPT: "A custom logic block based on a script."}[self]

    def fileExtension(self):
        return {ProjectType.CHIP_PROJECT: ".ucc",
                ProjectType.BLOCK_GRAPH: ".ucg",
                ProjectType.BLOCK_SCRIPT: ".ucs"}[self]

    def fileFilter(self):
        return self.typeName() + "(*." + self.fileExtension() + ")"

    @staticmethod
    def allFilter():
        return "uChip Files (" + " ".join(["*" + newType.fileExtension() for newType in ProjectType]) + ")"


class NewHandler:
    def OnNewRequest(self, newType: ProjectType, path: Path):
        print("Request new " + str(newType) + " at " + str(path.resolve()))


class NewDialog(QDialog):
    def __init__(self, parent, handler: NewHandler = NewHandler()):
        super().__init__(parent)

        self.setWindowTitle("New Project")

        self.setModal(True)

        self._handler = handler

        self._buttonGroup = QButtonGroup()
        for newType in ProjectType:
            self._buttonGroup.addButton(NewProjectOptionButton(newType))
        self._buttonGroup.buttons()[0].setChecked(True)

        self._buttonGroup.buttonClicked.connect(self.Clear)

        fileLabel = QLabel("Location for new project:")
        self._fileField = QLineEdit()
        self._fileField.setEnabled(False)

        browseButton = QPushButton("Browse...")
        browseButton.clicked.connect(self.BrowseForFile)

        self._errorField = QLabel("")

        self._okButton = QPushButton("Create")
        self._okButton.clicked.connect(self.OnOK)
        self._okButton.setEnabled(False)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.reject)

        layout = QVBoxLayout()
        typeButtonsLayout = QHBoxLayout()
        fileNameLayout = QHBoxLayout()
        okCancelLayout = QHBoxLayout()

        [typeButtonsLayout.addWidget(widget) for widget in self._buttonGroup.buttons()]
        [fileNameLayout.addWidget(widget) for widget in [fileLabel, self._fileField, browseButton]]
        [okCancelLayout.addWidget(widget) for widget in [cancelButton, self._okButton]]

        layout.addLayout(typeButtonsLayout)
        layout.addLayout(fileNameLayout)
        layout.addWidget(self._errorField)
        layout.addLayout(okCancelLayout)

        self.setLayout(layout)

    def Clear(self):
        print("Clear" + str(self._buttonGroup.checkedButton()) + str(self._buttonGroup.checkedId()))
        self._okButton.setEnabled(False)
        self._fileField.setText("")

    def OnOK(self):
        path = Path(self._fileField.text())
        if path.exists():
            self._errorField.setText("File already exists at location.")
            return
        if not path.parent.exists():
            self._errorField.setText("Path does not exist.")
            return

        self._handler.OnNewRequest(self._buttonGroup.checkedButton().newType, path)

        self.accept()

    def BrowseForFile(self):
        saveRoot, extension = QFileDialog.getSaveFileName(self,
                                                          "Location for new " + self._buttonGroup.checkedButton().newType.typeName(),
                                                          filter=self._buttonGroup.checkedButton().newType.fileFilter())
        saveFileName = saveRoot + extension
        if saveFileName:
            self._fileField.setText(saveFileName)
            self._okButton.setEnabled(True)


class NewProjectOptionButton(QPushButton):
    def __init__(self, newType: ProjectType):
        super().__init__("")

        self.setCheckable(True)
        self.newType = newType

        typeText = newType.typeName()
        descText = newType.description()

        self.setText(typeText + "\n" + descText)
