from typing import Set, Optional, List

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QApplication
from PySide6.QtGui import QPainter, QBrush, QColor, QTransform, QWheelEvent, QMouseEvent, QPen, QKeyEvent
from PySide6.QtCore import QPointF, Qt, QRectF, QSizeF, QLineF, Signal

from UI.ChipEditor.ChipItem import ChipItem

from enum import Enum, auto


class State(Enum):
    IDLE = auto()
    PANNING = auto()
    SELECTING = auto()
    MOVING = auto()


class SelectionMode:
    NORMAL = auto()
    MODIFY = auto()


class ChipSceneViewer(QGraphicsView):
    selectionChanged = Signal(list)

    def __init__(self):
        super().__init__()

        # Set up scene
        scene = QGraphicsScene()
        self.setScene(scene)

        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)

        self._offset = QPointF(0, 0)
        self._zoom = 0

        self.backgroundColor = QColor(40, 40, 40)

        self.gridSpacing = QSizeF(60, 60)
        self.gridThickness = 1
        self.gridColor = QColor(100, 100, 100)
        self.gridZoomThreshold = -1.5
        self.showGrid = True

        self.selectionBoxStrokeColor = QColor(52, 222, 235)
        self.selectionBoxFillColor = QColor(52, 222, 235, 50)
        self.selectionBoxThickness = 2
        self._editing = True

        self._hoveredItems: List[ChipItem] = []
        self._selectedItems: List[ChipItem] = []
        self._sceneItems: Set[ChipItem] = set()

        self._boxSelectionRectAnchor = QPointF()
        self._currentCursorPosition = QPointF()

        self.selectionBox = self.scene().addRect(QRectF(),
                                                 QPen(self.selectionBoxStrokeColor, self.selectionBoxThickness),
                                                 QBrush(self.selectionBoxFillColor))
        self.selectionBox.setVisible(False)

        self._state = State.IDLE

        self.UpdateView()

    def SetEditing(self, editing: bool):
        self._editing = editing

        self.showGrid = editing

        for item in self._sceneItems:
            item.SetEditDisplay(editing)

        if not editing:
            self.DeselectAll()

    def GetSelectedItems(self):
        return self._selectedItems

    def AddItem(self, item: ChipItem):
        if item not in self._sceneItems:
            self._sceneItems.add(item)
            self.scene().addItem(item.GraphicsObject())
        item.SetEditDisplay(self._editing)
        return item

    def RemoveItem(self, item: ChipItem):
        self.DeselectItem(item)
        if item in self._hoveredItems:
            self._hoveredItems.remove(item)

        if item in self._sceneItems:
            self._sceneItems.remove(item)
            self.scene().removeItem(item.GraphicsObject())

    def GetItems(self):
        return self._sceneItems

    def RemoveAll(self):
        self._hoveredItems.clear()
        self._selectedItems.clear()
        for item in self._sceneItems.copy():
            self.RemoveItem(item)

    def SelectItem(self, item: ChipItem):
        if item not in self._selectedItems:
            item.SetSelected(True)
            self._selectedItems.append(item)

    def ToggleSelectItem(self, item: ChipItem):
        if item in self._selectedItems:
            self.DeselectItem(item)
        else:
            self.SelectItem(item)

    def DeselectItem(self, item: ChipItem):
        if item in self._selectedItems:
            item.SetSelected(False)
            self._selectedItems.remove(item)

    def DeselectAll(self):
        for item in self._selectedItems.copy():
            self.DeselectItem(item)

    def Recenter(self):
        itemsRect = QRectF()
        for item in self._sceneItems:
            itemsRect = itemsRect.united(item.GraphicsObject().boundingRect().translated(item.GraphicsObject().pos()))
        self._offset = itemsRect.center()

        self.UpdateView()

    def CenterItem(self, item: ChipItem):
        QApplication.processEvents()
        sceneCenter = self.mapToScene(self.rect().center())
        currentCenter = item.GraphicsObject().sceneBoundingRect().center()
        delta = sceneCenter - currentCenter
        item.Move(delta)

    def UpdateView(self):
        matrix = QTransform()
        matrix.scale(2 ** self._zoom, 2 ** self._zoom)
        self.setTransform(matrix)
        self.setSceneRect(QRectF(self._offset.x(), self._offset.y(), 10, 10))

        self.UpdateSelectionBox()
        self.UpdateHoveredItems()

    @staticmethod
    def GetSelectionMode():
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            return SelectionMode.MODIFY
        return SelectionMode.NORMAL

    def CreateSelectionRect(self) -> QRectF:
        cursorScene = self.mapToScene(self._currentCursorPosition.toPoint())
        if self._state is State.SELECTING:
            selectionRect = QRectF(0, 0, abs(self._boxSelectionRectAnchor.x() - cursorScene.x()),
                                   abs(self._boxSelectionRectAnchor.y() - cursorScene.y()))
            selectionRect.moveCenter((cursorScene + self._boxSelectionRectAnchor) / 2.0)
        else:
            selectionRect = QRectF(cursorScene, QSizeF())
        return selectionRect

    def UpdateHoveredItems(self):
        if self._editing and self._state is not State.MOVING:
            items = [item for item in self.scene().items(self.selectionBox.sceneBoundingRect())]
        else:
            items = []

        matched = []
        for item in self._sceneItems:
            if item.CanSelect() and item.GraphicsObject() in items:
                matched.append(item)
        matched.sort(key=lambda item: item.GraphicsObject().zValue())

        for item in matched:
            if item not in self._hoveredItems and item.CanSelect():
                item.SetHovered(True)
        for item in self._hoveredItems:
            if item not in matched:
                item.SetHovered(False)
        self._hoveredItems = matched

    def UpdateSelectionBox(self):
        if self._state == State.SELECTING:
            self.selectionBox.setVisible(True)
            self.selectionBox.prepareGeometryChange()
        else:
            self.selectionBox.setVisible(False)
        self.selectionBox.setRect(self.CreateSelectionRect())

    def drawBackground(self, painter: QPainter, rect: QRectF):
        self.setBackgroundBrush(QBrush(self.backgroundColor))

        super().drawBackground(painter, rect)

        if self._zoom <= self.gridZoomThreshold or not self.showGrid:
            return

        painter.setPen(QPen(self.gridColor, self.gridThickness))

        lines = []
        if self.gridSpacing.width() > 0:
            xStart = rect.left() - rect.left() % self.gridSpacing.width()
            while xStart <= rect.right():
                line = QLineF(xStart, rect.bottom(), xStart, rect.top())
                lines.append(line)
                xStart = xStart + self.gridSpacing.width()

        if self.gridSpacing.height() > 0:
            yStart = rect.top() - rect.top() % self.gridSpacing.height()
            while yStart <= rect.bottom():
                line = QLineF(rect.left(), yStart, rect.right(), yStart)
                lines.append(line)
                yStart = yStart + self.gridSpacing.height()

        painter.drawLines(lines)

    def wheelEvent(self, event: QWheelEvent):
        numSteps = float(event.angleDelta().y()) / 1000

        oldWorldPos = self.mapToScene(self._currentCursorPosition.toPoint())
        self._zoom = min(self._zoom + numSteps, 0)
        self.UpdateView()
        newWorldPos = self.mapToScene(self._currentCursorPosition.toPoint())

        delta = newWorldPos - oldWorldPos
        self._offset -= delta

        self.UpdateView()

    def mousePressEvent(self, event):
        if self._state != State.IDLE:
            return

        if event.button() == Qt.RightButton:
            self._state = State.PANNING
        elif event.button() == Qt.LeftButton and self._editing:
            if len(self._hoveredItems) == 0:
                self._state = State.SELECTING
                self._boxSelectionRectAnchor = self.mapToScene(self._currentCursorPosition.toPoint())
            else:
                hoveredItem = self._hoveredItems[0]
                if self.GetSelectionMode() is SelectionMode.MODIFY:
                    self.ToggleSelectItem(hoveredItem)
                    self.selectionChanged.emit(self._selectedItems)
                else:
                    if hoveredItem not in self._selectedItems:
                        self.DeselectAll()
                        self.SelectItem(hoveredItem)
                        self.selectionChanged.emit(self._selectedItems)
                    if hoveredItem.CanMove(self.mapToScene(self._currentCursorPosition.toPoint())):
                        self._state = State.MOVING

        self.UpdateView()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        # Update position movement
        newCursorPosition = event.localPos()
        if self._currentCursorPosition is None:
            deltaScene = QPointF()
        else:
            deltaScene = (self.mapToScene(newCursorPosition.toPoint()) -
                          self.mapToScene(self._currentCursorPosition.toPoint()))
        self._currentCursorPosition = newCursorPosition

        if self._state is State.PANNING:
            self._offset -= deltaScene
            self.UpdateView()
        elif self._state is State.MOVING:
            for selectedItem in self._selectedItems:
                selectedItem.Move(deltaScene)

        self.UpdateView()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        if self._state == State.PANNING:
            if event.button() == Qt.RightButton:
                self._state = State.IDLE
        elif self._state == State.SELECTING:
            if event.button() == Qt.LeftButton:
                self._state = State.IDLE
                if self.GetSelectionMode() is SelectionMode.MODIFY:
                    for item in self._hoveredItems:
                        self.ToggleSelectItem(item)
                else:
                    self.DeselectAll()
                    for item in self._hoveredItems:
                        self.SelectItem(item)
                self.selectionChanged.emit(self._selectedItems)
        elif self._state == State.MOVING:
            if event.button() == Qt.LeftButton:
                self._state = State.IDLE

        self.UpdateView()

        super().mouseReleaseEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.DeleteSelected()

        if event.key() == Qt.Key.Key_D and event.modifiers() == Qt.Modifier.CTRL:
            self.DuplicateSelected()

        super().keyReleaseEvent(event)

    def DeleteSelected(self):
        for item in self._viewer.GetSelectedItems().copy():
            if item.CanDelete():
                item.Delete()
                self._viewer.RemoveItem(item)

    def DuplicateSelected(self):
        newItems = []
        for item in self._viewer.GetSelectedItems():
            if item.CanDuplicate():
                newItem = item.Duplicate()
                newItem.Move(QPointF(50, 50))
                self._viewer.AddItem(newItem)
                newItems.append(newItem)
        if newItems:
            self._viewer.DeselectAll()
            [self._viewer.SelectItem(item) for item in newItems]
            self._viewer.selectionChanged.emit(self._viewer.GetSelectedItems())
