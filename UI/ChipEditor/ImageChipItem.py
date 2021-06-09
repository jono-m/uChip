from typing import Optional

from PySide6.QtGui import QPixmap, QImage, Qt
from PySide6.QtCore import QPointF, QSize
from PySide6.QtWidgets import QLabel, QVBoxLayout

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from Model.Image import Image
from UI.AppGlobals import AppGlobals

from pathlib import Path


class ImageChipItem(WidgetChipItem):
    def __init__(self, image: Image):
        super().__init__()

        self._image = image

        self.image = QLabel()

        AppGlobals.Instance().onChipModified.connect(self.CheckForImage)

        layout = QVBoxLayout()
        layout.addWidget(self.image)
        self.containerWidget.setLayout(layout)

        self._lastFilename = None
        self._lastVersion = -1
        self._lastSize = None

        self._rawImage: Optional[QImage] = None

        self.Update()
        self.Move(QPointF())

    def CheckForImage(self):
        if self._image not in AppGlobals.Chip().images:
            self.RemoveItem()

    def Move(self, delta: QPointF):
        if delta != QPointF():
            AppGlobals.Instance().onChipDataModified.emit()
        self._image.position += delta
        self.GraphicsObject().setPos(self._image.position)

    def RequestDelete(self):
        AppGlobals.Chip().images.remove(self._image)
        AppGlobals.Instance().onChipModified.emit()

    def Duplicate(self) -> 'ChipItem':
        newImage = Image(self._image.path)
        newImage.position = QPointF(self._image.position)
        newImage.size = QSize(self._image.size)

        AppGlobals.Chip().images.append(newImage)
        AppGlobals.Instance().onChipModified.emit()
        return ImageChipItem(newImage)

    def Update(self):
        mTime = Path(self._image.path).stat().st_mtime

        if mTime > self._lastVersion or self._image.path != self._lastFilename:
            self._lastVersion = mTime
            self._lastSize = None
            self._lastFilename = self._image.path

            self._rawImage = QImage(str(self._image.path.absolute()))

        if self._image.size != self._lastSize:
            self.image.setPixmap(QPixmap(self._rawImage).scaled(self._image.size, Qt.AspectRatioMode.IgnoreAspectRatio))
            self.image.setFixedSize(self._image.size)
