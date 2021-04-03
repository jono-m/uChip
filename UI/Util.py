from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
import typing
from inspect import signature


class CleanSpinBox(QDoubleSpinBox):
    def textFromValue(self, val: float) -> str:
        if val.is_integer():
            return str(int(val))
        return repr(val)


class ColorIcon(QIcon):
    def __init__(self, filename, color: QColor):
        normalPixmap = QPixmap(filename)
        disabledPixmap = None

        if color is not None:
            tmp: QImage = normalPixmap.toImage()
            tmp2: QImage = normalPixmap.toImage()
            for x in range(tmp.height()):
                for y in range(tmp.width()):
                    normalColor = QColor(color)
                    normalColor.setAlpha(tmp.pixelColor(QPoint(x, y)).alpha())
                    tmp.setPixelColor(x, y, normalColor)
                    disabledColor = QColor(color)
                    disabledColor.setAlpha(tmp.pixelColor(QPoint(x, y)).alpha() / 2)
                    tmp2.setPixelColor(x, y, disabledColor)
            normalPixmap = QPixmap.fromImage(tmp)
            disabledPixmap = QPixmap.fromImage(tmp2)

        super().__init__(normalPixmap)

        if color is not None:
            self.addPixmap(disabledPixmap, QIcon.Disabled)
