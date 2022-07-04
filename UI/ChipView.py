from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QRectF
from UI.CustomGraphicsView import CustomGraphicsView, CustomGraphicsViewItem


class ChipView(QWidget):
    def __init__(self):
        super().__init__()
        self.graphicsView = CustomGraphicsView()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.layout().addWidget(self.graphicsView)

        demoWidget = QWidget()
        demoWidget.setLayout(QVBoxLayout())
        demoWidget.layout().addWidget(QLabel("Test!"))
        demoWidget.layout().addWidget(QPushButton("A button."))

        item = CustomGraphicsViewItem(demoWidget)

        self.graphicsView.AddItem(item)
        item.SetRect(QRectF(0, 0, 1000, 1000))

        self.graphicsView.UpdateItemVisuals()
