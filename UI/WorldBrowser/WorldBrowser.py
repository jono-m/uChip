from UI.WorldBrowser.PortHoles import *
from UI.WorldBrowser.BlockItem import *
import shiboken2


class WorldBrowser(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Set up scene
        scene = QGraphicsScene()
        self.setBackgroundBrush(QBrush(QColor(40, 40, 40)))
        self.setScene(scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.offset = QPointF(0, 0)
        self.setRenderHint(QPainter.Antialiasing)
        self.zoom = 0

        # Set up interface tracking elements
        self.selectedItem: typing.Optional[SelectableItem] = None
        self.hoverItem: typing.Optional[SelectableItem] = None

        self.isPanning = False
        self.isMoving = False
        self.lastPos = None

        self.isConnecting = False

        self.tempConnectionLine = ConnectionItem(self.scene(), None, None)
        self.tempConnectionLine.setVisible(False)
        self.anchorPort: typing.Optional[PortHoleWidget] = None
        self.hoverPort: typing.Optional[PortHoleWidget] = None

        self.IsFromPortFunc = lambda hole: True
        self.OnMakeConnectionFunc = lambda holeA, holeB: None
        self.CanMakeConnectionFunc = lambda holeA, holeB: True

        self.gridSpacing = QSize(30, 30)
        self.gridColor = QColor(50, 50, 50)

        self.boundToItems = False

        self.actionsEnabled = True

        self.UpdateView()

    def ClearOut(self):
        for item in self.items():
            if item == self.tempConnectionLine:
                continue
            else:
                self.scene().removeItem(item)
        self.hoverItem = None
        self.selectedItem = None

    def FrameItems(self):
        QApplication.processEvents()
        itemsRect = QRectF()
        for item in self.items():
            if isinstance(item, QGraphicsProxyWidget):
                item.widget().adjustSize()
                item.widget().repaint()
            itemsRect = itemsRect.united(item.boundingRect().translated(item.pos()))
        self.offset = itemsRect.center()

        self.UpdateView()

    def GetCenterPoint(self):
        return self.mapToScene(self.rect().center())

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)

        if not self.actionsEnabled:
            return

        painter.setPen(self.gridColor)

        if self.gridSpacing.width() > 0:
            xStart = rect.left() - rect.left() % self.gridSpacing.width()
            while xStart <= rect.right():
                painter.drawLine(int(xStart), int(rect.bottom()), int(xStart), int(rect.top()))
                xStart = xStart + self.gridSpacing.width()

        if self.gridSpacing.height() > 0:
            yStart = rect.top() - rect.top() % self.gridSpacing.height()
            while yStart <= rect.bottom():
                painter.drawLine(int(rect.left()), int(yStart), int(rect.right()), int(yStart))
                yStart = yStart + self.gridSpacing.height()

    def AddAndSelect(self, newItem: SelectableItem):
        self.scene().addItem(newItem)
        self.SelectItem(newItem)

    def SelectItem(self, item: typing.Optional[SelectableItem]):
        if not shiboken2.isValid(self.selectedItem):
            self.selectedItem = None
        if self.selectedItem == item:
            return
        if self.selectedItem is not None:
            self.selectedItem.SetIsSelected(False)
        self.selectedItem = item
        if self.selectedItem is not None:
            self.selectedItem.SetIsSelected(True)

    def HoverItem(self, item: typing.Optional[SelectableItem]):
        if not shiboken2.isValid(self.hoverItem):
            self.hoverItem = None
        if self.hoverItem == item:
            return
        if self.hoverItem is not None:
            self.hoverItem.SetIsHovered(False)
        self.hoverItem = item
        if self.hoverItem is not None:
            pass
            self.hoverItem.SetIsHovered(True)

    def ViewportToWorld(self, pos: QPointF) -> QPointF:
        fromCenter = pos - QPointF(self.width(), self.height()) / 2
        worldPos = fromCenter / (2 ** self.zoom) + self.offset
        return worldPos

    def CurrentMousePosition(self):
        return self.mapToScene(self.lastPos.toPoint())

    def ItemsUnderCursor(self, pos):
        return self.items(pos.toPoint())

    def UpdateView(self):
        matrix = QMatrix()
        matrix.scale(2 ** self.zoom, 2 ** self.zoom)
        self.setMatrix(matrix)
        self.setSceneRect(QRectF(self.offset.x(), self.offset.y(), 10, 10))

    def wheelEvent(self, event: QWheelEvent):
        numSteps = float(event.delta()) / 1000

        oldWorldPos = self.ViewportToWorld(event.posF())

        self.zoom = min(self.zoom + numSteps, 0)

        newWorldPos = self.ViewportToWorld(event.posF())

        delta = newWorldPos - oldWorldPos
        self.offset -= delta

        self.UpdateView()

        super().wheelEvent(event)

    def mousePressEvent(self, event):
        if self.isPanning or self.isMoving or self.isConnecting:
            return

        if event.button() == Qt.RightButton:
            # Pan with right mouse button
            self.isPanning = True
            self.lastPos = event.localPos()
        elif event.button() == Qt.LeftButton and self.actionsEnabled:
            items = self.ItemsUnderCursor(event.localPos())
            item = None
            for possible in items:
                if isinstance(possible, SelectableItem):
                    item = possible
                    break
            if item is not None:
                self.SelectItem(item)
                if item.IsMovableAtPoint(self.mapToScene(event.localPos().toPoint())):
                    self.isMoving = True
                else:
                    # Chance that it is a porthole. Let's check
                    if self.hoverPort is not None:
                        self.anchorPort = self.hoverPort
                        self.hoverPort = None
                        self.isConnecting = True
                        if self.IsFromPortFunc(self.anchorPort):
                            self.tempConnectionLine.SetFromPort(self.anchorPort)
                        else:
                            self.tempConnectionLine.SetToPort(self.anchorPort)
            else:
                self.SelectItem(None)

        self.UpdateHovers(event.localPos())

        if self.actionsEnabled:
            super().mousePressEvent(event)
        else:
            event.ignore()

    def mouseMoveEvent(self, event: QMouseEvent):
        # Update position movement
        currentPos = event.localPos()
        if self.lastPos is None:
            delta = QPointF()
        else:
            delta = (currentPos - self.lastPos) / (2 ** self.zoom)
        self.lastPos = currentPos

        if self.isPanning:
            self.offset -= delta
            self.UpdateView()
        elif self.isMoving:
            self.selectedItem.DoMove(currentPos, delta)
        else:
            self.UpdateHovers(event.localPos())

        if self.actionsEnabled:
            super().mouseMoveEvent(event)
        else:
            event.ignore()

    def UpdateHovers(self, pos: QPointF):
        if not self.actionsEnabled:
            self.HoverItem(None)
            if self.hoverPort is not None:
                self.hoverPort.SetHighlighted(False)
                self.hoverPort = None
            return

        items = self.ItemsUnderCursor(pos)

        firstSelectableItem = None
        for possible in items:
            if isinstance(possible, SelectableItem):
                firstSelectableItem = possible
                break

        if firstSelectableItem is not None:
            self.HoverItem(firstSelectableItem)
        else:
            self.HoverItem(None)

        if not self.actionsEnabled:
            return

        firstPortHole = None
        for possible in items:
            if isinstance(possible, BlockItem):
                localPosition = possible.mapFromScene(self.mapToScene(pos.toPoint()))
                w = possible.widget().childAt(localPosition.toPoint())
                if isinstance(w, PortHoleWidget):
                    firstPortHole = w
                    break

        if self.hoverPort is not None and firstPortHole != self.hoverPort:
            self.hoverPort.SetHighlighted(False)

        self.hoverPort = firstPortHole

        if self.hoverPort == self.anchorPort:
            self.hoverPort = None

        if self.isConnecting:
            self.tempConnectionLine.setVisible(True)
            self.tempConnectionLine.overridePos = self.mapToScene(pos.toPoint())

            if self.hoverPort is not None:
                if self.IsFromPortFunc(self.hoverPort):
                    if self.CanMakeConnectionFunc(self.hoverPort, self.anchorPort):
                        self.tempConnectionLine.SetFromPort(self.hoverPort)
                        self.hoverPort.SetHighlighted(True)
                    else:
                        self.tempConnectionLine.SetFromPort(None)
                else:
                    if self.CanMakeConnectionFunc(self.anchorPort, self.hoverPort):
                        self.tempConnectionLine.SetToPort(self.hoverPort)
                        self.hoverPort.SetHighlighted(True)
                    else:
                        self.tempConnectionLine.SetToPort(None)
            else:
                if self.IsFromPortFunc(self.anchorPort):
                    self.tempConnectionLine.SetToPort(None)
                else:
                    self.tempConnectionLine.SetFromPort(None)

            self.tempConnectionLine.UpdatePath()
        else:
            if self.tempConnectionLine is not None:
                self.tempConnectionLine.setVisible(False)
            if self.hoverPort is not None:
                self.hoverPort.SetHighlighted(True)

    def SetEnabled(self, state):
        for x in [x for x in self.items() if isinstance(x, QGraphicsProxyWidget)]:
            x.setEnabled(state)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.RightButton:
            self.isPanning = False
        elif event.button() == Qt.LeftButton and self.actionsEnabled:
            if self.isMoving:
                self.selectedItem.MoveFinished()
                self.isMoving = False
            if self.isConnecting:
                self.isConnecting = False
                self.anchorPort.SetHighlighted(False)
                if self.tempConnectionLine.GetFromPort() is not None and self.tempConnectionLine.GetToPort() is not None:
                    self.OnMakeConnectionFunc(self.tempConnectionLine.GetFromPort(),
                                              self.tempConnectionLine.GetToPort())

        self.tempConnectionLine.SetFromPort(None)
        self.tempConnectionLine.SetToPort(None)
        self.anchorPort = None

        self.UpdateHovers(event.localPos())

        if self.actionsEnabled:
            super().mouseReleaseEvent(event)
        else:
            event.ignore()

    def keyReleaseEvent(self, event: QKeyEvent):
        if not self.actionsEnabled:
            event.ignore()
            return

        if event.key() == Qt.Key.Key_Delete:
            if self.selectedItem is not None:
                self.selectedItem.TryDelete()
        if event.key() == Qt.Key.Key_D and event.modifiers() == Qt.Modifier.CTRL:
            if self.selectedItem is not None:
                newItem = self.selectedItem.TryDuplicate()
                if newItem is not None:
                    self.SelectItem(newItem)
