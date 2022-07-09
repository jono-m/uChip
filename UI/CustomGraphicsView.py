from typing import List, Tuple, Optional
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QGraphicsProxyWidget, \
    QGraphicsRectItem, QVBoxLayout, QLabel, QFrame, QScrollArea
from PySide6.QtGui import QPen, QColor, QPainter, QBrush, QWheelEvent, QTransform, QGuiApplication, \
    QPalette, QKeyEvent
from PySide6.QtCore import Qt, QPointF, QSizeF, QRectF, QLineF, QRect, QMarginsF, QPoint
from UI.UIMaster import UIMaster
from enum import Enum, auto
from functools import reduce


class CustomGraphicsViewState(Enum):
    IDLE = auto()
    PANNING = auto()
    MOVING = auto()
    RESIZING = auto()
    BAND_SELECTING = auto()


class CustomGraphicsViewItem:
    def __init__(self, name: str = ""):
        self.itemProxy = QGraphicsProxyWidget()
        self.borderRectItem = QGraphicsRectItem()
        self.borderWidth = 5
        self.borderVisible = False
        self.borderColor = QColor(255, 255, 255)
        self.inspectorProxy = QGraphicsProxyWidget()
        inspectorWidget = QWidget()
        inspectorWidget.setLayout(QVBoxLayout())
        self.nameLabel = QLabel("<b><u>" + name + "</u></b>")
        inspectorWidget.layout().addWidget(self.nameLabel)
        self._rect = QRectF()
        self.customInspector: Optional[QWidget] = None
        self.inspectorProxy.setWidget(inspectorWidget)

    def UpdateGeometry(self):
        self.itemProxy.setPos(self._rect.topLeft())
        self.itemProxy.resize(self._rect.size())
        self._rect = self.itemProxy.sceneBoundingRect()
        self.borderRectItem.setPen(QPen(self.borderColor, self.borderWidth, j=Qt.MiterJoin))
        self.borderRectItem.setRect(self._rect)
        self.borderRectItem.setVisible(self.borderVisible)
        self.inspectorProxy.adjustSize()
        self.inspectorProxy.setPos(
            self._rect.topLeft() - QPointF(0, self.inspectorProxy.sceneBoundingRect().height()))

    def GetRect(self):
        return self._rect

    def SetWidget(self, w: QWidget):
        self.itemProxy.setWidget(w)
        self.UpdateGeometry()

    def SetInspector(self, w: QWidget):
        if self.customInspector is not None:
            self.inspectorProxy.widget().layout().removeWidget(self.customInspector)
        self.inspectorProxy.widget().layout().addWidget(w)
        w.setHidden(False)
        self.customInspector = w

    def SetRect(self, rect: QRectF):
        self._rect = rect
        self.UpdateGeometry()

    def OnRemoved(self):
        pass

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
        self.inspectorItemUnderMouse = None

        # Selection box and transformation handles
        self.selectionBoxRectItem = QGraphicsRectItem()
        self.selectionBoxRectItem.setBrush(Qt.NoBrush)
        self.selectionBoxRectScreenSize = 2
        self.selectionBoxRectColor = QColor(200, 200, 255)
        self.selectedItemBorderSize = 4
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

        # Rubber band selection
        self.rubberBandRectItem = QGraphicsRectItem()
        self.rubberBandRectItem.setBrush(Qt.NoBrush)
        self.rubberBandRectScreenSize = 2
        self.rubberBandRectColor = QColor(200, 200, 255)
        self.rubberBandAnchor = QPointF()
        self.scene().addItem(self.rubberBandRectItem)
        self.rubberBandRectItem.setVisible(False)

        # Initialization
        self.UpdateViewMatrix()
        self.UpdateSelectionDisplay()
        self.UpdateSelectionBox()
        self.UpdateInspectors()
        self.UpdateCursor()

    def Clear(self):
        self.DeleteItems(self.allItems.copy())

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
        self.UpdateSelectionDisplay()

    def UpdateMouseInfo(self, mousePosition: QPoint):
        self.mouseScenePosition = self.mapToScene(mousePosition)
        self.mouseDeltaScenePosition = self.mouseScenePosition - self.mapToScene(
            self._lastMouseViewPosition)
        self._lastMouseViewPosition = mousePosition

        self.itemUnderMouse = None
        self.inspectorItemUnderMouse = None
        for item in sorted(self.allItems, key=lambda x: x.itemProxy.zValue(), reverse=True):
            if item.inspectorProxy.isVisible() and item.inspectorProxy.sceneBoundingRect().contains(
                    self.mouseScenePosition):
                self.inspectorItemUnderMouse = item
                break
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
            UIMaster.SetCursor(Qt.ClosedHandCursor)
        elif self.state == CustomGraphicsViewState.MOVING:
            UIMaster.SetCursor(Qt.SizeAllCursor)
        elif self.state == CustomGraphicsViewState.RESIZING:
            if self._transformResizeHandleIndex == 0 or self._transformResizeHandleIndex == 7:
                UIMaster.SetCursor(Qt.SizeFDiagCursor)
            if self._transformResizeHandleIndex == 1 or self._transformResizeHandleIndex == 6:
                UIMaster.SetCursor(Qt.SizeVerCursor)
            if self._transformResizeHandleIndex == 2 or self._transformResizeHandleIndex == 5:
                UIMaster.SetCursor(Qt.SizeBDiagCursor)
            if self._transformResizeHandleIndex == 3 or self._transformResizeHandleIndex == 4:
                UIMaster.SetCursor(Qt.SizeHorCursor)
        elif self.state == CustomGraphicsViewState.IDLE:
            if self.resizeHandleIndexUnderMouse >= 0:
                if self.resizeHandleIndexUnderMouse == 0 or self.resizeHandleIndexUnderMouse == 7:
                    UIMaster.SetCursor(Qt.SizeFDiagCursor)
                if self.resizeHandleIndexUnderMouse == 1 or self.resizeHandleIndexUnderMouse == 6:
                    UIMaster.SetCursor(Qt.SizeVerCursor)
                if self.resizeHandleIndexUnderMouse == 2 or self.resizeHandleIndexUnderMouse == 5:
                    UIMaster.SetCursor(Qt.SizeBDiagCursor)
                if self.resizeHandleIndexUnderMouse == 3 or self.resizeHandleIndexUnderMouse == 4:
                    UIMaster.SetCursor(Qt.SizeHorCursor)
            elif self.itemUnderMouse in self.selectedItems:
                UIMaster.SetCursor(Qt.SizeAllCursor)
            else:
                UIMaster.SetCursor(None)
        else:
            UIMaster.SetCursor(None)

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
        self.UpdateSelectionBox()

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

        self.UpdateSelectionBox()

    def AddItems(self, items: List[CustomGraphicsViewItem]):
        self.allItems += items
        z = self.GetMaxItemZValue()
        for i in items:
            self.scene().addItem(i.borderRectItem)
            self.scene().addItem(i.inspectorProxy)
            self.scene().addItem(i.itemProxy)
            i.itemProxy.setZValue(z + 1)
            i.borderRectItem.setZValue(z + 2)
            z += 2

    def CenterItem(self, item: CustomGraphicsViewItem):
        r = item.itemProxy.sceneBoundingRect()
        r.moveCenter(self.viewOffset)
        item.SetRect(r)

    def DeleteItems(self, items: List[CustomGraphicsViewItem]):
        for i in items:
            self.allItems.remove(i)
            self.scene().removeItem(i.borderRectItem)
            self.scene().removeItem(i.itemProxy)
            self.scene().removeItem(i.inspectorProxy)
            i.OnRemoved()
        self.SelectItems([i for i in self.selectedItems if i not in items])

    def GetMaxItemZValue(self):
        return max([x.inspectorProxy.zValue() for x in self.allItems]) if len(
            self.allItems) > 0 else 0

    def SetInteractive(self, interactive: bool):
        self.isInteractive = interactive
        self.showGrid = interactive
        self.SelectItems([])
        self.scene().update()

    def SelectItems(self, items: List[CustomGraphicsViewItem]):
        self.selectedItems = items
        self.UpdateInspectors()
        self.UpdateSelectionDisplay()

    def IsInteractive(self):
        return self.isInteractive

    def GetPixelSceneSize(self, size):
        return self.mapToScene(QRect(0, 0, size, 1)).boundingRect().width()

    def UpdateSelectionDisplay(self):
        selectedItemBorderSceneSize = self.GetPixelSceneSize(self.selectedItemBorderSize)
        for item in self.allItems:
            isSelected = item in self.selectedItems
            item.borderVisible = isSelected
            item.resizeHandlesVisible = isSelected
            item.borderWidth = selectedItemBorderSceneSize
            item.borderColor = self.selectedItemBorderColor
            if item.customInspector is not None:
                item.inspectorProxy.setScale(1 / self.zoom)
            item.UpdateGeometry()
        self.UpdateSelectionBox()

    def UpdateInspectors(self):
        maxZValue = self.GetMaxItemZValue()
        for i in self.allItems:
            if i not in self.selectedItems or not self.isInteractive or \
                    self.state != CustomGraphicsViewState.IDLE or i.customInspector is None:
                i.inspectorProxy.setVisible(False)
            else:
                i.inspectorProxy.setVisible(True)
                i.inspectorProxy.setZValue(maxZValue + 1)

    def UpdateSelectionBox(self):
        selectionRect = None if len(self.selectedItems) == 0 else \
            reduce(QRectF.united, [item.GetRect() for item in self.selectedItems])
        selectedItemBorderSceneSize = self.GetPixelSceneSize(self.selectedItemBorderSize)
        if selectionRect is not None:
            maxZValue = self.GetMaxItemZValue()

            selectionRect = selectionRect.marginsAdded(QMarginsF(selectedItemBorderSceneSize,
                                                                 selectedItemBorderSceneSize,
                                                                 selectedItemBorderSceneSize,
                                                                 selectedItemBorderSceneSize))
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
            handleSize = self.GetPixelSceneSize(self.resizeHandleScreenSize)
            for pos, h in zip(handlePositions, self.resizeHandles):
                h.setVisible(True)
                h.setPen(QPen(self.resizeHandleBorderColor,
                              self.GetPixelSceneSize(self.resizeHandleBorderScreenSize),
                              j=Qt.MiterJoin))
                h.setBrush(QBrush(self.resizeHandleColor))
                h.setZValue(maxZValue + 2)
                r = QRectF(QPointF(), QSizeF(handleSize, handleSize))
                r.moveCenter(pos)
                h.setRect(r)
        else:
            self.selectionBoxRectItem.setVisible(False)
            [h.setVisible(False) for h in self.resizeHandles]

        rubberBandWidth = self.GetPixelSceneSize(self.rubberBandRectScreenSize)
        self.rubberBandRectItem.setZValue(self.GetMaxItemZValue() + 2)
        self.rubberBandRectItem.setPen(QPen(self.rubberBandRectColor, rubberBandWidth))

    def DoMultiSelection(self):
        itemsInRect = [x for x in self.allItems if x.itemProxy.sceneBoundingRect().intersects(
            self.rubberBandRectItem.sceneBoundingRect()) or x.borderRectItem.contains(
            self.mouseScenePosition)]
        if self.IsMultiSelect():
            self.SelectItems(
                [x for x in self.selectedItems if x not in itemsInRect] +
                [x for x in itemsInRect if x not in self.selectedItems])
        else:
            self.SelectItems(itemsInRect)

    def IsMultiSelect(self):
        return QGuiApplication.queryKeyboardModifiers() == Qt.ShiftModifier

    def Duplicate(self):
        duplicates = []
        for i in self.selectedItems:
            d = i.Duplicate()
            d.SetRect(
                i.GetRect().translated(
                    QPointF(self.gridSpacing.width(), self.gridSpacing.height())))
            duplicates.append(d)
        self.AddItems(duplicates)
        self.SelectItems(duplicates)

    # Events
    def wheelEvent(self, event: QWheelEvent):
        self.UpdateMouseInfo(event.position().toPoint())
        self.UpdateZoom(self.mouseScenePosition,
                        self.zoom + float(event.angleDelta().y()) * self.scrollSensitivity)

    def keyPressEvent(self, event: QKeyEvent):
        if self.isInteractive and self.inspectorItemUnderMouse is None:
            if event.key() == Qt.Key_Delete:
                self.DeleteItems(self.selectedItems)
            elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_D:
                self.Duplicate()
            elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_A:
                self.SelectItems(self.allItems)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.UpdateMouseInfo(event.pos())
        if self.state != CustomGraphicsViewState.IDLE:
            return
        if event.button() == Qt.LeftButton and self.isInteractive and \
                self.inspectorItemUnderMouse is None:
            self.rubberBandAnchor = self.mouseScenePosition
            self.rubberBandRectItem.setRect(QRectF(self.mouseScenePosition, QSizeF()))
            if self.resizeHandleIndexUnderMouse >= 0:
                self._transformResizeHandleIndex = self.resizeHandleIndexUnderMouse
                self._transformStartRects = [x.itemProxy.sceneBoundingRect() for x in
                                             self.selectedItems]
                self._transformStartMousePos = self.mouseScenePosition
                self.state = CustomGraphicsViewState.RESIZING
            elif self.itemUnderMouse is not None:
                if self.IsMultiSelect():
                    self.DoMultiSelection()
                else:
                    if self.itemUnderMouse not in self.selectedItems:
                        self.SelectItems([self.itemUnderMouse])
                    self.state = CustomGraphicsViewState.MOVING
                    self._transformStartRects = [x.itemProxy.sceneBoundingRect() for x in
                                                 self.selectedItems]
                    self._transformStartMousePos = self.mouseScenePosition
            else:
                self.state = CustomGraphicsViewState.BAND_SELECTING
                self.rubberBandRectItem.setVisible(True)
        elif event.button() == Qt.RightButton:
            self.state = CustomGraphicsViewState.PANNING

        self.UpdateCursor()
        if not self.isInteractive or self.inspectorItemUnderMouse is not None:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.UpdateMouseInfo(event.pos())

        if self.state == CustomGraphicsViewState.PANNING and event.button() == Qt.RightButton:
            self.state = CustomGraphicsViewState.IDLE
        elif self.state == CustomGraphicsViewState.MOVING and event.button() == Qt.LeftButton:
            self.state = CustomGraphicsViewState.IDLE
        elif self.state == CustomGraphicsViewState.RESIZING and event.button() == Qt.LeftButton:
            self.state = CustomGraphicsViewState.IDLE
        elif self.state == CustomGraphicsViewState.BAND_SELECTING and \
                event.button() == Qt.LeftButton:
            self.state = CustomGraphicsViewState.IDLE
            self.rubberBandRectItem.setVisible(False)
            self.DoMultiSelection()
        self.UpdateCursor()
        if not self.isInteractive or self.inspectorItemUnderMouse is not None:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        self.UpdateMouseInfo(event.pos())
        if self.state == CustomGraphicsViewState.PANNING:
            self.viewOffset -= self.mouseDeltaScenePosition
            self.UpdateViewMatrix()
        elif self.state == CustomGraphicsViewState.MOVING:
            self.DoMove()
            self.scene().update()
        elif self.state == CustomGraphicsViewState.RESIZING:
            self.DoResize()
            self.scene().update()
        elif self.state == CustomGraphicsViewState.BAND_SELECTING:
            self.rubberBandRectItem.setRect(
                QRectF(self.rubberBandAnchor, self.mouseScenePosition).normalized())
            self.scene().update()
        self.UpdateCursor()
        if not self.isInteractive or \
                (self.inspectorItemUnderMouse is not None and
                 self.state == CustomGraphicsViewState.IDLE):
            super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if not self.isInteractive or self.inspectorItemUnderMouse is not None:
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
