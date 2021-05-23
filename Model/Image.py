import typing
from PySide6.QtGui import QImage
from PySide6.QtCore import QPointF, QSize


class Image:
    def __init__(self):
        self.position = QPointF()
        self.filename: typing.Optional[str] = None
        self.size = QSize()

    def InitializeSize(self):
        image = QImage(self.filename)
        self.size.setWidth(image.width())
        self.size.setHeight(image.height())
