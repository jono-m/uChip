from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout
from UI.ChipEditor.ChipItem import ChipItem


class ChipInspector(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.setLayout(layout)

        self._currentEntity: Optional[ChipItem] = None

    def InspectEntity(self, item: ChipItem):
        if self._currentEntity:
            self._currentEntity.
