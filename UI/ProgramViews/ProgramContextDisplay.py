from Data.Program.ProgramInstance import ProgramInstance, Program

from PySide6.QtWidgets import QFrame, QVBoxLayout, QApplication, QPushButton
from PySide6.QtCore import Qt, QEvent, Signal
from UI.ProgramViews.ProgramInstanceWidget import ProgramInstanceWidget


class ProgramContextDisplay(QFrame):
    onDelete = Signal(Program)
    onEdit = Signal(Program)

    def __init__(self, parent, programInstance: ProgramInstance, listWidget, editable):
        super().__init__(parent)

        self._programInstance = programInstance

        self.listWidget = listWidget

        container = QFrame()
        self.setAutoFillBackground(True)
        clayout = QVBoxLayout()
        clayout.setContentsMargins(0, 0, 0, 0)
        clayout.setSpacing(0)
        self.setLayout(clayout)
        self.layout().addWidget(container)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        container.setLayout(layout)

        QApplication.instance().installEventFilter(self)

        self._instanceWidget = ProgramInstanceWidget(programInstance)
        self._instanceWidget.SetShowAllParameters(True)
        self._instanceWidget.ownsInstance = False
        layout.addWidget(self._instanceWidget)

        if editable:
            self._editButton = QPushButton("Edit")
            self._editButton.clicked.connect(lambda: self.onEdit.emit(self._programInstance.program))
            self._deleteButton = QPushButton("Delete")
            self._deleteButton.clicked.connect(lambda: self.onDelete.emit(self._programInstance.program))
            layout.addWidget(self._editButton)
            layout.addWidget(self._deleteButton)

        self.setFocusPolicy(Qt.ClickFocus)

        self.Reposition()

    def Reposition(self):
        self.adjustSize()
        self.show()
        self.raise_()
        topLeft = self.mapToGlobal(self.rect().topLeft())

        matches = [item for item in [self.listWidget.item(row) for row in range(self.listWidget.count())] if
                   item.program is self._programInstance.program]
        if matches:
            listWidgetItem = matches[0]
        else:
            return

        rect = listWidgetItem.listWidget().rectForIndex(
            listWidgetItem.listWidget().indexFromItem(listWidgetItem))
        topRightItem = listWidgetItem.listWidget().mapToGlobal(rect.topRight())
        delta = topRightItem - topLeft
        self.move(self.pos() + delta)

    def eventFilter(self, watched, event) -> bool:
        if self.isVisible() and event.type() == QEvent.MouseButtonPress:
            widget = QApplication.widgetAt(event.globalPos())
            while widget:
                if widget is self:
                    return False
                widget = widget.parent()
            self.deleteLater()
        return False

    def event(self, e) -> bool:
        if e.type() == QEvent.LayoutRequest:
            self.adjustSize()
        return super().event(e)