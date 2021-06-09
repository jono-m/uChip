import typing
from PySide6.QtGui import QImage
from PySide6.QtCore import QPointF, QSize
from pathlib import Path


class Image:
    def __init__(self, path: Path):
        self.position = QPointF()
        self.path = path

        self.size = QSize()

        self.InitializeSize()

    def InitializeSize(self):
        image = QImage(str(self.path.absolute()))
        self.size.setWidth(image.width())
        self.size.setHeight(image.height())
