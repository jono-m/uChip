from UI.WorldBrowser.SelectableItem import *
from UI.WorldBrowser.BlockItem import *


class PortHoleWidget(QFrame):
    def __init__(self, graphicsParent: BlockItem):
        super().__init__()

        self._IsConnected = False
        self.penColor = QColor(245, 215, 66, 255)
        self.connectedColor = QColor(245, 215, 66, 100)
        self.hoverColor = QColor(245, 215, 66, 255)
        self.highlightColor = QColor(245, 215, 66, 150)
        self._IsHighlighted = False
        self._IsHovered = False
        self.connectedThickness = 4
        self.unconnectedThickness = 2
        self.graphicsParent = graphicsParent

        self.connectionClass: typing.Type[ConnectionItem] = ConnectionItem

        self.connections: typing.List[ConnectionItem] = []

    def IsHovered(self):
        return self._IsHovered

    def IsHighlighted(self):
        return self._IsHighlighted

    def IsConnected(self):
        return self._IsConnected

    def SetIsHighlighted(self, highlighted):
        if self._IsHighlighted != highlighted:
            self._IsHighlighted = highlighted
            self.update()

    def SetIsHovered(self, hovered):
        if self._IsHovered != hovered:
            self._IsHovered = hovered
            self.update()

    def SetIsConnected(self, filled):
        if self._IsConnected != filled:
            self._IsConnected = filled
            self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        if self._IsHighlighted:
            color = self.highlightColor
        elif self._IsHovered:
            color = self.hoverColor
        elif self._IsConnected:
            color = self.connectedColor
        else:
            color = None

        if color is None:
            painter.setBrush(Qt.NoBrush)
        else:
            painter.setBrush(color)

        if self._IsConnected:
            painter.setPen(QPen(self.penColor, self.connectedThickness))
        else:
            painter.setPen(QPen(self.penColor, self.unconnectedThickness))

        r = self.contentsRect()

        painter.drawEllipse(r.center(), r.width() / 3, r.height() / 3)

        for c in self.connections:
            c.UpdatePath()

    def CanConnect(self, other: "PortHoleWidget") -> bool:
        return False

    def DoConnect(self, other: "PortHoleWidget"):
        return

    def GetPositionInScene(self) -> QPointF:
        if not self.isVisible():
            return self.graphicsParent.mapToScene(self.graphicsParent.rect().center())
        else:
            return self.graphicsParent.mapToScene(
                self.mapTo(self.graphicsParent.blockWidget, self.rect().center()))


class ConnectionItem(QGraphicsPathItem, SelectableItem):
    def __init__(self, s: QGraphicsScene, portHoleA: typing.Optional[PortHoleWidget],
                 portHoleB: typing.Optional[PortHoleWidget]):
        super().__init__()

        self.arrowSpacing = 80
        self.arrowSize = 25
        self.pulsePercentageSize = 0.4
        self.hoverWidth = 8
        self.lineWidth = 5

        self._portHoleA = None
        self._portHoleB = None

        self.SetPortHoleA(portHoleA)
        self.SetPortHoleB(portHoleB)

        self.setPos(QPointF(0, 0))
        self.setZValue(-10)

        self.IsHovered = False
        self.IsSelected = False

        self.overridePos = QPointF(0, 0)

        self.selectedColor = QColor(52, 222, 235)

        self.myPath = None

        s.addItem(self)

        self.UpdatePath()

    def SetPortHoleA(self, port: typing.Optional[PortHoleWidget]):
        if self._portHoleA is not None:
            self._portHoleA.connections.remove(self)
        self._portHoleA = port
        if self._portHoleA is not None:
            self._portHoleA.connections.append(self)

    def SetPortHoleB(self, port: typing.Optional[PortHoleWidget]):
        if self._portHoleB is not None:
            self._portHoleB.connections.remove(self)
        self._portHoleB = port
        if self._portHoleB is not None:
            self._portHoleB.connections.append(self)

    def GetPath(self):
        fromCenter = self.GetFromCenter()
        toCenter = self.GetToCenter()
        offset = QPointF(80, 0)
        path = QPainterPath(fromCenter)
        path.lineTo(fromCenter + offset)
        path.lineTo(toCenter - offset)
        path.lineTo(toCenter)
        return path

    def GetFromPortHole(self):
        return self._portHoleA

    def GetToPortHole(self):
        return self._portHoleB

    def GetConnectionClass(self) -> typing.Type["ConnectionItem"]:
        if self._portHoleA is not None:
            return self._portHoleA.connectionClass
        if self._portHoleB is not None:
            return self._portHoleB.connectionClass
        return ConnectionItem

    def GetFromCenter(self):
        if self.GetConnectionClass().GetFromPortHole(self) is None:
            fromCenter = self.overridePos
        else:
            fromCenter = self.GetConnectionClass().GetFromPortHole(self).GetPositionInScene()
        return fromCenter

    def GetToCenter(self):
        if self.GetConnectionClass().GetToPortHole(self) is None:
            toCenter = self.overridePos
        else:
            toCenter = self.GetConnectionClass().GetToPortHole(self).GetPositionInScene()
        return toCenter

    def UpdatePath(self):
        myPath = self.GetConnectionClass().GetPath(self)
        self.myPath = myPath

        dummyPath = QPainterPath()
        dummyPath.addPath(myPath)
        dummyPath.addPath(myPath.toReversed())
        self.setPath(dummyPath)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: typing.Optional[QWidget] = ...):
        if self._portHoleA is None and self._portHoleB is None:
            return

        pen = QPen()
        if self.IsSelected:
            pen.setColor(self.selectedColor)
        else:
            if self._portHoleA is not None:
                pen.setColor(self._portHoleA.penColor)
            elif self._portHoleB is not None:
                pen.setColor(self._portHoleB.penColor)

        if self.IsHovered:
            pen.setWidth(self.hoverWidth)
        else:
            pen.setWidth(self.lineWidth)

        myPath = self.myPath
        painter.setPen(pen)
        painter.drawPath(myPath)

        painter.setBrush(QBrush(pen.color()))
        painter.setPen(Qt.NoPen)
        for pathIndex in range(1, myPath.elementCount()):
            b = QPointF(myPath.elementAt(pathIndex).x, myPath.elementAt(pathIndex).y)
            a = QPointF(myPath.elementAt(pathIndex - 1).x, myPath.elementAt(pathIndex - 1).y)
            delta = b - a
            magnitude = ((delta.x() ** 2 + delta.y() ** 2) ** 0.5)
            unit = delta * (1 / magnitude)

            progress = self.arrowSpacing
            while progress < magnitude:
                midPoint = a + unit * progress
                base = midPoint - unit * (self.arrowSize / 2)
                tip = midPoint + unit * (self.arrowSize / 2)
                left = base + QPointF(unit.y(), -unit.x()) * (self.arrowSize / 2)
                right = base + QPointF(-unit.y(), unit.x()) * (self.arrowSize / 2)
                painter.drawPolygon(QPolygonF([tip, left, right]))
                progress += self.arrowSpacing

        dummyPen = QPen()
        dummyPen.setWidth(self.arrowSize)
        self.setBrush(Qt.red)
        self.setPen(dummyPen)

    def SetIsHovered(self, hoverOn):
        if self.IsHovered != hoverOn:
            self.IsHovered = hoverOn
            self.update()

    def SetIsSelected(self, isSelected):
        if self.IsSelected != isSelected:
            self.IsSelected = isSelected
            self.update()
