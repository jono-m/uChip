from UI.WorldBrowser.SelectableItem import *


class PortHoleWidget(QLabel):
    def __init__(self, graphicsParent: QGraphicsProxyWidget):
        super().__init__()

        self._IsFilled = False
        self.Color = QColor(245, 215, 66)
        self._IsHighlighted = False
        self.graphicsParent = graphicsParent

        self.connectionClass: typing.Type[ConnectionItem] = ConnectionItem

        self.connections: typing.List[ConnectionItem] = []

    def IsHighlighted(self):
        return self._IsHighlighted

    def IsFilled(self):
        return self._IsFilled

    def SetHighlighted(self, highlighted):
        if self._IsHighlighted != highlighted:
            self._IsHighlighted = highlighted

    def SetIsFilled(self, filled):
        if self._IsFilled != filled:
            self._IsFilled = filled

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

    def CanConnect(self, other: "PortHoleWidget") -> bool:
        return False

    def DoConnect(self, other: "PortHoleWidget"):
        return

    def GetPositionInScene(self) -> QPointF:
        if not self.isVisible():
            return self.graphicsParent.mapToScene(self.graphicsParent.rect().center())
        else:
            return self.graphicsParent.mapToScene(
                self.mapTo(self.graphicsParent.widget(), self.rect().center()))


class ConnectionItem(QGraphicsPathItem, SelectableItem):
    def __init__(self, s: QGraphicsScene, portHoleA: typing.Optional[PortHoleWidget],
                 portHoleB: typing.Optional[PortHoleWidget]):
        super().__init__()

        self.arrowSpacing = 80
        self.arrowSize = 25
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
                pen.setColor(self._portHoleA.Color)
            elif self._portHoleB is not None:
                pen.setColor(self._portHoleB.Color)

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

    def SetIsSelected(self, isSelected):
        if self.IsSelected != isSelected:
            self.IsSelected = isSelected
