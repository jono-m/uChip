from ChipController.ChipController import *
from UI.StylesheetLoader import *


class ProceduresDialog(QDialog):
    def __init__(self, chipController: ChipController, *args, **kwargs):
        super().__init__(f=Qt.WindowTitleHint | Qt.WindowCloseButtonHint, *args, **kwargs)

        self.setWindowTitle("Procedures Manager")

        StylesheetLoader.GetInstance().RegisterWidget(self)

        self.chipController = chipController

        self.listBox = QListWidget()
        self.listBox.itemSelectionChanged.connect(self.OnSelectionChanged)

        self.okButton = QPushButton("OK")
        self.okButton.clicked.connect(self.OkClicked)
        self.renameButton = QToolButton()
        self.renameButton.setIcon(ColorIcon("Assets/pencilIcon.png", QColor(255, 255, 255)))
        self.renameButton.setToolTip("Rename Procedure")
        self.renameButton.clicked.connect(self.OnRenameClicked)
        self.deleteProcedureButton = QToolButton()
        self.deleteProcedureButton.setIcon(ColorIcon("Assets/minimizeIcon.png", QColor(255, 255, 255)))
        self.deleteProcedureButton.setToolTip("Delete Procedure")
        self.deleteProcedureButton.clicked.connect(self.OnDeleteClicked)

        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout2 = QHBoxLayout()
        layout2.setContentsMargins(0, 0, 0, 0)
        layout2.setSpacing(0)

        layout.addLayout(layout2)

        layout2.addWidget(self.listBox)
        layout3 = QVBoxLayout()
        layout3.setContentsMargins(0, 0, 0, 0)
        layout3.setSpacing(0)
        layout2.addLayout(layout3)
        layout3.addWidget(self.renameButton)
        layout3.addWidget(self.deleteProcedureButton)

        layout.addWidget(self.okButton)
        self.okButton.setFixedWidth(150)

        self.setLayout(layout)

        self.PopulateProceduresList()

        self.OnSelectionChanged()

    def OnSelectionChanged(self):
        hasSelection = self.listBox.currentItem() is not None
        self.renameButton.setEnabled(hasSelection)
        self.deleteProcedureButton.setEnabled(hasSelection)

    def PopulateProceduresList(self):
        c = self.GetSelectedProcedure()

        self.listBox.clear()
        for procedure in sorted(self.chipController.GetProcedures(), key=lambda x: x.GetName()):
            newItem = QListWidgetItem("  " + procedure.GetName())
            newItem.setData(typing.cast(int, Qt.ItemDataRole.UserRole), procedure)
            self.listBox.addItem(newItem)
            if c == procedure:
                self.listBox.setCurrentItem(newItem)

    def GetSelectedProcedure(self) -> typing.Optional[Procedure]:
        currentItem: QListWidgetItem = self.listBox.currentItem()

        if currentItem is not None:
            return currentItem.data(typing.cast(int, Qt.ItemDataRole.UserRole))
        else:
            return None

    def OnRenameClicked(self):
        (text, ok) = QInputDialog.getText(self, "Rename Procedure", "Procedure Name:")

        if ok and text:
            current = self.GetSelectedProcedure()
            current.SetName(text)
            self.PopulateProceduresList()

    def OkClicked(self):
        self.accept()

    def OnDeleteClicked(self):
        current = self.GetSelectedProcedure()
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Confirm Delete")
        msgBox.setText("Confirm Delete Procedure")
        msgBox.setInformativeText("Are you sure that you want to delete '" + current.GetName() + "'?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec()
        if ret != QMessageBox.Yes:
            return
        if current is not None:
            if len(self.chipController.GetProcedures()) == 1:
                self.chipController.AddProcedure(Procedure())
            current.Destroy()
            self.PopulateProceduresList()
