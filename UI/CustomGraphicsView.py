from typing import List, Tuple, Optional
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QGraphicsProxyWidget, \
    QGraphicsRectItem
from PySide6.QtGui import QPen, QColor, QPainter, QBrush, QWheelEvent, QTransform, QGuiApplication, \
    QPalette
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
        self.borderRectItem.setPen(QPen(self.borderColor, self.borderWidth, j=Qt.MiterJoin))
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

        self.setMouseTracking(True)

        self.viewOffset = QPointF(0, 0)
        self.zoom = 1

        self.gridSpacing = QSizeF(50, 50)
        self.gridThickness = 1
        self.gridZoomThreshold = 0.25
        self.showGrid = True

        self.scrollSensitivity = 1 / 1000

        self.state = CustomGraphicsViewState.IDLE

        self.mouseDeltaScenePosition = QPointF()
        self.mouseScenePosition = QPointF()
        self._lastMouseViewPosition = QPoint()
        self.itemUnderMouse: Optional[CustomGraphicsViewItem] = None
        self.resizeHandleIndexUnderMouse = -1

        self.selectionBoxRectItem = QGraphicsRectItem()
        self.selectionBoxRectItem.setBrush(Qt.NoBrush)
        self.selectionBoxRectScreenSize = 2
        self.selectionBoxRectColor = QColor(200, 200, 255)
        self.selectedItemBorderSize = 2
        self.selectedItemBorderColor = QColor(200, 200, 255)
        self.scene().addItem(self.selectionBoxRectItem)

        self._transformStartMousePos = QPointF()
        self._transformResizeHandleIndex = -1
        self._transformStartRects: List[QRectF] = []

        self.resizeHandleScreenSize = 5
        self.resizeHandleBorderScreenSize = 1
        self.resizeHandleColor = QColor(100, 100, 255)
        self.resizeHandleBorderColor = QColor(100, 100, 255)
        self.resizeHandles = [QGraphicsRectItem() for _ in range(8)]
        [self.scene().addItem(h) for h in self.resizeHandles]

        self.allItems: List[CustomGraphicsViewItem] = []
        self.selectedItems: List[CustomGraphicsViewItem] = []
        self.isInteractive = True

        self.UpdateViewMatrix()
        self.UpdateItemVisuals()

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
            if QGuiApplication.queryKeyboardModifiers() == Qt.ShiftModifier:
                if self.itemUnderMouse is not None:
                    if self.itemUnderMouse in self.selectedItems:
                        self.selectedItems.remove(self.itemUnderMouse)
                    else:
                        self.selectedItems.append(self.itemUnderMouse)
            else:
                if self.resizeHandleIndexUnderMouse >= 0:
                    self._transformResizeHandleIndex = self.resizeHandleIndexUnderMouse
                    self._transformStartRects = [x.graphicsProxy.sceneBoundingRect() for x in
                                                 self.selectedItems]
                    self._transformStartMousePos = self.mouseScenePosition
                    self.state = CustomGraphicsViewState.RESIZING
                elif self.itemUnderMouse is not None:
                    if self.itemUnderMouse not in self.selectedItems:
                        self.selectedItems = [self.itemUnderMouse]
                    self.state = CustomGraphicsViewState.MOVING
                    self._transformStartRects = [x.graphicsProxy.sceneBoundingRect() for x in
                                                 self.selectedItems]
                    self._transformStartMousePos = self.mouseScenePosition
                else:
                    self.selectedItems = []
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
            self.viewOffset -= self.mouseDeltaScenePosition
            self.UpdateViewMatrix()
        elif self.state == CustomGraphicsViewState.MOVING:
            self.DoMove()
        elif self.state == CustomGraphicsViewState.RESIZING:
            self.DoResize()
        else:
            self.UpdateItemVisuals()
        self.UpdateCursor()
        super().mouseMoveEvent(event)

    def DoMove(self):
        def Snap(x, div):
            return round(float(x) / div) * div

        def SnapPoint(p: QPointF):
            return QPointF(Snap(p.x(), self.gridSpacing.width()),
                           Snap(p.y(), self.gridSpacing.height()))

        moveDelta = self.mouseScenePosition - self._transformStartMousePos
        for startRect, item in zip(self._transformStartRects, self.selectedItems):
            newRect = startRect.translated(moveDelta)
            snapOffsets = (SnapPoint(newRect.topLeft()) - newRect.topLeft(),
                           SnapPoint(newRect.topRight()) - newRect.topRight(),
                           SnapPoint(newRect.bottomLeft()) - newRect.bottomLeft(),
                           SnapPoint(newRect.bottomRight()) - newRect.bottomRight())
            magnitudes = [d.x() ** 2 + d.y() ** 2 for d in snapOffsets]
            minOffset = min(zip(magnitudes, snapOffsets), key=lambda x: x[0])[1]
            item.graphicsProxy.setPos(newRect.topLeft() + minOffset)
        self.UpdateItemVisuals()

    def DoResize(self):
        def Snap(x, div):
            return round(float(x) / div) * div

        def SnapPoint(p: QPointF):
            return QPointF(Snap(p.x(), self.gridSpacing.width()),
                           Snap(p.y(), self.gridSpacing.height()))

        resizeDelta = self.mouseScenePosition - self._transformStartMousePos
        initialRect = self._transformStartRects[0]
        for r in self._transformStartRects:
            initialRect = initialRect.united(r)
        newRect = QRectF(initialRect)
        if self._transformResizeHandleIndex == 0:
            newRect.setTopLeft(SnapPoint(newRect.topLeft() + resizeDelta))
        elif self._transformResizeHandleIndex == 2:
            newRect.setTopRight(SnapPoint(newRect.topRight() + resizeDelta))
        elif self._transformResizeHandleIndex == 5:
            newRect.setBottomLeft(SnapPoint(newRect.bottomLeft() + resizeDelta))
        elif self._transformResizeHandleIndex == 7:
            newRect.setBottomRight(SnapPoint(newRect.bottomRight() + resizeDelta))
        elif self._transformResizeHandleIndex == 1:
            newRect.setTop(Snap(newRect.top() + resizeDelta.y(), self.gridSpacing.height()))
        elif self._transformResizeHandleIndex == 6:
            newRect.setBottom(Snap(newRect.bottom() + resizeDelta.y(), self.gridSpacing.height()))
        elif self._transformResizeHandleIndex == 3:
            newRect.setLeft(Snap(newRect.left() + resizeDelta.x(), self.gridSpacing.width()))
        elif self._transformResizeHandleIndex == 4:
            newRect.setRight(Snap(newRect.right() + resizeDelta.x(), self.gridSpacing.width()))
        newRect = newRect.normalized()

        def Transform(p: QPointF):
            return QPointF(
                ((p.x() - initialRect.x()) / initialRect.width()) * newRect.width() + newRect.x(),
                ((p.y() - initialRect.y()) / initialRect.height()) * newRect.height() + newRect.y())

        for (r, i) in zip(self._transformStartRects, self.selectedItems):
            i.SetRect(QRectF(Transform(r.topLeft()), Transform(r.bottomRight())))
        self.UpdateItemVisuals()

    def DrawDebugRect(self, rect, id: int, color: QColor):
        try:
            self._drawnRects
        except:
            self._drawnRects = {}
        if id not in self._drawnRects:
            self._drawnRects[id] = QGraphicsRectItem()
            self._drawnRects[id].setPen(QPen(color, 1))
            self.scene().addItem(self._drawnRects[id])
        self._drawnRects[id].setRect(rect)

    def UpdateMouseInfo(self, mousePosition: QPoint):
        self.mouseScenePosition = self.mapToScene(mousePosition)
        self.mouseDeltaScenePosition = self.mouseScenePosition - self.mapToScene(
            self._lastMouseViewPosition)
        self._lastMouseViewPosition = mousePosition

        self.itemUnderMouse = None
        for item in sorted(self.allItems, key=lambda x: x.graphicsProxy.zValue()):
            if item.borderRectItem.contains(self.mouseScenePosition):
                self.itemUnderMouse = item
                break

        self.resizeHandleIndexUnderMouse = -1
        for i, handle in enumerate(self.resizeHandles):
            if handle.contains(self.mouseScenePosition):
                self.resizeHandleIndexUnderMouse = i
                break

    def UpdateCursor(self):
        if self.state == CustomGraphicsViewState.PANNING:
            self.SetCursorHelper(Qt.ClosedHandCursor)
        elif self.state == CustomGraphicsViewState.MOVING:
            self.SetCursorHelper(Qt.SizeAllCursor)
        elif self.state == CustomGraphicsViewState.RESIZING:
            if self._transformResizeHandleIndex == 0 or self._transformResizeHandleIndex == 7:
                self.SetCursorHelper(Qt.SizeFDiagCursor)
            if self._transformResizeHandleIndex == 1 or self._transformResizeHandleIndex == 6:
                self.SetCursorHelper(Qt.SizeVerCursor)
            if self._transformResizeHandleIndex == 2 or self._transformResizeHandleIndex == 5:
                self.SetCursorHelper(Qt.SizeBDiagCursor)
            if self._transformResizeHandleIndex == 3 or self._transformResizeHandleIndex == 4:
                self.SetCursorHelper(Qt.SizeHorCursor)
        elif self.state == CustomGraphicsViewState.IDLE:
            if self.resizeHandleIndexUnderMouse >= 0:
                if self.resizeHandleIndexUnderMouse == 0 or self.resizeHandleIndexUnderMouse == 7:
                    self.SetCursorHelper(Qt.SizeFDiagCursor)
                if self.resizeHandleIndexUnderMouse == 1 or self.resizeHandleIndexUnderMouse == 6:
                    self.SetCursorHelper(Qt.SizeVerCursor)
                if self.resizeHandleIndexUnderMouse == 2 or self.resizeHandleIndexUnderMouse == 5:
                    self.SetCursorHelper(Qt.SizeBDiagCursor)
                if self.resizeHandleIndexUnderMouse == 3 or self.resizeHandleIndexUnderMouse == 4:
                    self.SetCursorHelper(Qt.SizeHorCursor)
            elif self.itemUnderMouse in self.selectedItems:
                self.SetCursorHelper(Qt.SizeAllCursor)
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
        if self.backgroundBrush().color() != self.palette().color(QPalette.Midlight):
            self.setBackgroundBrush(self.palette().color(QPalette.Midlight))
        super().drawBackground(painter, rect)

        if self.zoom <= self.gridZoomThreshold or not self.showGrid:
            return

        painter.setPen(QPen(self.palette().color(QPalette.Dark), self.gridThickness))

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
        z = self.GetMaxItemZValue()
        item.borderRectItem.setZValue(z + 1)
        item.graphicsProxy.setZValue(z + 1)

    def GetMaxItemZValue(self):
        return max([x.graphicsProxy.zValue() for x in self.allItems]) if len(
            self.allItems) > 0 else 0

    def SetInteractive(self, interactive: bool):
        self.isInteractive = interactive
        if not interactive:
            self.selectedItems = []
            self.UpdateItemVisuals()

    def UpdateItemVisuals(self):
        borderWidthSelected = self.mapToScene(
            QRect(0, 0, self.selectedItemBorderSize, 1)).boundingRect().width()
        selectionRect = None
        for item in self.allItems:
            selected = item in self.selectedItems
            item.borderVisible = selected
            item.resizeHandlesVisible = selected
            if selected:
                item.borderWidth = borderWidthSelected
                if selectionRect is None:
                    selectionRect = item.graphicsProxy.sceneBoundingRect()
                else:
                    selectionRect = selectionRect.united(item.graphicsProxy.sceneBoundingRect())
            item.borderColor = self.selectedItemBorderColor
            item.UpdateGeometry()

        if selectionRect is not None:
            maxZValue = self.GetMaxItemZValue()

            selectionRect = selectionRect.marginsAdded(
                QMarginsF(borderWidthSelected, borderWidthSelected, borderWidthSelected,
                          borderWidthSelected))
            self.selectionBoxRectItem.setVisible(True)
            self.selectionBoxRectItem.setRect(selectionRect)
            self.selectionBoxRectItem.setZValue(maxZValue + 1)
            self.selectionBoxRectItem.setPen(
                QPen(self.selectionBoxRectColor,
                     self.mapToScene(
                         QRect(0, 0, self.selectionBoxRectScreenSize, 1)).boundingRect().width(),
                     j=Qt.MiterJoin))

            handlePositions = (
                selectionRect.topLeft(), QPointF(selectionRect.center().x(), selectionRect.top()),
                selectionRect.topRight(), QPointF(selectionRect.left(), selectionRect.center().y()),
                QPointF(selectionRect.right(), selectionRect.center().y()),
                selectionRect.bottomLeft(),
                QPointF(selectionRect.center().x(), selectionRect.bottom()),
                selectionRect.bottomRight())
            handleSize = self.mapToScene(
                QRect(0, 0, self.resizeHandleScreenSize,
                      self.resizeHandleScreenSize)).boundingRect().size()
            for pos, h in zip(handlePositions, self.resizeHandles):
                h.setVisible(True)
                h.setPen(QPen(self.resizeHandleBorderColor,
                              self.mapToScene(QRect(0, 0, self.resizeHandleBorderScreenSize,
                                                    1)).boundingRect().width(),
                              j=Qt.MiterJoin))
                h.setBrush(QBrush(self.resizeHandleColor))
                h.setZValue(maxZValue + 2)
                r = QRectF(QPointF(), handleSize)
                r.moveCenter(pos)
                h.setRect(r)
        else:
            self.selectionBoxRectItem.setVisible(False)
            [h.setVisible(False) for h in self.resizeHandles]
