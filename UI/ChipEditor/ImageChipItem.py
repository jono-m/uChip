from typing import Optional

from PySide6.QtGui import QPixmap, QImage, Qt
from PySide6.QtCore import QPointF, QSize, Signal, QRectF
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from Model.Image import Image
from UI.AppGlobals import AppGlobals

import math
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

        self.GraphicsObject().setZValue(-10)

        self._neHandle = MovingHandle(self.containerWidget)
        self._neHandle.moved.connect(
            lambda currentPosition: self.HandleResize(self._neHandle, currentPosition))

        self._nwHandle = MovingHandle(self.containerWidget)
        self._nwHandle.moved.connect(
            lambda currentPosition: self.HandleResize(self._nwHandle, currentPosition))

        self._seHandle = MovingHandle(self.containerWidget)
        self._seHandle.moved.connect(
            lambda currentPosition: self.HandleResize(self._seHandle, currentPosition))

        self._swHandle = MovingHandle(self.containerWidget)
        self._swHandle.moved.connect(
            lambda currentPosition: self.HandleResize(self._swHandle, currentPosition))

        self._handles = [self._neHandle, self._seHandle, self._swHandle, self._nwHandle]

        self.Update()
        self.Move(QPointF())
        self.PositionHandles()

    def SetSelected(self, isSelected: bool):
        self.PositionHandles()
        for handle in self._handles:
            handle.setVisible(isSelected)

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

    def PositionHandles(self):
        self._neHandle.move(self.containerWidget.rect().topRight() - self._neHandle.rect().topRight())
        self._nwHandle.move(self.containerWidget.rect().topLeft() - self._neHandle.rect().topLeft())
        self._seHandle.move(self.containerWidget.rect().bottomRight() - self._neHandle.rect().bottomRight())
        self._swHandle.move(self.containerWidget.rect().bottomLeft() - self._neHandle.rect().bottomLeft())

    def Update(self):
        mTime = Path(self._image.path).stat().st_mtime

        if mTime > self._lastVersion or self._image.path != self._lastFilename:
            self._lastVersion = mTime
            self._lastSize = None
            self._lastFilename = self._image.path

            newImage = QImage(str(self._image.path.absolute()))
            if self._rawImage and newImage.size() != self._rawImage.size():
                self._image.size = newImage.size()
            self._rawImage = newImage
            self.containerWidget.adjustSize()
            self.PositionHandles()

        if self._image.size != self._lastSize:
            self.image.setPixmap(QPixmap(self._rawImage).scaled(self._image.size, Qt.AspectRatioMode.IgnoreAspectRatio))
            self.image.setFixedSize(self._image.size)
            self.containerWidget.adjustSize()
            self._lastSize = self._image.size
            self.PositionHandles()

    def HandleResize(self, handle: 'MovingHandle', currentPosition: QPointF):
        imageRect = QRectF(self._image.position, self._image.size)
        currentPosition = self.GraphicsObject().mapToScene(self.containerWidget.mapFromGlobal(currentPosition))
        aspect = self._rawImage.width() / self._rawImage.height()

        getHandlePosition = lambda rect: {self._neHandle: rect.topRight(),
                                          self._nwHandle: rect.topLeft(),
                                          self._seHandle: rect.bottomRight(),
                                          self._swHandle: rect.bottomLeft()}[handle]

        setHandlePosition = lambda rect, position: {self._neHandle: rect.setTopRight,
                                                    self._nwHandle: rect.setTopLeft,
                                                    self._seHandle: rect.setBottomRight,
                                                    self._swHandle: rect.setBottomLeft}[handle](position)

        signMod = {self._neHandle: -1,
                   self._nwHandle: 1,
                   self._seHandle: 1,
                   self._swHandle: -1}[handle]

        wpRect = QRectF(imageRect)
        hpRect = QRectF(imageRect)

        trueDelta = currentPosition - getHandlePosition(imageRect)

        wpDelta = QPointF(trueDelta.x(), signMod * trueDelta.x() / aspect)
        hpDelta = QPointF(trueDelta.y() * aspect * signMod, trueDelta.y())

        setHandlePosition(wpRect, getHandlePosition(wpRect) + wpDelta)
        setHandlePosition(hpRect, getHandlePosition(hpRect) + hpDelta)

        if DistanceToEdge(currentPosition, wpRect) < DistanceToEdge(currentPosition, hpRect):
            imageRect = wpRect
        else:
            imageRect = hpRect

        self._image.position = imageRect.topLeft()
        self._image.size = imageRect.size().toSize()
        self.Update()
        self.GraphicsObject().setPos(self._image.position)


class MovingHandle(QFrame):
    moved = Signal(QPointF)

    def __init__(self, parent):
        super().__init__(parent)

        self._pressed = False
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)

    def mousePressEvent(self, event) -> None:
        self._pressed = True
        print("Pressed")

    def mouseMoveEvent(self, event) -> None:
        if self._pressed:
            currentPosition = event.globalPosition()
            self.moved.emit(currentPosition)

    def mouseReleaseEvent(self, event) -> None:
        self._pressed = False
        print("Released")


def DistanceToEdge(point: QPointF, rect: QRectF):
    dx = max(rect.left() - point.x(), 0, point.x() - rect.right())
    dy = max(rect.top() - point.y(), 0, point.y() - rect.bottom())
    return math.sqrt(dx * dx + dy * dy)


def Sign(number):
    if number == 0:
        return 0
    return number / abs(number)
