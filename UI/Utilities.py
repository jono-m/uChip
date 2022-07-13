from PySide6.QtGui import QFontMetrics, QFont
from PySide6.QtCore import QSize


def ComputeAutofit(font: QFont, goalSize: QSize, text: str):
    font.setPixelSize(16)
    metrics = QFontMetrics(font).boundingRect(text).size()
    scaleFactorX = float(goalSize.width()) / metrics.width()
    scaleFactorY = float(goalSize.height()) / metrics.height()
    scale = min(scaleFactorX, scaleFactorY)
    font.setPixelSize(round(16*scale))
    return font
