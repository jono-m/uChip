from UI.WorldBrowser.PortHoles import *
from UI.WorldBrowser.BlockItem import *
from Util import Event
import shiboken2
from enum import Enum

class State(Enum):
    IDLE = 0
    PANNING = 1
    MOVING = 2
    CONNECTING = 3
    SELECTING = 4

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
        self._offset = QPointF(0, 0)
        self.setRenderHint(QPainter.Antialiasing)
        self._zoom = 0

        # Set up interface tracking elements
        self._selectedItems: typing.List[SelectableItem] = []
        self._hoveredItems: typing.List[SelectableItem] = []

        self._state = State.IDLE

        self._boxSelectionRectAnchor = QPointF()
        self._currentCursorPosition = None

        self.tempConnectionLine = ConnectionItem(self.scene(), None, None)
        self.tempConnectionLine.setVisible(False)
        self.anchorPort: typing.Optional[PortHoleWidget] = None
        self._hoveredPortHole: typing.Optional[PortHoleWidget] = None

        self.OnConnectionMade = Event()

        self.gridSpacing = QSize(30, 30)
        self.gridColor = QColor(50, 50, 50)

        self._actionsEnabled = True

        self.UpdateView()

    def Clear(self):
        for item in self.items():
            if item == self.tempConnectionLine:
                continue
            else:
                del item
        self._hoveredItems = []
        self._selectedItems = []

    def FrameItems(self):
        QApplication.processEvents()
        itemsRect = QRectF()
        for item in self.items():
            if isinstance(item, QGraphicsProxyWidget):
                item.widget().adjustSize()
                item.widget().repaint()
            itemsRect = itemsRect.united(item.boundingRect().translated(item.pos()))
        self._offset = itemsRect.center()

        self.UpdateView()

    def GetCenterPoint(self):
        return self.mapToScene(self.rect().center())

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)

        if not self._actionsEnabled:
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

    def ClearSelection(self):
        for item in self._selectedItems:
            item.SetIsSelected(False)
        self._selectedItems = []

    def AddToSelection(self, item: SelectableItem):
        if item in self._selectedItems:
            return
        item.SetIsSelected(True)
        self._selectedItems.append(item)

    def RemoveFromSelection(self, item: SelectableItem):
        if item not in self._selectedItems:
            return
        item.SetIsSelected(False)
        self._selectedItems.remove(item)

    def SetHoveredItems(self, items: typing.List[SelectableItem]):
        for item in items:
            if item not in self.hoverItems:
                item.SetIsHovered(True)
        for item in self.hoverItems:
            if item not in items:
                item.SetIsHovered(False)
        self._hoveredItems = items

    def ViewportToWorld(self, pos: QPointF) -> QPointF:
        fromCenter = pos - QPointF(self.width(), self.height()) / 2
        worldPos = fromCenter / (2 ** self._zoom) + self._offset
        return worldPos

    def CurrentMousePosition(self):
        return self.mapToScene(self._currentCursorPosition.toPoint())

    def GetHoveredSelectableItems(self):
        if self._state != State.SELECTING:
            return self.items(self._currentCursorPosition)
        width = abs(self._boxSelectionRectAnchor.x() - self._currentCursorPosition.x())
        height = abs(self._boxSelectionRectAnchor.y() - self._currentCursorPosition.y())
        center = (self._boxSelectionRectCorner + self._boxSelectionRectAnchor) / 2.0
        selectionRect = QRectF()
        selectionRect.setSize(QSizeF(width, height))
        selectionRect.moveCenter(center)
        return [item for item in self.items(selectionRect) if isinstance(item, SelectableItem)]

    def UpdateView(self):
        matrix = QMatrix()
        matrix.scale(2 ** self._zoom, 2 ** self._zoom)
        self.setMatrix(matrix)
        self.setSceneRect(QRectF(self._offset.x(), self._offset.y(), 10, 10))

    def wheelEvent(self, event: QWheelEvent):
        numSteps = float(event.delta()) / 1000

        oldWorldPos = self.ViewportToWorld(event.posF())

        self._zoom = min(self._zoom + numSteps, 0)

        newWorldPos = self.ViewportToWorld(event.posF())

        delta = newWorldPos - oldWorldPos
        self._offset -= delta

        self.UpdateView()

        super().wheelEvent(event)

    def mousePressEvent(self, event):
        if self._state != State.IDLE:
            return

        if event.button() == Qt.RightButton:
            # Pan with right mouse button
            self._state = State.PANNING
        elif event.button() == Qt.LeftButton and self._actionsEnabled:
            # Chance that it is a porthole. Let's check
            if self._hoveredPortHole is not None:
                self._state = State.CONNECTING

                self.anchorPort = self._hoveredPortHole
                self.
            else:
                if len(self._hoveredItems) == 0:
                    self._state = State.SELECTING
                    self._boxSelectionRectAnchor = self._currentCursorPosition
                else:
                    hoveredItem = self._hoveredItems[0]
                    if self.ShouldMultiSelect():
                        if hoveredItem in self._selectedItems:
                            self.RemoveFromSelection(hoveredItem)
                        else:
                            self.AddToSelection(hoveredItem)
                    else:
                        if hoveredItem not in self._selectedItems:
                            self.ClearSelection()
                            self.AddToSelection(hoveredItem)
                        if hoveredItem.IsMovableAtPoint(self.mapToScene(event.localPos().toPoint())):
                            self._state = State.MOVING

        if self._actionsEnabled:
            super().mousePressEvent(event)
        else:
            event.ignore()

    def ShouldMultiSelect(self):
        return QApplication.keyboardModifiers() == Qt.ShiftModifier

    def mouseMoveEvent(self, event: QMouseEvent):
        # Update position movement
        newCursorPosition = event.localPos()
        if self._currentCursorPosition is None:
            delta = QPointF()
        else:
            delta = (newCursorPosition - self._currentCursorPosition) / (2 ** self._zoom)
        self._currentCursorPosition = newCursorPosition

        if self._state == State.PANNING:
            self._offset -= delta
            self.UpdateView()
        elif self._state == State.MOVING:
            for selectedItem in self._selectedItems:
                selectedItem.DoMove(self._currentCursorPosition, delta)
        else:
            self.SetHoveredItems(self.GetHoveredSelectableItems())
            self.SetHoveredPortHole(self.GetHoveredPorthole())
            self.UpdateConnectionLine()

        if self._actionsEnabled:
            super().mouseMoveEvent(event)
        else:
            event.ignore()

    def SetActionsEnabled(self, actionsEnabled):
        self._actionsEnabled = actionsEnabled
        if not self._actionsEnabled:
            self.SetHoveredItems([])
            self.SetHoveredPortHole(None)
            self.ClearSelection()
            self.SetConnectionLinePort(None)
        for x in [x for x in self.items() if isinstance(x, QGraphicsProxyWidget)]:
            x.setEnabled(actionsEnabled)

    def UpdateSelectionHovers(self):
        if not self._actionsEnabled:
            return

    def GetHoveredPorthole(self) -> typing.Optional[PortHoleWidget]:
        for hoveredItem in self._hoveredItems:
            if isinstance(hoveredItem, BlockItem):
                localPosition = hoveredItem.mapFromScene(self.mapToScene(self._currentCursorPosition))
                w = hoveredItem.widget().childAt(localPosition.toPoint())
                if isinstance(w, PortHoleWidget):
                    return w

    def SetHoveredPortHole(self, portHole: typing.Optional[PortHoleWidget]):
        if portHole != self._hoveredPortHole:
            if self._hoveredPortHole is not None:
                self._hoveredPortHole.SetHighlighted(False)

            self._hoveredPortHole = portHole
            if self._isConnecting:
                if not self.anchorPort.CanConnect(self._hoveredPortHole):
                    self._hoveredPortHole = None

            if self._hoveredPortHole is not None:
                self._hoveredPortHole.SetHighlighted(True)

    def SetConnectionLinePort(self, port: typing.Optional[PortHoleWidget]):
        if port is None:
            self.tempConnectionLine.SetFromPort(None)
            self.tempConnectionLine.SetToPort(None)
            self.tempConnectionLine.setVisible(False)
        else:
            self.tempConnectionLine.setVisible(True)

            if self.anchorPort is None:
                refPort = port
            else:
                refPort = self.anchorPort
            if self.IsFromPortFunc(refPort):
                self.tempConnectionLine.SetFromPort(port)
            else:
                self.tempConnectionLine.SetToPort(port)

    def UpdateConnectionLine(self):
        if self._state != State.CONNECTING:
            self.SetConnectionLinePort(None)
        else:
            self.tempConnectionLine.overridePos = self.mapToScene(self._currentCursorPosition)
            self.tempConnectionLine.UpdatePath()

            self.SetConnectionLinePort(self._hoveredPortHole)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        if self._state == State.PANNING:
            if event.button() == Qt.RightButton:
                self._state = State.IDLE
        elif event.button() == Qt.LeftButton:
            if self._state == State.MOVING:
                for selectedItem in self._selectedItems:
                    selectedItem.MoveFinished()
                self._state = State.IDLE
            if self.state == State.CONNECTING:
                self._state = State.IDLE
                self.anchorPort.SetHighlighted(False)
                if self.tempConnectionLine.GetFromPort() is not None and self.tempConnectionLine.GetToPort() is not None:
                    self.OnMakeConnectionFunc(self.tempConnectionLine.GetFromPort(),
                                              self.tempConnectionLine.GetToPort())

        self.tempConnectionLine.SetFromPort(None)
        self.tempConnectionLine.SetToPort(None)
        self.anchorPort = None

        self.UpdateSelectionHovers(event.localPos())

        if self._actionsEnabled:
            super().mouseReleaseEvent(event)
        else:
            event.ignore()

    def keyReleaseEvent(self, event: QKeyEvent):
        if not self._actionsEnabled:
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
