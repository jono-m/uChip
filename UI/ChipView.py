from PySide6.QtWidgets import QWidget, QVBoxLayout
from UI.CustomGraphicsView import CustomGraphicsView


class ChipView(QWidget):
    def __init__(self):
        super().__init__()
        self.graphicsView = CustomGraphicsView()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.layout().addWidget(self.graphicsView)
