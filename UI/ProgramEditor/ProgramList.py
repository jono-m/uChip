from typing import Optional
from PySide6.QtWidgets import QWidget, QLabel, QListWidget, QPushButton, QMessageBox, QListWidgetItem, QVBoxLayout, \
    QApplication, QLineEdit
from PySide6.QtCore import Signal, Qt, QTimer, QEvent, QRect
from Model.Program.Program import Program
from UI.AppGlobals import AppGlobals


class ProgramList(QWidget):
    onProgramOpened = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self._programsLabel = QLabel("Programs")
        self._programsList = QListWidget()
        self._programsList.itemClicked.connect(self.SelectProgram)

        self._newButton = QPushButton("Create New Program")
        self._newButton.clicked.connect(self.NewProgram)

        layout = QVBoxLayout()
        layout.addWidget(self._programsLabel)
        layout.addWidget(self._programsList)
        layout.addWidget(self._newButton)

        self.setLayout(layout)

        AppGlobals.onChipOpened().connect(self.RefreshList)

        self._contextView = ProgramContextDisplay(self.topLevelWidget())
        self._contextView.onProgramDelete.connect(self.RefreshList)

    def SelectProgram(self, selectedProgram: 'ProgramListItem'):
        self._contextView.SetProgramItem(selectedProgram)

    def NewProgram(self):
        newProgram = Program()
        AppGlobals.Chip().programs.append(newProgram)
        self.RefreshList()
        programItem = self.ProgramItem(newProgram)
        self._programsList.setCurrentItem(programItem)
        self._contextView.SetProgramItem(programItem, True)

    def ProgramItem(self, program: Program):
        matches = [item for item in [self._programsList.item(row) for row in range(self._programsList.count())] if
                   item.program is program]
        if matches:
            return matches[0]

    def RefreshList(self):
        self._programsList.blockSignals(True)

        self._programsList.clear()
        for program in AppGlobals.Chip().programs:
            self._programsList.addItem(ProgramListItem(program))

        self._programsList.blockSignals(False)


class ProgramListItem(QListWidgetItem):
    def __init__(self, program: Program):
        super().__init__(program.name)
        self.program = program


class ProgramContextDisplay(QWidget):
    onProgramDelete = Signal()

    onProgramChanged = Signal()

    def __init__(self, parent):
        super().__init__(parent)

        container = QWidget()
        self.setAutoFillBackground(True)
        clayout = QVBoxLayout()
        clayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(clayout)
        self.layout().addWidget(container)

        self._nameField = QLineEdit()
        self._nameField.textChanged.connect(self.UpdateProgram)
        layout = QVBoxLayout()
        container.setLayout(layout)
        layout.addWidget(self._nameField)
        self.raise_()

        deleteButton = QPushButton("Delete")
        deleteButton.clicked.connect(self.DeleteProgram)

        QApplication.instance().installEventFilter(self)

        layout.addWidget(deleteButton)

        self._program = None
        self._programItem: Optional[ProgramListItem] = None

        self.setFocusPolicy(Qt.ClickFocus)
        self.Clear()

        timer = QTimer(self)
        timer.timeout.connect(self.Reposition)
        timer.start(30)

    def SetProgramItem(self, programItem: ProgramListItem, focusText=False):
        self._program = programItem.program
        self._programItem = programItem

        self._nameField.setText(self._program.name)

        self.setVisible(True)
        if focusText:
            self._nameField.setFocus()
            self._nameField.selectAll()
        else:
            self.setFocus()
        self.Reposition()

    def Clear(self):
        self._program = None
        self._programItem = None
        self.setVisible(False)

    def Reposition(self):
        if not self.isVisible():
            return
        self.resize(self.sizeHint())
        topLeft = self.mapToGlobal(self.rect().topLeft())

        rect = self._programItem.listWidget().rectForIndex(
            self._programItem.listWidget().indexFromItem(self._programItem))
        topRightItem = self._programItem.listWidget().mapToGlobal(rect.topRight())
        delta = topRightItem - topLeft
        self.move(self.pos() + delta)

    def eventFilter(self, watched, event) -> bool:
        if self.isVisible() and event.type() == QEvent.MouseButtonPress:
            widget = QApplication.widgetAt(event.globalPos())
            while widget:
                if widget is self:
                    return False
                widget = widget.parent()
            self.Clear()
        return False

    def DeleteProgram(self):
        if QMessageBox.question(self, "Confirm Deletion",
                                "Are you sure you want to delete " + self._program.name + "?") is QMessageBox.Yes:
            AppGlobals.Chip().programs.remove(self._program)
            self.onProgramDelete.emit()
            self.Clear()

    def UpdateProgram(self):
        self._program.name = self._nameField.text()
        self._programItem.setText(self._program.name)
        self.onProgramChanged.emit()