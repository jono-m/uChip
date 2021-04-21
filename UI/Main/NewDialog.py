from PySide6.QtWidgets import QDialog, QPushButton, QLabel, QVBoxLayout, QButtonGroup, QLineEdit, QFileDialog, \
    QHBoxLayout
from pathlib import Path
from ProjectSystem.ProjectTypes import ProjectType


class NewHandler:
    def OnNewRequest(self, path: Path):
        print("Request new " + str(ProjectType.TypeFromPath(path)) + " at " + str(path.resolve()))


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

        self._buttonGroup.buttonClicked.connect(self.TypeChange)

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

    def TypeChange(self):
        existingText = self._fileField.text()
        if existingText:
            corrected = Path(existingText).absolute().with_suffix(
                self._buttonGroup.checkedButton().newType.fileExtension())
            self._fileField.setText(str(corrected))

    def OnOK(self):
        path = Path(self._fileField.text())
        if path.exists():
            self._errorField.setText("File already exists at location.")
            return
        if not path.parent.exists():
            self._errorField.setText("Path does not exist.")
            return

        self._handler.OnNewRequest(path)

        self.accept()

    def BrowseForFile(self):
        saveFilename = NewDialog.BrowseForLocation(self)
        if saveFilename:
            self._fileField.setText(str(saveFilename.absolute()))
            self._okButton.setEnabled(True)
            self.TypeChange()

    @staticmethod
    def BrowseForLocation(parent):
        saveFilename, _ = QFileDialog.getSaveFileName(parent, "New File Location", filter=ProjectType.allFilter(),
                                                      options=QFileDialog.DontConfirmOverwrite)
        if saveFilename:
            return Path(saveFilename)
        else:
            return None


class NewProjectOptionButton(QPushButton):
    def __init__(self, newType: ProjectType):
        super().__init__("")

        self.setCheckable(True)
        self.newType = newType

        typeText = newType.typeName()
        descText = newType.description()

        self.setText(typeText + "\n" + descText)
