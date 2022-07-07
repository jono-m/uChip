from typing import List, Tuple, Optional
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QGraphicsProxyWidget, \
    QGraphicsRectItem, QVBoxLayout, QLabel, QFrame
from PySide6.QtGui import QPen, QColor, QPainter, QBrush, QWheelEvent, QTransform, QGuiApplication, \
    QPalette, QKeyEvent
from PySide6.QtCore import Qt, QPointF, QSizeF, QRectF, QLineF, QRect, QMarginsF, QPoint
from enum import Enum, auto


class CustomGraphicsViewState(Enum):
    IDLE = auto()
    PANNING = auto()
    MOVING = auto()
    RESIZING = auto()
    BAND_SELECTING = auto()


class CustomGraphicsViewItem:
    def __init__(self, name: str = ""):
        self.graphicsProxy = QGraphicsProxyWidget()
        self.borderRectItem = QGraphicsRectItem()
        self.borderWidth = 5
        self.borderVisible = True
        self.borderColor = QColor(255, 255, 255)
        self.inspectorWidget = QWidget()
        self.inspectorWidget.setLayout(QVBoxLayout())
        self.nameLabel = QLabel("<b><u>" + name + "</u></b>")
        self.inspectorWidget.layout().addWidget(self.nameLabel)
        self._oldWidget = None

    def UpdateGeometry(self):
        self.borderRectItem.setPen(QPen(self.borderColor, self.borderWidth, j=Qt.MiterJoin))
        self.borderRectItem.setRect(
            QRectF(self.graphicsProxy.scenePos(), self.graphicsProxy.size()))
        self.borderRectItem.setVisible(self.borderVisible)

    def SetWidget(self, w: QWidget):
        self.graphicsProxy.setWidget(w)
        self.UpdateGeometry()

    def SetInspector(self, w: QWidget):
        if self._oldWidget is not None:
            self.inspectorWidget.layout().removeWidget(self._oldWidget)
        self.inspectorWidget.layout().addWidget(w)
        self._oldWidget = w

    def SetRect(self, rect: QRectF):
        self.graphicsProxy.setPos(rect.topLeft())
        self.graphicsProxy.resize(rect.size())
        self.UpdateGeometry()

    def SetPosition(self, point: QPointF):
        self.graphicsProxy.setPos(point)

    def Remove(self) -> bool:
        return True

    def Duplicate(self):
        return CustomGraphicsViewItem()


class CustomGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Set up view
        self.setScene(QGraphicsScene())
        self.setMouseTracking(True)
        self.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing |
            QPainter.VerticalSubpixelPositioning)

        # State
        self.viewOffset = QPointF(0, 0)
        self.zoom = 1
        self.state = CustomGraphicsViewState.IDLE
        self.allItems: List[CustomGraphicsViewItem] = []
        self.selectedItems: List[CustomGraphicsViewItem] = []
        self.isInteractive = True

        # Grid settings
        self.gridSpacing = QSizeF(50, 50)
        self.gridThickness = 1
        self.gridZoomThreshold = 0.25
        self.showGrid = True

        # Mouse control and state
        self.scrollSensitivity = 1 / 1000
        self.mouseDeltaScenePosition = QPointF()
        self.mouseScenePosition = QPointF()
        self._lastMouseViewPosition = QPoint()
        self.itemUnderMouse: Optional[CustomGraphicsViewItem] = None
        self.resizeHandleIndexUnderMouse = -1

        # Selection box and transformation handles
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

        # Inspector
        self.inspectorPanel = QFrame(self)
        self.inspectorPanel.setFixedWidth(200)
        self.inspectorPanel.setMinimumHeight(300)
        self.inspectorPanel.setFrameShape(QFrame.Box)
        self.inspectorPanel.setAutoFillBackground(True)
        inspectorLayout = QVBoxLayout()
        inspectorLayout.setAlignment(Qt.AlignTop)
        self.inspectorPanel.setLayout(inspectorLayout)
        label = QLabel("<b>Inspector</b>")
        label.setAlignment(Qt.AlignCenter)
        inspectorLayout.addWidget(label)
        inspectorLayout.addWidget(BorderSpacer(False))
        self.noneSelectedLabel = QLabel("No objects selected.")
        inspectorLayout.addWidget(self.noneSelectedLabel)
        self.inspectorLayout = QVBoxLayout()
        inspectorLayout.addLayout(self.inspectorLayout)

        # Initialization
        self.UpdateViewMatrix()
        self.UpdateItemVisuals()

    def Clear(self):
        for i in self.allItems:
            self.scene().removeItem(i.borderRectItem)
            self.scene().removeItem(i.graphicsProxy)
        self.selectedItems = []
        self.UpdateInspector()
        self.UpdateItemVisuals()

    def UpdateViewMatrix(self):
        transform = QTransform()
        transform.scale(self.zoom, self.zoom)
        self.setTransform(transform)
        self.setSceneRect(QRectF(self.viewOffset, QSizeF()))

    def UpdateZoom(self, scenePositionAnchor: QPointF, newZoom: float):
        anchorScreenSpace = self.mapFromScene(scenePositionAnchor)
        self.zoom = min(max(newZoom, 0.05), 1)
        self.UpdateViewMatrix()
        newAnchorPosition = self.mapToScene(anchorScreenSpace)
        self.viewOffset -= newAnchorPosition - scenePositionAnchor
        self.UpdateViewMatrix()
        self.UpdateItemVisuals()

    def UpdateInspector(self):
        self.inspectorPanel.setVisible(self.isInteractive)
        self.noneSelectedLabel.setVisible(len(self.selectedItems) == 0)
        for i in range(self.inspectorLayout.count()):
            w = self.inspectorLayout.takeAt(0)
            if w.widget():
                w.widget().setVisible(False)
        for i in self.selectedItems:
            if i.inspectorWidget is not None:
                self.inspectorLayout.addWidget(i.inspectorWidget)
                i.inspectorWidget.setVisible(True)
        self.inspectorPanel.adjustSize()
        size = QPoint(self.inspectorPanel.rect().width(), self.inspectorPanel.rect().height())
        padding = 20
        self.inspectorPanel.move(self.rect().bottomRight() - size - QPoint(padding, padding))

    def UpdateMouseInfo(self, mousePosition: QPoint):
        self.mouseScenePosition = self.mapToScene(mousePosition)
        self.mouseDeltaScenePosition = self.mouseScenePosition - self.mapToScene(
            self._lastMouseViewPosition)
        self._lastMouseViewPosition = mousePosition

        self.itemUnderMouse = None
        for item in sorted(self.allItems, key=lambda x: x.graphicsProxy.zValue(), reverse=True):
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
            item.SetRect(newRect.translated(minOffset))
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

    def AddItem(self, item: CustomGraphicsViewItem, center=False, select=False):
        self.allItems.append(item)
        self.scene().addItem(item.borderRectItem)
        self.scene().addItem(item.graphicsProxy)
        z = self.GetMaxItemZValue()
        item.borderRectItem.setZValue(z + 1)
        item.graphicsProxy.setZValue(z + 1)
        if center:
            r = item.graphicsProxy.sceneBoundingRect()
            r.moveCenter(self.viewOffset)
            item.SetRect(r)
        if select:
            self.SelectItems([item])
        self.UpdateItemVisuals()

    def RemoveItem(self, item: CustomGraphicsViewItem):
        self.allItems.remove(item)
        self.scene().removeItem(item.borderRectItem)
        self.scene().removeItem(item.graphicsProxy)
        self.SelectItems([i for i in self.selectedItems if i != item])
        self.UpdateInspector()
        self.UpdateItemVisuals()

    def GetMaxItemZValue(self):
        return max([x.graphicsProxy.zValue() for x in self.allItems]) if len(
            self.allItems) > 0 else 0

    def SetInteractive(self, interactive: bool):
        self.isInteractive = interactive
        self.showGrid = interactive
        if not interactive:
            self.SelectItems([])
        self.UpdateInspector()
        self.setFocus()
        self.scene().update()

    def SelectItems(self, items: List[CustomGraphicsViewItem]):
        self.selectedItems = items
        self.UpdateInspector()
        self.UpdateItemVisuals()

    def IsInteractive(self):
        return self.isInteractive

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

    # Events
    def wheelEvent(self, event: QWheelEvent):
        self.UpdateMouseInfo(event.position().toPoint())
        self.UpdateZoom(self.mouseScenePosition,
                        self.zoom + float(event.angleDelta().y()) * self.scrollSensitivity)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.UpdateInspector()

    def keyPressEvent(self, event: QKeyEvent):
        if self.isInteractive:
            if event.key() == Qt.Key_Delete:
                for item in self.selectedItems.copy():
                    if item.Remove():
                        self.RemoveItem(item)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.UpdateMouseInfo(event.pos())
        if self.state != CustomGraphicsViewState.IDLE:
            return
        if event.button() == Qt.LeftButton and self.isInteractive:
            if QGuiApplication.queryKeyboardModifiers() == Qt.ShiftModifier:
                if self.itemUnderMouse is not None:
                    if self.itemUnderMouse in self.selectedItems:
                        self.SelectItems(
                            [i for i in self.selectedItems if i != self.itemUnderMouse])
                    else:
                        self.SelectItems(self.selectedItems + [self.itemUnderMouse])
            else:
                if self.resizeHandleIndexUnderMouse >= 0:
                    self._transformResizeHandleIndex = self.resizeHandleIndexUnderMouse
                    self._transformStartRects = [x.graphicsProxy.sceneBoundingRect() for x in
                                                 self.selectedItems]
                    self._transformStartMousePos = self.mouseScenePosition
                    self.state = CustomGraphicsViewState.RESIZING
                elif self.itemUnderMouse is not None:
                    if self.itemUnderMouse not in self.selectedItems:
                        self.SelectItems([self.itemUnderMouse])
                    self.state = CustomGraphicsViewState.MOVING
                    self._transformStartRects = [x.graphicsProxy.sceneBoundingRect() for x in
                                                 self.selectedItems]
                    self._transformStartMousePos = self.mouseScenePosition
                else:
                    self.SelectItems([])
        elif event.button() == Qt.RightButton:
            self.state = CustomGraphicsViewState.PANNING

        self.UpdateCursor()
        if not self.isInteractive:
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
        if not self.isInteractive:
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
        elif self.state == CustomGraphicsViewState.BAND_SELECTING:
            pass
        self.UpdateCursor()
        if not self.isInteractive:
            super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if not self.isInteractive:
            super().mouseDoubleClickEvent(event)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        if self.backgroundBrush().color() != self.palette().color(QPalette.Light):
            self.setBackgroundBrush(self.palette().color(QPalette.Light))
        super().drawBackground(painter, rect)

        if self.zoom <= self.gridZoomThreshold or not self.showGrid:
            return

        painter.setPen(QPen(self.palette().color(QPalette.Midlight), self.gridThickness))

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


class BorderSpacer(QLabel):
    def __init__(self, vertical):
        super().__init__()
        self.setStyleSheet("""background-color: #999999""")
        if vertical:
            self.setFixedWidth(1)
        else:
            self.setFixedHeight(1)
