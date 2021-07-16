from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from typing import List
from UI.ChipEditor.ChipItem import ChipItem


class Inspector(QFrame):
    def __init__(self, parent):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._itemsLayout = QVBoxLayout()
        self._itemsLayout.setContentsMargins(0, 0, 0, 0)
        self._itemsLayout.setSpacing(0)

        self.setLayout(layout)

        self._titleWidget = TitleWidget("Inspector")
        layout.addWidget(self._titleWidget)
        layout.addLayout(self._itemsLayout)
        self.SetSelection([])

    def SetSelection(self, selection: List[ChipItem]):
        self.setVisible(len(selection) > 0)

        while self._itemsLayout.count():
            self._itemsLayout.takeAt(0).widget().setVisible(False)

        for selected in selection:
            self._itemsLayout.addWidget(selected.HoverWidget())
            selected.HoverWidget().setVisible(True)


class TitleWidget(QLabel):
    pass
