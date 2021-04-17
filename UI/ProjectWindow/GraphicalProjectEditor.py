from enum import Enum
from ProjectSystem.Project import Project
from UI.ProjectWindow.GraphicalProjectEntity import GraphicalProjectEntity
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import typing


class State(Enum):
    IDLE = 0
    PANNING = 1
    MOVING = 2
    CONNECTING = 3
    SELECTING = 4


class GraphicalProjectEditor(QGraphicsView):
    def __init__(self, project: Project):
        super().__init__()

        self._project = project
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
        self._selectedEntities: typing.List[GraphicalProjectEntity] = []
        self._hoveredEntities: typing.List[GraphicalProjectEntity] = []

        self._state = State.IDLE

        self._boxSelectionRectAnchor = QPointF()
        self._currentCursorPosition = QPoint()

        self.selectionBox = self.scene().addRect(QRectF(), QPen(QBrush(QColor(52, 222, 235)), 2),
                                                 QBrush(QColor(52, 222, 235, 50)))
        self.selectionBox.setZValue(100)
        self.selectionBox.setVisible(False)

        self.gridSpacing = QSize(60, 60)
        self.gridColor = QColor(50, 50, 50)

        self.gridThreshold = -1.5

        self.UpdateView()

    def FitAllItems(self):
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

        if self._zoom <= self.gridThreshold:
            return

        if not self._actionsEnabled:
            return

        painter.setPen(self.gridColor)

        lines = []
        if self.gridSpacing.width() > 0:
            xStart = rect.left() - rect.left() % self.gridSpacing.width()
            while xStart <= rect.right():
                line = QLine(int(xStart), int(rect.bottom()), int(xStart), int(rect.top()))
                lines.append(line)
                xStart = xStart + self.gridSpacing.width()

        if self.gridSpacing.height() > 0:
            yStart = rect.top() - rect.top() % self.gridSpacing.height()
            while yStart <= rect.bottom():
                line = QLine(int(rect.left()), int(yStart), int(rect.right()), int(yStart))
                lines.append(line)
                yStart = yStart + self.gridSpacing.height()

        painter.drawLines(lines)

    def ClearSelection(self):
        for item in self._selectedItems:
            item.SetIsSelected(False)
        self._selectedEntities = []

    def AddToSelection(self, entity: GraphicalProjectEntity):
        if entity in self._selectedEntities:
            return
        entity.SetIsSelected(True)
        self._selectedEntities.append(entity)

    def RemoveFromSelection(self, entity: GraphicalProjectEntity):
        if entity not in self._selectedEntities:
            return
        entity.SetIsSelected(False)
        self._selectedEntities.remove(entity)

    def UpdateHoveredItems(self):
        if self._actionsEnabled and self._state != State.MOVING:
            items = self.GetHoveredSelectableItems()
        else:
            items = []
        for item in items:
            if item not in self._hoveredEntities:
                item.SetIsHovered(True)
        for item in self._hoveredEntities:
            if item not in items:
                item.SetIsHovered(False)
        self._hoveredEntities = items

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
        self.UpdateView()
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
                if len(self._hoveredEntities) == 0:
                    self._state = State.SELECTING
                    self._boxSelectionRectAnchor = self._currentCursorPosition
                    if not GraphicalProjectEditor.ShouldMultiSelect():
                        self.ClearSelection()
                else:
                    hoveredItem = self._hoveredEntities[0]
                    if GraphicalProjectEditor.ShouldMultiSelect():
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

        sceneCoordinates = self.mapToScene(newCursorPosition)
        StatusBar.globalStatusBar.SetCoordinates(sceneCoordinates.toPoint())

    def SetActionsEnabled(self, actionsEnabled):
        self._actionsEnabled = actionsEnabled
        if not self._actionsEnabled:
            self.ClearSelection()
        for x in [x for x in self.items() if isinstance(x, QGraphicsProxyWidget)]:
            x.setEnabled(actionsEnabled)

    def GetHoveredPorthole(self) -> typing.Optional[PortHoleWidget]:
        for hoveredItem in self._hoveredEntities:
            if isinstance(hoveredItem, GraphicalProjectEntity):
                localPosition = hoveredItem.mapFromScene(self.mapToScene(self._currentCursorPosition))
                w = hoveredItem.blockWidget.childAt(localPosition.toPoint())
                if isinstance(w, PortHoleWidget):
                    return w

    def UpdateHoveredPorthole(self):
        if self._actionsEnabled and self._state == State.CONNECTING or self._state == State.IDLE:
            portHole = self.GetHoveredPorthole()
        else:
            portHole = None

        if portHole != self._hoveredPortHole:
            if self._hoveredPortHole is not None:
                self._hoveredPortHole.SetIsHovered(False)
                self._hoveredPortHole.SetIsHighlighted(False)

            self._hoveredPortHole = portHole
            if self._state == State.CONNECTING:
                if not self.anchorPort.CanConnect(self._hoveredPortHole):
                    self._hoveredPortHole = None
                else:
                    self._hoveredPortHole.SetIsHighlighted(True)

            if self._hoveredPortHole is not None:
                self._hoveredPortHole.SetIsHovered(True)

    def UpdateConnectionLine(self):
        if self._state == State.CONNECTING and self._actionsEnabled:
            self.tempConnectionLine.setVisible(True)
            self.anchorPort.SetIsHighlighted(True)
            self.tempConnectionLine.overridePos = self.mapToScene(self._currentCursorPosition)
            self.tempConnectionLine.UpdatePath()
            self.tempConnectionLine.SetPortHoleA(self.anchorPort)
            self.tempConnectionLine.SetPortHoleB(self._hoveredPortHole)
        else:
            if self.anchorPort is not None:
                self.anchorPort.SetIsHighlighted(False)
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
                if not GraphicalProjectEditor.ShouldMultiSelect():
                    self.ClearSelection()
                for item in self._hoveredEntities:
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
                    if item in self._hoveredEntities:
                        self._hoveredEntities.remove(item)
                    self._hoveredPortHole = None
        if event.key() == Qt.Key.Key_D and event.modifiers() == Qt.Modifier.CTRL:
            selectedItemsCopy = self._selectedItems[:]
            self.ClearSelection()
            for item in selectedItemsCopy:
                newItem = item.TryDuplicate()
                if newItem is not None:
                    self.AddToSelection(newItem)
