from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *

from UI.WorldBrowser.SelectableItem import *

import typing


class PortHoleWidget(QLabel):
    def __init__(self, graphicsParent: QGraphicsProxyWidget):
        super().__init__()
        self.setFixedSize(30, 30)

        self._IsFilled = False
        self.Color = QColor(245, 215, 66)
        self._IsHighlighted = False
        self.graphicsParent = graphicsParent
        self.setProperty("PreventMove", True)
        self.setAttribute(Qt.WA_Hover, True)

        self.connections: typing.List[ConnectionItem] = []

    def IsHighlighted(self):
        return self._IsHighlighted

    def IsFilled(self):
        return self._IsFilled

    def SetHighlighted(self, highlighted):
        self._IsHighlighted = highlighted
        self.update()

    def SetIsFilled(self, filled):
        self._IsFilled = filled
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        if self._IsFilled or self._IsHighlighted:
            painter.setBrush(QBrush(self.Color))
        else:
            painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(self.Color, 2))

        r = self.rect()

        painter.drawEllipse(r.center(), r.width() / 3, r.height() / 3)

        for c in self.connections:
            c.UpdatePath()

    def CanConnect(self, other: "PortHoleWidget"):
        return False

    def GetPositionInScene(self):
        return self.graphicsParent.mapToScene(
            self.mapTo(self.graphicsParent.widget(), self.rect().center()))


class ConnectionItem(QGraphicsPathItem, SelectableItem):
    def __init__(self, s: QGraphicsScene, fromPort: typing.Optional[PortHoleWidget],
                 toPort: typing.Optional[PortHoleWidget]):
        super().__init__()

        self._fromPort = None
        self._toPort = None

        self.SetFromPort(fromPort)
        self.SetToPort(toPort)

        self.setPos(QPointF(0, 0))
        self.setZValue(-10)

        self.IsHovered = False
        self.IsSelected = False

        self.overridePos = QPointF(0, 0)

        self.myPath = None

        s.addItem(self)

        self.UpdatePath()

    def SetFromPort(self, fromPort: typing.Optional[PortHoleWidget]):
        if self._fromPort is not None:
            self._fromPort.connections.remove(self)
        self._fromPort = fromPort
        if self._fromPort is not None:
            self._fromPort.connections.append(self)

    def SetToPort(self, toPort: typing.Optional[PortHoleWidget]):
        if self._toPort is not None:
            self._toPort.connections.remove(self)
        self._toPort = toPort
        if self._toPort is not None:
            self._toPort.connections.append(self)

    def GetFromPort(self):
        return self._fromPort

    def GetToPort(self):
        return self._toPort

    @staticmethod
    def GetPath(fromCenter: QPointF, toCenter: QPointF):
        offset = QPointF(80, 0)
        path = QPainterPath(fromCenter)
        path.lineTo(fromCenter + offset)
        path.lineTo(toCenter - offset)
        path.lineTo(toCenter)
        return path

    def UpdatePath(self):
        if self._fromPort is None:
            aCenter = self.overridePos
        else:
            if not self._toPort.isVisible():
                aCenter = self._fromPort.graphicsParent.mapToScene(self._fromPort.graphicsParent.rect().center())
            else:
                aCenter = self._fromPort.GetPositionInScene()

        if self._toPort is None:
            bCenter = self.overridePos
        else:
            if not self._toPort.isVisible():
                bCenter = self._toPort.graphicsParent.mapToScene(self._toPort.graphicsParent.rect().center())
            else:
                bCenter = self._toPort.GetPositionInScene()
        myPath = self.GetPath(aCenter, bCenter)
        self.myPath = myPath

        dummyPath = QPainterPath()
        dummyPath.addPath(myPath)
        dummyPath.addPath(myPath.toReversed())
        self.setPath(dummyPath)

    def paint(self, painter, option, widget, PySide2_QtWidgets_QWidget=None, NoneType=None, *args, **kwargs):
        if self._fromPort is None and self._toPort is None:
            return

        pen = QPen()
        if self.IsSelected:
            pen.setColor(QColor(52, 222, 235))
        else:
            if self._fromPort is not None:
                pen.setColor(self._fromPort.Color)
            elif self._toPort is not None:
                pen.setColor(self._toPort.Color)

        if self.IsHovered:
            pen.setWidth(8)
        else:
            pen.setWidth(5)

        myPath = self.myPath
        painter.setPen(pen)
        painter.drawPath(myPath)

        painter.setBrush(QBrush(pen.color()))
        painter.setPen(Qt.NoPen)
        arrowSize = 25
        for pathIndex in range(1, myPath.elementCount()):
            b = QPointF(myPath.elementAt(pathIndex).x, myPath.elementAt(pathIndex).y)
            a = QPointF(myPath.elementAt(pathIndex - 1).x, myPath.elementAt(pathIndex - 1).y)
            delta = b - a
            magnitude = ((delta.x() ** 2 + delta.y() ** 2) ** 0.5)
            unit = delta * (1 / magnitude)

            spacing = 80
            progress = spacing
            while progress < magnitude:
                midPoint = a + unit * progress
                base = midPoint - unit * (arrowSize / 2)
                tip = midPoint + unit * (arrowSize / 2)
                left = base + QPointF(unit.y(), -unit.x()) * (arrowSize / 2)
                right = base + QPointF(-unit.y(), unit.x()) * (arrowSize / 2)
                painter.drawPolygon(QPolygonF([tip, left, right]))
                progress += spacing

        dummyPen = QPen()
        dummyPen.setWidth(arrowSize)
        self.setBrush(Qt.red)
        self.setPen(dummyPen)

    def SetIsHovered(self, hoverOn):
        self.IsHovered = hoverOn
        self.update()

    def SetIsSelected(self, isSelected):
        self.IsSelected = isSelected
        self.update()
