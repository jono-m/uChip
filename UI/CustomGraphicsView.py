from typing import List, Tuple, Optional
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QGraphicsProxyWidget, \
    QGraphicsRectItem
from PySide6.QtGui import QPen, QColor, QPainter, QBrush, QWheelEvent, QTransform, QGuiApplication
from PySide6.QtCore import Qt, QPointF, QSizeF, QRectF, QLineF, QRect, QMarginsF, QPoint
from enum import Enum, auto


class CustomGraphicsViewState(Enum):
    IDLE = auto()
    PANNING = auto()
    MOVING = auto()
    RESIZING = auto()
    BAND_SELECTING = auto()


class CustomGraphicsViewItem:
    def __init__(self, widget: QWidget):
        self.widget = widget
        self.graphicsProxy = QGraphicsProxyWidget()
        self.graphicsProxy.setWidget(widget)
        self.borderRectItem = QGraphicsRectItem()
        self.borderWidth = 5
        self.borderVisible = True
        self.borderColor = QColor(255, 255, 255)

    def UpdateGeometry(self):
        self.borderRectItem.setPen(QPen(self.borderColor, self.borderWidth))
        self.borderRectItem.setRect(
            QRectF(self.graphicsProxy.scenePos(), self.graphicsProxy.size()))
        self.borderRectItem.setVisible(self.borderVisible)

    def SetRect(self, rect: QRectF):
        self.graphicsProxy.setPos(rect.topLeft())
        self.graphicsProxy.resize(rect.size())
        self.UpdateGeometry()

    def SetPosition(self, point: QPointF):
        self.graphicsProxy.setPos(point)


class CustomGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()

        scene = QGraphicsScene()
        self.setScene(scene)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setMouseTracking(True)

        self.viewOffset = QPointF(0, 0)
        self.zoom = 1

        self.setBackgroundBrush(QColor(30, 30, 30))
        self.gridSpacing = QSizeF(60, 60)
        self.gridThickness = 1
        self.gridColor = QColor(50, 50, 50)
        self.gridZoomThreshold = 0.25
        self.showGrid = True

        self.scrollSensitivity = 1 / 1000

        self.state = CustomGraphicsViewState.IDLE

        self.mouseDeltaScenePosition = QPointF()
        self.mouseScenePosition = QPointF()
        self.itemUnderMouse: Optional[CustomGraphicsViewItem] = None
        self.resizeHandleIndexUnderMouse = -1

        self.selectionBoxRectItem = QGraphicsRectItem()
        self.selectionBoxRectScreenSize = 5
        self.selectionBoxRectColor = QColor(100, 100, 255)

        self.allItems: List[CustomGraphicsViewItem] = []
        self.selectedItems: List[CustomGraphicsViewItem] = []
        self.hoveredItems: List[CustomGraphicsViewItem] = []
        self.isInteractive = True

        self.UpdateViewMatrix()

    def UpdateViewMatrix(self):
        transform = QTransform()
        transform.scale(self.zoom, self.zoom)
        self.setTransform(transform)
        self.setSceneRect(QRectF(self.viewOffset, QSizeF()))

    def wheelEvent(self, event: QWheelEvent):
        self.UpdateMouseInfo(event.position().toPoint())
        self.UpdateZoom(self.mouseScenePosition,
                        self.zoom + float(event.angleDelta().y()) * self.scrollSensitivity)

    def UpdateZoom(self, scenePositionAnchor: QPointF, newZoom: float):
        anchorScreenSpace = self.mapFromScene(scenePositionAnchor)
        self.zoom = min(max(newZoom, 0.05), 1)
        self.UpdateViewMatrix()
        newAnchorPosition = self.mapToScene(anchorScreenSpace)
        self.viewOffset -= newAnchorPosition - scenePositionAnchor
        self.UpdateViewMatrix()
        self.UpdateItemVisuals()

    def mousePressEvent(self, event):
        self.UpdateMouseInfo(event.pos())
        if self.state != CustomGraphicsViewState.IDLE:
            return
        if event.button() == Qt.LeftButton:
            if self.hoveredResizeHandle == -1 and s
                self.UpdateItemVisuals()
        if event.button() == Qt.RightButton:
            self.state = CustomGraphicsViewState.PANNING

        self.UpdateCursor()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.UpdateMouseInfo(event.pos())

        if self.state == CustomGraphicsViewState.PANNING and event.button() == Qt.RightButton:
            self.state = CustomGraphicsViewState.IDLE
        elif self.state == CustomGraphicsViewState.MOVING and event.button() == Qt.LeftButton:
            self.state = CustomGraphicsViewState.IDLE
        elif self.state == CustomGraphicsViewState.RESIZING and event.button() == Qt.LeftButton:
            self.state = CustomGraphicsViewState.IDLE
        self.UpdateCursor()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        self.UpdateMouseInfo(event.pos())
        if self.state == CustomGraphicsViewState.PANNING:
            self.viewOffset -= self.mouseInfo.deltaScenePosition
            self.UpdateViewMatrix()
        elif self.state == CustomGraphicsViewState.MOVING:
            snappedDelta = self.mouseInfo.scenePosition - self._movingInitialPosition
            for item in self.selectedItems:
                item.graphicsProxy.setPos(
                    item.graphicsProxy.scenePos() + snappedDelta)
            self.UpdateItemVisuals()
        elif self.state == CustomGraphicsViewState.RESIZING:
            newRect = QRectF(self._resizingItemInitialRect)
            if self._resizingHandleIndex == 0:
                newRect.setTopLeft(self.mouseInfo.scenePosition)
            elif self._resizingHandleIndex == 1:
                newRect.setTop(self.mouseInfo.scenePosition.y())
            elif self._resizingHandleIndex == 2:
                newRect.setTopRight(self.mouseInfo.scenePosition)
            elif self._resizingHandleIndex == 3:
                newRect.setLeft(self.mouseInfo.scenePosition.x())
            elif self._resizingHandleIndex == 4:
                newRect.setRight(self.mouseInfo.scenePosition.x())
            elif self._resizingHandleIndex == 5:
                newRect.setBottomLeft(self.mouseInfo.scenePosition)
            elif self._resizingHandleIndex == 6:
                newRect.setBottom(self.mouseInfo.scenePosition.y())
            elif self._resizingHandleIndex == 7:
                newRect.setBottomRight(self.mouseInfo.scenePosition)
            self._resizingItem.SetRect(newRect)
        else:
            self.hoveredItems = [] if self.mouseInfo.item is None else [self.mouseInfo.item]
            self.UpdateItemVisuals()
        self.UpdateCursor()
        super().mouseMoveEvent(event)

    def UpdateMouseInfo(self, mousePosition: QPoint):
        newMousePosition = self.mapToScene(mousePosition)
        self.mouseInfo.deltaScenePosition = newMousePosition - self.mouseInfo.scenePosition
        self.mouseInfo.scenePosition = newMousePosition

        self.mouseInfo.item = None
        self.mouseInfo.itemHandleIndex = -1
        for item in sorted(self.allItems, key=lambda x: x.graphicsProxy.zValue()):
            if item.resizeHandlesVisible:
                for i, resizeHandle in enumerate(item.resizeHandles):
                    if resizeHandle.contains(self.mouseInfo.scenePosition):
                        self.mouseInfo.item = item
                        self.mouseInfo.itemHandleIndex = i
                        return
            if item.borderRectItem.contains(self.mouseInfo.scenePosition):
                self.mouseInfo.item = item
                return

    def UpdateCursor(self):
        if self.state == CustomGraphicsViewState.PANNING:
            self.SetCursorHelper(Qt.ClosedHandCursor)
        elif self.state == CustomGraphicsViewState.MOVING:
            self.SetCursorHelper(Qt.SizeAllCursor)
        elif self.state == CustomGraphicsViewState.RESIZING:
            pass
        elif self.state == CustomGraphicsViewState.IDLE:
            if self.mouseInfo.item in self.selectedItems:
                if self.mouseInfo.itemHandleIndex == -1:
                    self.SetCursorHelper(Qt.SizeAllCursor)
                elif self.mouseInfo.itemHandleIndex == 0 or self.mouseInfo.itemHandleIndex == 7:
                    self.SetCursorHelper(Qt.SizeFDiagCursor)
                elif self.mouseInfo.itemHandleIndex == 1 or self.mouseInfo.itemHandleIndex == 6:
                    self.SetCursorHelper(Qt.SizeVerCursor)
                elif self.mouseInfo.itemHandleIndex == 2 or self.mouseInfo.itemHandleIndex == 5:
                    self.SetCursorHelper(Qt.SizeBDiagCursor)
                elif self.mouseInfo.itemHandleIndex == 3 or self.mouseInfo.itemHandleIndex == 4:
                    self.SetCursorHelper(Qt.SizeHorCursor)
            else:
                self.SetCursorHelper(None)
        else:
            self.SetCursorHelper(None)

    @staticmethod
    def SetCursorHelper(cursorShape):
        currentCursorShape = None if QGuiApplication.overrideCursor() is None \
            else QGuiApplication.overrideCursor().shape()
        if currentCursorShape != cursorShape:
            QGuiApplication.restoreOverrideCursor()
            if cursorShape is not None:
                QGuiApplication.setOverrideCursor(cursorShape)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)

        if self.zoom <= self.gridZoomThreshold or not self.showGrid:
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

    def AddItem(self, item: CustomGraphicsViewItem):
        self.allItems.append(item)
        self.scene().addItem(item.borderRectItem)
        self.scene().addItem(item.graphicsProxy)
        [self.scene().addItem(x) for x in item.resizeHandles]

    def SetInteractive(self, interactive: bool):
        self.isInteractive = interactive
        if not interactive:
            self.hoveredItems = []
            self.selectedItems = []
            self.UpdateItemVisuals()

    def UpdateItemVisuals(self):
        borderWidthSelected = self.mapToScene(QRect(0, 0, 8, 8)).boundingRect().width()
        borderWidthHovered = self.mapToScene(QRect(0, 0, 5, 5)).boundingRect().width()
        resizeHandleWidth = self.mapToScene(QRect(0, 0, 10, 10)).boundingRect().width()
        for item in self.allItems:
            selected = item in self.selectedItems
            hovered = item in self.hoveredItems
            item.borderVisible = selected or hovered
            item.resizeHandlesVisible = selected
            if selected:
                item.borderWidth = borderWidthSelected
            elif hovered:
                item.borderWidth = borderWidthHovered
            item.resizeHandlesWidth = resizeHandleWidth
            item.resizeHandlesColor = QColor(100, 100, 255)
            item.borderColor = QColor(100, 100, 255)
            item.UpdateGeometry()
