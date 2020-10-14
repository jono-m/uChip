from enum import Enum

from UI.WorldBrowser.BlockItem import *
from UI.WorldBrowser.PortHoles import *
from Util import Event


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

        self.selectionBox = self.scene().addRect(QRectF(), QPen(QBrush(QColor(52, 222, 235)), 2), QBrush(QColor(52, 222, 235, 50)))
        self.selectionBox.setZValue(100)
        self.selectionBox.setVisible(False)

        self.OnConnectionMade = Event()

        self.gridSpacing = QSize(30, 30)
        self.gridColor = QColor(50, 50, 50)

        self._actionsEnabled = True

        self.UpdateView()

    def Clear(self):
        for item in self.items():
            if item == self.tempConnectionLine or item == self.selectionBox:
                continue
            else:
                del item
        self._hoveredItems = []
        self._selectedItems = []
        self.anchorPort = None
        self._hoveredPortHole = None

    def FrameItems(self):
        QApplication.processEvents()
        itemsRect = QRectF()
        for item in self.items():
            itemsRect = itemsRect.united(item.boundingRect().translated(item.pos()))
        self._offset = itemsRect.center()

        self.UpdateView()

    def GetCenterPoint(self) -> QPointF:
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

    def UpdateHoveredItems(self):
        if self._actionsEnabled and self._state != State.MOVING and self._state != State.CONNECTING:
            items = self.GetHoveredSelectableItems()
        else:
            items = []
        for item in items:
            if item not in self._hoveredItems:
                item.SetIsHovered(True)
        for item in self._hoveredItems:
            if item not in items:
                item.SetIsHovered(False)
        self._hoveredItems = items

    def GetSelectionRect(self) -> QRect:
        selectionRect = QRect()
        selectionRect.setSize(QSize(abs(self._boxSelectionRectAnchor.x() - self._currentCursorPosition.x()),
                                    abs(self._boxSelectionRectAnchor.y() - self._currentCursorPosition.y())))
        selectionRect.moveCenter((self._currentCursorPosition + self._boxSelectionRectAnchor) / 2.0)
        return selectionRect

    def GetHoveredSelectableItems(self) -> typing.List[SelectableItem]:
        if self._state == State.SELECTING:
            return [item for item in self.items(self.GetSelectionRect()) if isinstance(item, SelectableItem)]
        else:
            for item in self.items(self._currentCursorPosition):
                if isinstance(item, SelectableItem):
                    return [item]
            return []

    def UpdateView(self):
        matrix = QMatrix()
        matrix.scale(2 ** self._zoom, 2 ** self._zoom)
        self.setMatrix(matrix)
        self.setSceneRect(QRectF(self._offset.x(), self._offset.y(), 10, 10))

    def wheelEvent(self, event: QWheelEvent):
        numSteps = float(event.delta()) / 1000

        oldWorldPos = self.mapToScene(self._currentCursorPosition)
        self._zoom = min(self._zoom + numSteps, 0)
        newWorldPos = self.mapToScene(self._currentCursorPosition)

        delta = newWorldPos - oldWorldPos
        self._offset -= delta

        self.UpdateView()

    def mousePressEvent(self, event):
        if self._state != State.IDLE:
            return

        if event.button() == Qt.RightButton:
            self._state = State.PANNING
        elif event.button() == Qt.LeftButton and self._actionsEnabled:
            if self._hoveredPortHole is not None:
                self._state = State.CONNECTING
                self.anchorPort = self._hoveredPortHole
            else:
                if len(self._hoveredItems) == 0:
                    self._state = State.SELECTING
                    self._boxSelectionRectAnchor = self._currentCursorPosition
                    if not WorldBrowser.ShouldMultiSelect():
                        self.ClearSelection()
                else:
                    hoveredItem = self._hoveredItems[0]
                    if WorldBrowser.ShouldMultiSelect():
                        if hoveredItem in self._selectedItems:
                            self.RemoveFromSelection(hoveredItem)
                        else:
                            self.AddToSelection(hoveredItem)
                    else:
                        if hoveredItem not in self._selectedItems:
                            self.ClearSelection()
                            self.AddToSelection(hoveredItem)
                        if hoveredItem.IsMovableAtPoint(self.mapToScene(self._currentCursorPosition)):
                            self._state = State.MOVING

        self.UpdateUI()

        super().mousePressEvent(event)

    @staticmethod
    def ShouldMultiSelect():
        return QApplication.keyboardModifiers() == Qt.ShiftModifier

    def UpdateUI(self):
        self.UpdateHoveredItems()
        self.UpdateHoveredPorthole()
        self.UpdateConnectionLine()
        self.UpdateSelectionBox()

    def mouseMoveEvent(self, event: QMouseEvent):
        # Update position movement
        newCursorPosition = event.localPos().toPoint()
        if self._currentCursorPosition is None:
            delta = QPointF()
        else:
            delta = (self.mapToScene(newCursorPosition) - self.mapToScene(self._currentCursorPosition))
        self._currentCursorPosition = newCursorPosition

        if self._state == State.PANNING:
            self._offset -= delta
            self.UpdateView()
        elif self._state == State.MOVING:
            for selectedItem in self._selectedItems:
                selectedItem.DoMove(self._currentCursorPosition, delta)

        self.UpdateUI()

        super().mouseMoveEvent(event)

    def SetActionsEnabled(self, actionsEnabled):
        self._actionsEnabled = actionsEnabled
        if not self._actionsEnabled:
            self.ClearSelection()
        for x in [x for x in self.items() if isinstance(x, QGraphicsProxyWidget)]:
            x.setEnabled(actionsEnabled)

    def GetHoveredPorthole(self) -> typing.Optional[PortHoleWidget]:
        for hoveredItem in self._hoveredItems:
            if isinstance(hoveredItem, BlockItem):
                localPosition = hoveredItem.mapFromScene(self.mapToScene(self._currentCursorPosition))
                w = hoveredItem.widget().childAt(localPosition.toPoint())
                if isinstance(w, PortHoleWidget):
                    return w

    def UpdateHoveredPorthole(self):
        if self._actionsEnabled and self._state == State.CONNECTING or self._state == State.IDLE:
            portHole = self.GetHoveredPorthole()
        else:
            portHole = None

        if portHole != self._hoveredPortHole:
            if self._hoveredPortHole is not None:
                self._hoveredPortHole.SetHighlighted(False)

            self._hoveredPortHole = portHole
            if self._state == State.CONNECTING:
                if not self.anchorPort.CanConnect(self._hoveredPortHole):
                    self._hoveredPortHole = None

            if self._hoveredPortHole is not None:
                self._hoveredPortHole.SetHighlighted(True)

    def UpdateConnectionLine(self):
        if self._state == State.CONNECTING and self._actionsEnabled:
            self.tempConnectionLine.setVisible(True)
            self.anchorPort.SetHighlighted(True)
            self.tempConnectionLine.overridePos = self.mapToScene(self._currentCursorPosition)
            self.tempConnectionLine.UpdatePath()
            self.tempConnectionLine.SetPortHoleA(self.anchorPort)
            self.tempConnectionLine.SetPortHoleB(self._hoveredPortHole)
        else:
            if self.anchorPort is not None:
                self.anchorPort.SetHighlighted(False)
            self.anchorPort = None
            self.tempConnectionLine.SetPortHoleA(None)
            self.tempConnectionLine.SetPortHoleB(None)
            self.tempConnectionLine.setVisible(False)

    def UpdateSelectionBox(self):
        if self._state == State.SELECTING and self._actionsEnabled:
            self.selectionBox.setVisible(True)
            self.selectionBox.prepareGeometryChange()
            self.selectionBox.setRect(self.mapToScene(self.GetSelectionRect()).boundingRect())
        else:
            self.selectionBox.setVisible(False)

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
            if self._state == State.CONNECTING:
                self._state = State.IDLE
                if self.anchorPort.CanConnect(self._hoveredPortHole):
                    self.anchorPort.DoConnect(self._hoveredPortHole)
            if self._state == State.SELECTING:
                self._state = State.IDLE
                if not WorldBrowser.ShouldMultiSelect():
                    self.ClearSelection()
                for item in self._hoveredItems:
                    self.AddToSelection(item)

        self.UpdateUI()

        super().mouseReleaseEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if not self._actionsEnabled or self._state != State.IDLE:
            event.ignore()
            return

        if event.key() == Qt.Key.Key_Delete:
            for item in self._selectedItems[:]:
                if item.TryDelete():
                    self._selectedItems.remove(item)
                    if item in self._hoveredItems:
                        self._hoveredItems.remove(item)
                    self._hoveredPortHole = None
        if event.key() == Qt.Key.Key_D and event.modifiers() == Qt.Modifier.CTRL:
            if self.selectedItem is not None:
                newItem = self.selectedItem.TryDuplicate()
                if newItem is not None:
                    self.SelectItem(newItem)
