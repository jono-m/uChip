from typing import Set, List

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QApplication
from PySide6.QtGui import QPainter, QBrush, QColor, QTransform, QWheelEvent, QMouseEvent, QPen, \
    QKeyEvent, \
    QGuiApplication
from PySide6.QtCore import QPointF, Qt, QRectF, QSizeF, QLine, Signal

from enum import Enum, auto
from PySide6.QtWidgets import QGraphicsObject, QFrame
from PySide6.QtCore import QPointF, Signal, QObject
from abc import abstractmethod
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton, QMenu, QHBoxLayout, QFrame
from PySide6.QtCore import Signal, QEvent
from UI.ChipEditor.ChipSceneViewer import ChipSceneViewer
from UI.ChipEditor.Inspector import Inspector


class ChipView(QFrame):
    def __init__(self):
        super().__init__()
        self.viewer = ChipSceneViewer()
        self.setContentsMargins(0, 0, 0, 0)

        actionsLayout = QHBoxLayout()
        actionsLayout.setContentsMargins(0, 0, 0, 0)
        actionsLayout.setSpacing(0)
        self._actionsWidget = FloatingWidget(self)
        self._actionsWidget.onResize.connect(self.FloatWidgets)
        self._actionsWidget.setLayout(actionsLayout)

        self._lockButton = ActionButtonFrame("Assets/Images/checkIcon.png")
        self._lockButton.button.clicked.connect(lambda: self.SetEditing(False))
        self._editButton = ActionButtonFrame("Assets/Images/Edit.png")
        self._editButton.button.clicked.connect(lambda: self.SetEditing(True))

        self._plusButton = ActionButtonFrame("Assets/Images/plusIcon.png")
        self._plusButton.button.setPopupMode(QToolButton.InstantPopup)

        actionsLayout.addWidget(self._plusButton)
        actionsLayout.addWidget(self._lockButton)
        actionsLayout.addWidget(self._editButton)

        self._inspector = Inspector(self)
        self.viewer.selectionChanged.connect(self._inspector.SetSelection)
        inspectorLayout = QHBoxLayout()
        inspectorLayout.setContentsMargins(0, 0, 0, 0)
        inspectorLayout.setSpacing(0)
        inspectorLayout.addWidget(self._inspector)
        self._inspectorWidget = FloatingWidget(self)
        self._inspectorWidget.onResize.connect(self.FloatWidgets)
        self._inspectorWidget.setLayout(inspectorLayout)

        menu = QMenu(self._plusButton)
        menu.addAction("Valve").triggered.connect(self.AddValve)
        menu.addAction("Program...").triggered.connect(self.SelectProgram)
        menu.addAction("Image...").triggered.connect(self.BrowseForImage)

        self._plusButton.button.setMenu(menu)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.viewer)

        self.setLayout(layout)

        self.isEditing = False

        self._actionsWidget.raise_()
        self._inspectorWidget.raise_()

        self.FloatWidgets()

    def AddValve(self):
        pass

    def BrowseForImage(self):
        pass

    def SelectProgram(self):
        pass

    def resizeEvent(self, event) -> None:
        self.FloatWidgets()
        super().resizeEvent(event)

    def SetEditing(self, editing):
        self.viewer.SetEditing(editing)

        self._lockButton.setVisible(editing)
        self._plusButton.setVisible(editing)
        self._editButton.setVisible(not editing)

        self.FloatWidgets()

    def FloatWidgets(self):
        self._actionsWidget.adjustSize()
        self._inspectorWidget.adjustSize()
        self._actionsWidget.move(self.rect().topRight() - self._actionsWidget.rect().topRight())
        self._inspectorWidget.move(
            self.rect().bottomRight() - self._inspectorWidget.rect().bottomRight())


class FloatingWidget(QFrame):
    onResize = Signal()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.onResize.emit()

    def event(self, e) -> bool:
        if e.type() == QEvent.LayoutRequest:
            self.onResize.emit()
        return super().event(e)


class ActionButtonFrame(QFrame):
    def __init__(self, icon):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.button = QToolButton()
        self.button.setProperty("Attention", True)
        self.button.setIcon(QIcon(icon))
        layout.addWidget(self.button)


class ChipItem(QObject):
    onRemoved = Signal(QObject)

    def __init__(self, graphicsObject: QGraphicsObject):
        super().__init__()
        self._graphicsObject = graphicsObject
        self._hoverWidget = QFrame()

    def HoverWidget(self):
        return self._hoverWidget

    def SetEditing(self, isEditing: bool):
        pass

    def GraphicsObject(self):
        return self._graphicsObject

    @abstractmethod
    def CanSelect(self) -> bool:
        pass

    def SetHovered(self, isHovered: bool):
        pass

    def SetSelected(self, isSelected: bool):
        pass

    @abstractmethod
    def CanMove(self, scenePoint: QPointF) -> bool:
        pass

    def Move(self, delta: QPointF):
        pass

    @abstractmethod
    def CanDelete(self) -> bool:
        pass

    def RequestDelete(self):
        pass

    def RemoveItem(self):
        self.GraphicsObject().deleteLater()
        self.onRemoved.emit(self)

    @abstractmethod
    def CanDuplicate(self) -> bool:
        pass

    def Duplicate(self) -> 'ChipItem':
        pass


class ChipSceneViewer(QGraphicsView):
    selectionChanged = Signal(list)

    def __init__(self):
        super().__init__()

        scene = QGraphicsScene()
        self.setScene(scene)

        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)

        self._offset = QPointF(0, 0)
        self._zoom = 0

        self.backgroundColor = QColor(30, 30, 30)

        self.gridSpacing = QSizeF(60, 60)
        self.gridThickness = 1
        self.gridColor = QColor(50, 50, 50)
        self.gridZoomThreshold = -1.5
        self.showGrid = True

        self.selectionBoxStrokeColor = QColor.fromHsv(200, 210, 250, 255)
        self.selectionBoxFillColor = QColor.fromHsv(200, 210, 250, 50)
        self.selectionBoxThickness = 2
        self._editing = True

        self._hoveredItems: List[ChipItem] = []
        self._selectedItems: List[ChipItem] = []
        self._sceneItems: Set[ChipItem] = set()

        self._boxSelectionRectAnchor = QPointF()
        self._currentCursorPosition = QPointF()

        self.selectionBox = self.scene().addRect(QRectF(),
                                                 QPen(self.selectionBoxStrokeColor,
                                                      self.selectionBoxThickness),
                                                 QBrush(self.selectionBoxFillColor))
        self.selectionBox.setVisible(False)

        self._state = State.IDLE

        self.UpdateView()

    def SetEditing(self, editing: bool):
        self._editing = editing

        self.showGrid = editing

        for item in self._sceneItems:
            item.SetEditing(editing)

        if not editing:
            self.DeselectAll()
            self.selectionChanged.emit(self._selectedItems)

        self.UpdateView()
        self.update()

    def GetSelectedItems(self):
        return self._selectedItems

    def AddItem(self, item: ChipItem):
        if item not in self._sceneItems:
            self._sceneItems.add(item)
            item.Move(QPointF())
            item.onRemoved.connect(self.RemoveItem)
            self.scene().addItem(item.GraphicsObject())
            item.SetEditing(self._editing)
        return item

    def RemoveItem(self, item: ChipItem):
        self.DeselectItem(item)
        if item in self._hoveredItems:
            self._hoveredItems.remove(item)

        if item in self._sceneItems:
            self._sceneItems.remove(item)
            self.scene().removeItem(item.GraphicsObject())
        self.selectionChanged.emit(self._selectedItems)

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
            itemsRect = itemsRect.united(
                item.GraphicsObject().boundingRect().translated(item.GraphicsObject().pos()))
        self._offset = itemsRect.center()

        self.UpdateView()

    def CenterItem(self, item: ChipItem):
        QApplication.processEvents()
        sceneCenter = self.mapToScene(self.rect().center())
        currentCenter = item.GraphicsObject().sceneBoundingRect().center()
        delta = sceneCenter - currentCenter
        item.Move(delta)
        self.DeselectAll()
        self.SelectItem(item)
        self.selectionChanged.emit(self._selectedItems)

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
        if not self._editing or self._state is State.MOVING:
            hoveredChipItems = []
        else:
            # What are we hovering over in the scene
            hoveredGraphicsItems = [item for item in
                                    self.scene().items(self.selectionBox.sceneBoundingRect())]

            hoveredChipItems = [item for item in self._sceneItems if
                                item.GraphicsObject() in hoveredGraphicsItems]
            # Make sure we maintain the found order
            hoveredChipItems.sort(key=lambda x: hoveredGraphicsItems.index(x.GraphicsObject()))

            if self._state is not State.SELECTING:
                hoveredChipItems = hoveredChipItems[:1]

        for item in hoveredChipItems:
            if item not in self._hoveredItems and item.CanSelect():
                item.SetHovered(True)
        for item in self._hoveredItems:
            if item not in hoveredChipItems:
                item.SetHovered(False)
        self._hoveredItems = hoveredChipItems

        goalCursor = None
        if self._state == State.PANNING:
            goalCursor = Qt.ClosedHandCursor
        elif self._state == State.MOVING:
            goalCursor = Qt.SizeAllCursor
        elif self._state == State.IDLE and self.GetSelectionMode() != SelectionMode.MODIFY:
            if len(self._hoveredItems) > 0 and self._hoveredItems[0].CanMove(
                    self.mapToScene(self._currentCursorPosition.toPoint())):
                goalCursor = Qt.SizeAllCursor
        if goalCursor is None and QGuiApplication.overrideCursor() is not None:
            QGuiApplication.restoreOverrideCursor()
        elif QGuiApplication.overrideCursor() != goalCursor:
            QGuiApplication.restoreOverrideCursor()
            QGuiApplication.setOverrideCursor(goalCursor)

    def UpdateSelectionBox(self):
        if self._state == State.SELECTING:
            self.selectionBox.setVisible(True)
            self.selectionBox.prepareGeometryChange()
            self.update()
        else:
            self.selectionBox.setVisible(False)
        self.selectionBox.setRect(self.CreateSelectionRect())

    def drawBackground(self, painter: QPainter, rect: QRectF):
        currentColor = self.backgroundBrush().color()
        if currentColor != self.backgroundColor:
            self.setBackgroundBrush(QBrush(self.backgroundColor))

        super().drawBackground(painter, rect)

        if self._zoom <= self.gridZoomThreshold or not self.showGrid:
            return

        painter.setPen(QPen(self.gridColor, self.gridThickness))

        lines = []
        if self.gridSpacing.width() > 0:
            xStart = rect.left() - rect.left() % self.gridSpacing.width()
            while xStart <= rect.right():
                line = QLine(xStart, rect.bottom(), xStart, rect.top())
                lines.append(line)
                xStart = xStart + self.gridSpacing.width()

        if self.gridSpacing.height() > 0:
            yStart = rect.top() - rect.top() % self.gridSpacing.height()
            while yStart <= rect.bottom():
                line = QLine(rect.left(), yStart, rect.right(), yStart)
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
            super().mousePressEvent(event)
            return

        if event.button() == Qt.RightButton:
            self._state = State.PANNING
        elif event.button() == Qt.LeftButton and self._editing:
            if len(self._hoveredItems) == 0:
                self._state = State.SELECTING
                self._boxSelectionRectAnchor = self.mapToScene(
                    self._currentCursorPosition.toPoint())
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

        super().mousePressEvent(event)
        self.UpdateView()
        self.update()

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
            self.update()

        self.UpdateView()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
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
        self.update()

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.DeleteSelected()

        if event.key() == Qt.Key.Key_D and event.modifiers() == Qt.Modifier.CTRL:
            self.DuplicateSelected()

        super().keyReleaseEvent(event)

    def DeleteSelected(self):
        for item in self.GetSelectedItems().copy():
            if item.CanDelete():
                item.RequestDelete()

    def DuplicateSelected(self):
        newItems = []
        for item in self.GetSelectedItems().copy():
            if item.CanDuplicate():
                newItem = item.Duplicate()
                newItem.Move(QPointF(50, 50))
                self.AddItem(newItem)
                newItems.append(newItem)
        if newItems:
            self.DeselectAll()
            [self.SelectItem(item) for item in newItems]
            self.selectionChanged.emit(self.GetSelectedItems())


class State(Enum):
    IDLE = auto()
    PANNING = auto()
    SELECTING = auto()
    MOVING = auto()


class SelectionMode:
    NORMAL = auto()
    MODIFY = auto()
from typing import Optional

from PySide6.QtGui import QPixmap, QImage, Qt
from PySide6.QtCore import QPointF, QSizeF, Signal, QRectF
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from Data.Image import Image
from UI.AppGlobals import AppGlobals

from pathlib import Path


class ImageChipItem(WidgetChipItem):
    def __init__(self, image: Image):
        super().__init__()

        self._image = image

        self.image = ImageLabel()

        AppGlobals.Instance().onChipAddRemove.connect(self.CheckForImage)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.image)
        self.containerWidget.setLayout(layout)

        self._lastFilename = None
        self._lastVersion = -1
        self._lastSize = None

        self._rawImage: Optional[QImage] = None

        self.GraphicsObject().setZValue(-10)

        self._neHandle = MovingHandle(self.bigContainer)
        self._neHandle.moved.connect(
            lambda currentPosition: self.HandleResize(self._neHandle, currentPosition))

        self._nwHandle = MovingHandle(self.bigContainer)
        self._nwHandle.moved.connect(
            lambda currentPosition: self.HandleResize(self._nwHandle, currentPosition))

        self._seHandle = MovingHandle(self.bigContainer)
        self._seHandle.moved.connect(
            lambda currentPosition: self.HandleResize(self._seHandle, currentPosition))

        self._swHandle = MovingHandle(self.bigContainer)
        self._swHandle.moved.connect(
            lambda currentPosition: self.HandleResize(self._swHandle, currentPosition))

        self._handles = [self._neHandle, self._seHandle, self._swHandle, self._nwHandle]

        [handle.setCursor(cursor) for handle, cursor in
         zip(self._handles, [Qt.SizeBDiagCursor, Qt.SizeFDiagCursor, Qt.SizeBDiagCursor, Qt.SizeFDiagCursor])]

        self.Update()
        self.Move(QPointF())
        self.PositionHandles()

    def CanMove(self, scenePoint: QPointF) -> bool:
        childAt = self.bigContainer.childAt(self.GraphicsObject().mapFromScene(scenePoint).toPoint())
        return childAt not in self._handles

    def SetSelected(self, isSelected: bool):
        self.PositionHandles()
        for handle in self._handles:
            handle.setVisible(isSelected)

    def CheckForImage(self):
        if self._image not in AppGlobals.Chip().images:
            self.RemoveItem()

    def Move(self, delta: QPointF):
        if delta != QPointF():
            AppGlobals.Instance().onChipDataModified.emit()
        self._image.position += delta
        self.GraphicsObject().setPos(self._image.position)
        super().Move(delta)

    def RequestDelete(self):
        AppGlobals.Chip().images.remove(self._image)
        AppGlobals.Instance().onChipAddRemove.emit()

    def Duplicate(self) -> 'ChipItem':
        newImage = Image(self._image.path)
        newImage.position = QPointF(self._image.position)
        newImage.size = QSizeF(self._image.size)

        AppGlobals.Chip().images.append(newImage)
        AppGlobals.Instance().onChipAddRemove.emit()
        return ImageChipItem(newImage)

    def PositionHandles(self):
        self._neHandle.move(self.bigContainer.rect().topRight() - self._neHandle.rect().topRight())
        self._nwHandle.move(self.bigContainer.rect().topLeft() - self._neHandle.rect().topLeft())
        self._seHandle.move(self.bigContainer.rect().bottomRight() - self._neHandle.rect().bottomRight())
        self._swHandle.move(self.bigContainer.rect().bottomLeft() - self._neHandle.rect().bottomLeft())

    def Update(self):
        mTime = Path(self._image.path).stat().st_mtime

        if mTime > self._lastVersion or self._image.path != self._lastFilename:
            self._lastVersion = mTime
            self._lastSize = None
            self._lastFilename = self._image.path

            newImage = QImage(str(self._image.path.absolute()))
            if self._rawImage and newImage.size() != self._rawImage.size():
                self._image.size = newImage.size()
            self._rawImage = newImage
            self.PositionHandles()

        if self._image.size != self._lastSize:
            size = QSizeF(self._image.size.width(), self._image.size.height()).toSize()
            self.image.setPixmap(
                QPixmap(self._rawImage).scaled(size,
                                               Qt.AspectRatioMode.IgnoreAspectRatio))
            self.image.setFixedSize(size)
            self._lastSize = self._image.size
            self.PositionHandles()

    def HandleResize(self, handle: 'MovingHandle', currentPosition: QPointF):
        imageRect = QRectF(self._image.position, self._image.size)
        currentPosition = self.GraphicsObject().mapToScene(self.bigContainer.mapFromGlobal(currentPosition))

        getHandlePosition = lambda rect: {self._neHandle: rect.topRight(),
                                          self._nwHandle: rect.topLeft(),
                                          self._seHandle: rect.bottomRight(),
                                          self._swHandle: rect.bottomLeft()}[handle]

        setHandlePosition = lambda rect, position: {self._neHandle: rect.setTopRight,
                                                    self._nwHandle: rect.setTopLeft,
                                                    self._seHandle: rect.setBottomRight,
                                                    self._swHandle: rect.setBottomLeft}[handle](position)

        trueDelta = currentPosition - getHandlePosition(imageRect)

        setHandlePosition(imageRect, getHandlePosition(imageRect) + trueDelta)

        self._image.position = imageRect.topLeft()
        self._image.size = imageRect.size()
        self.Update()
        self.GraphicsObject().setPos(self._image.position)
        self.GraphicsObject().prepareGeometryChange()


class MovingHandle(QFrame):
    moved = Signal(QPointF)

    def __init__(self, parent):
        super().__init__(parent)

        self._pressed = False
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)

    def mousePressEvent(self, event) -> None:
        self._pressed = True

    def mouseMoveEvent(self, event) -> None:
        if self._pressed:
            currentPosition = event.globalPosition()
            self.moved.emit(currentPosition)

    def mouseReleaseEvent(self, event) -> None:
        self._pressed = False


class ImageLabel(QLabel):
    pass
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from typing import List
from UI.ChipEditor.ChipItem import ChipItem


class Inspector(QFrame):
    def __init__(self, parent):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._itemsLayout = QVBoxLayout()
        self._itemsLayout.setContentsMargins(0, 0, 0, 0)
        self._itemsLayout.setSpacing(0)

        self.setLayout(layout)

        self._titleWidget = TitleWidget("Properties")
        layout.addWidget(self._titleWidget)
        layout.addLayout(self._itemsLayout)
        self.SetSelection([])

    def SetSelection(self, selection: List[ChipItem]):
        self.setVisible(len(selection) > 0)

        while self._itemsLayout.count():
            self._itemsLayout.takeAt(0).widget().setVisible(False)

        for selected in selection:
            self._itemsLayout.addWidget(selected.HoverWidget())
            selected.HoverWidget().setVisible(True)


class TitleWidget(QLabel):
    pass
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QLabel, QHBoxLayout, QCheckBox

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from UI.ProgramViews.ProgramInstanceWidget import ProgramInstanceWidget
from Data.Program.ProgramPreset import ProgramPreset
from UI.AppGlobals import AppGlobals


class ProgramPresetItem(WidgetChipItem):
    def __init__(self, preset: ProgramPreset):
        super().__init__()

        AppGlobals.Instance().onChipAddRemove.connect(self.CheckForPreset)

        self._preset = preset

        self._presetNameLabel = QLabel(preset.name)
        self._presetNameLabel.setAlignment(Qt.AlignCenter)

        self._instanceWidget = ProgramInstanceWidget(preset.instance)
        self._instanceWidget.SetTitleVisible(False)
        self._instanceWidget.ownsInstance = True

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._presetNameLabel)
        layout.addWidget(self._instanceWidget)
        self.containerWidget.setLayout(layout)

        inspLayout = QVBoxLayout()
        inspLayout.setContentsMargins(0, 0, 0, 0)
        inspLayout.setSpacing(0)
        nameLayout = QHBoxLayout()
        nameLayout.setContentsMargins(0, 0, 0, 0)
        nameLayout.setSpacing(0)
        inspLayout.addLayout(nameLayout)
        self.HoverWidget().setLayout(inspLayout)
        self._presetNameField = QLineEdit(preset.name)
        self._presetNameField.textChanged.connect(self.UpdatePreset)
        self._showDescriptionField = QCheckBox("Show Description")
        self._showDescriptionField.setChecked(self._preset.showDescription)
        self._showDescriptionField.stateChanged.connect(self.UpdatePreset)
        nameLayout.addWidget(self._presetNameField)
        inspLayout.addWidget(self._showDescriptionField)

        self._inspectorInstance = ProgramInstanceWidget(preset.instance)
        self._inspectorInstance.SetShowAllParameters(True)
        self._inspectorInstance.SetEditParameterVisibility(True)
        self._inspectorInstance.SetDescriptionVisible(False)
        self._inspectorInstance.SetTitleVisible(False)
        self._inspectorInstance.SetRunVisible(False)
        self._inspectorInstance.ownsInstance = True
        inspLayout.addWidget(self._inspectorInstance)

        self.UpdatePresetView()
        self.CheckForPreset()

    def SetEditing(self, isEditing: bool):
        self._instanceWidget.runButton.setEnabled(not isEditing)
        self._instanceWidget.stopButton.setEnabled(not isEditing)

    def Move(self, delta: QPointF):
        if delta != QPointF():
            AppGlobals.Instance().onChipDataModified.emit()
        self._preset.position += delta
        self.GraphicsObject().setPos(self._preset.position)
        super().Move(delta)

    def CanMove(self, scenePoint: QPointF) -> bool:
        childAt = self.bigContainer.childAt(self.GraphicsObject().mapFromScene(scenePoint).toPoint())
        return isinstance(childAt, QLabel) or childAt == self.containerWidget

    def UpdatePreset(self):
        self._preset.name = self._presetNameField.text()
        self._preset.showDescription = self._showDescriptionField.isChecked()
        AppGlobals.Instance().onChipDataModified.emit()
        self.UpdatePresetView()

    def UpdatePresetView(self):
        self._presetNameLabel.setText(
            "<b>" + self._preset.name + "</b> <i>(" + self._preset.instance.program.name + ")</i>")
        if self._instanceWidget.DescriptionVisible() != self._preset.showDescription:
            self._instanceWidget.SetDescriptionVisible(self._preset.showDescription)

    def CheckForPreset(self):
        if self._preset not in AppGlobals.Chip().programPresets:
            self.RemoveItem()

    def RequestDelete(self):
        super().RequestDelete()
        AppGlobals.Chip().programPresets.remove(self._preset)
        AppGlobals.Instance().onChipAddRemove.emit()

    def Duplicate(self) -> 'ChipItem':
        newPreset = ProgramPreset(self._preset.instance.program)
        newPreset.instance = self._preset.instance.Clone()
        newPreset.position = QPointF(self._preset.position)
        newPreset.name = self._preset.name

        AppGlobals.Chip().programPresets.append(newPreset)
        AppGlobals.Instance().onChipAddRemove.emit()
        return ProgramPresetItem(newPreset)

    def RunPreset(self):
        AppGlobals.ProgramRunner().Run(self._preset.instance)
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QPushButton, QSpinBox, QLabel, QGridLayout, QLineEdit, QHBoxLayout

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from Data.Valve import Valve
from UI.AppGlobals import AppGlobals


class ValveChipItem(WidgetChipItem):
    def __init__(self, valve: Valve):
        super().__init__()

        AppGlobals.Instance().onChipAddRemove.connect(self.CheckForValve)
        AppGlobals.Instance().onValveChanged.connect(self.UpdateDisplay)

        self._valve = valve

        self.valveToggleButton = QPushButton()
        self.valveToggleButton.setObjectName("ValveButton")
        self.containerWidget.setObjectName("ValveContainer")
        self.valveNumberLabel = QLabel("Number")
        self.valveNumberDial = QSpinBox()
        self.valveNumberDial.setMinimum(0)
        self.valveNumberDial.setValue(self._valve.solenoidNumber)
        self.valveNumberDial.setMaximum(9999)
        self.valveNumberDial.valueChanged.connect(self.UpdateValve)

        self.valveNameLabel = QLabel("Name")
        self.valveNameField = QLineEdit(self._valve.name)
        self.valveNameField.textChanged.connect(self.UpdateValve)

        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.addWidget(self.valveToggleButton)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.valveNameLabel, 0, 0)
        layout.addWidget(self.valveNameField, 0, 1)
        layout.addWidget(self.valveNumberLabel, 1, 0)
        layout.addWidget(self.valveNumberDial, 1, 1)
        self.HoverWidget().setLayout(layout)

        self.containerWidget.setLayout(mainLayout)
        self.valveToggleButton.clicked.connect(self.Toggle)

        self._showOpen = None

        self.UpdateDisplay()
        self.Move(QPointF())

    def SetEditing(self, isEditing: bool):
        self.valveToggleButton.blockSignals(isEditing)

    def CheckForValve(self):
        if self._valve not in AppGlobals.Chip().valves:
            self.RemoveItem()

    def Move(self, delta: QPointF):
        if delta != QPointF():
            AppGlobals.Instance().onChipDataModified.emit()
        self._valve.position += delta
        self.GraphicsObject().setPos(self._valve.position)
        super().Move(delta)

    def UpdateValve(self):
        self._valve.solenoidNumber = self.valveNumberDial.value()
        self._valve.name = self.valveNameField.text()
        AppGlobals.Instance().onChipDataModified.emit()
        self.UpdateDisplay()

    def Toggle(self):
        AppGlobals.Rig().SetSolenoidState(self._valve.solenoidNumber,
                                          not AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber), True)
        AppGlobals.Instance().onValveChanged.emit()

    def RequestDelete(self):
        AppGlobals.Chip().valves.remove(self._valve)
        AppGlobals.Instance().onChipAddRemove.emit()

    def Duplicate(self) -> 'ChipItem':
        newValve = Valve()
        newValve.position = QPointF(self._valve.position)
        newValve.name = self._valve.name
        newValve.solenoidNumber = AppGlobals.Chip().NextSolenoidNumber()

        AppGlobals.Chip().valves.append(newValve)
        AppGlobals.Instance().onChipAddRemove.emit()
        return ValveChipItem(newValve)

    def UpdateDisplay(self):
        text = self._valve.name + "\n(" + str(self._valve.solenoidNumber) + ")"
        if text != self.valveToggleButton.text():
            self.valveToggleButton.setText(text)

        newState = AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber)
        if newState != self._showOpen:
            self.valveToggleButton.setProperty("On", newState)
            self.valveToggleButton.setProperty("Off", not newState)
            self.valveToggleButton.setStyle(self.valveToggleButton.style())
            self._showOpen = newState
from PySide6.QtCore import QPointF, QEvent
from PySide6.QtWidgets import QGraphicsProxyWidget, QFrame, QVBoxLayout
from UI.ChipEditor.ChipItem import ChipItem
from UI.StylesheetLoader import StylesheetLoader


class WidgetChipItem(ChipItem):

    def __init__(self):
        self.graphicsWidget = ClearingProxy()

        super().__init__(self.graphicsWidget)

        self.bigContainer = WidgetChipItemContainer()

        self.containerWidget = WidgetChipItemContents()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.containerWidget)

        self.bigContainer.setLayout(layout)
        self.graphicsWidget.setWidget(self.bigContainer)

        StylesheetLoader.RegisterWidget(self.bigContainer)

        self._displayHovered = False
        self._displaySelected = False

        self.UpdateStyle()

    def SetHovered(self, isHovered: bool):
        self._displayHovered = isHovered
        self.UpdateStyle()

    def SetSelected(self, isSelected: bool):
        self._displaySelected = isSelected
        self.UpdateStyle()

    def CanSelect(self) -> bool:
        return True

    def CanMove(self, scenePoint: QPointF) -> bool:
        return True

    def CanDelete(self) -> bool:
        return True

    def RemoveItem(self):
        super().RemoveItem()
        StylesheetLoader.UnregisterWidget(self.bigContainer)

    def CanDuplicate(self) -> bool:
        return True

    def UpdateStyle(self):
        state = {(False, False): 'None',
                 (False, True): 'Hover',
                 (True, False): 'Select',
                 (True, True): 'HoverAndSelect'}[(self._displaySelected, self._displayHovered)]
        oldState = self.containerWidget.property("state")
        if oldState is None or oldState != state:
            self.containerWidget.setProperty("state", state)
            self.containerWidget.setStyle(self.containerWidget.style())


class ClearingProxy(QGraphicsProxyWidget):
    def mousePressEvent(self, event):
        toClear = [self.widget()]
        while toClear:
            w = toClear.pop(0)
            w.clearFocus()
            toClear += [child for child in w.children() if isinstance(child, QFrame)]
        super().mousePressEvent(event)


class WidgetChipItemContainer(QFrame):
    def event(self, e) -> bool:
        if e.type() == QEvent.LayoutRequest:
            self.adjustSize()
        return super().event(e)


class WidgetChipItemContents(QFrame):
    pass
from typing import List
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QToolButton, QPlainTextEdit, \
    QGridLayout, QSizePolicy
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from UI.ProgramViews.DataValueWidget import DataValueWidget
from Data.Program.ProgramInstance import ProgramInstance, Parameter
from Data.Program.Data import DataType
from UI.AppGlobals import AppGlobals


class ProgramInstanceWidget(QFrame):
    def __init__(self, programInstance: ProgramInstance):
        super().__init__()

        AppGlobals.Instance().onChipAddRemove.connect(self.UpdateParameterItems)
        AppGlobals.ProgramRunner().onInstanceChange.connect(self.UpdateInstanceView)
        AppGlobals.Instance().onChipDataModified.connect(self.UpdateInstanceView)

        self._showAllParameters = False
        self._editParameterVisibility = False
        self._runVisible = True

        self.programInstance = programInstance
        self.ownsInstance = False

        self.programNameWidget = QLabel()
        self.programNameWidget.setAlignment(Qt.AlignCenter)

        self._description = QPlainTextEdit(programInstance.program.description)
        self._description.setReadOnly(True)

        outerLayout = QHBoxLayout()
        outerLayout.setContentsMargins(0, 0, 0, 0)
        outerLayout.setSpacing(0)

        innerLayout = QVBoxLayout()
        innerLayout.setContentsMargins(0, 0, 0, 0)
        innerLayout.setSpacing(0)

        self.runButton = QPushButton("Run")
        self.runButton.setProperty("On", True)
        self.runButton.clicked.connect(self.RunProgram)

        self.stopButton = QPushButton("Stop")
        self.stopButton.setProperty("Off", True)
        self.stopButton.clicked.connect(self.StopProgram)

        self.parameterItems: List[ProgramParameterItem] = []

        self._parameterWidget = QFrame()
        self._parametersLayout = QGridLayout()
        self._parametersLayout.setAlignment(Qt.AlignTop)
        self._parametersLayout.setSpacing(0)
        self._parametersLayout.setContentsMargins(0, 0, 0, 0)
        self._parameterWidget.setLayout(self._parametersLayout)

        innerLayout.addWidget(self.programNameWidget)
        innerLayout.addWidget(self._parameterWidget)
        innerLayout.addWidget(self.runButton)
        innerLayout.addWidget(self.stopButton)
        innerLayout.addStretch(1)

        outerLayout.addLayout(innerLayout)
        outerLayout.addWidget(self._description)

        self.setLayout(outerLayout)

        self.UpdateParameterItems()

    def SetRunVisible(self, visible):
        self._runVisible = visible
        self.UpdateInstanceView()

    def SetTitleVisible(self, visible):
        self.programNameWidget.setVisible(visible)

    def SetDescriptionVisible(self, visisble):
        self._description.setVisible(visisble)

    def DescriptionVisible(self):
        return self._description.isVisible()

    def SetShowAllParameters(self, showAll):
        self._showAllParameters = showAll
        self.UpdateInstanceView()

    def SetEditParameterVisibility(self, edit):
        self._editParameterVisibility = edit
        self.UpdateInstanceView()

    def UpdateParameterItems(self):
        [item.deleteLater() for item in self.parameterItems]
        self.parameterItems = []

        i = 0
        for parameter in self.programInstance.program.parameters:
            if parameter.dataType is not DataType.OTHER:
                newItem = ProgramParameterItem(parameter, self.programInstance)
                self._parametersLayout.addWidget(newItem.visibilityToggle, i, 0)
                self._parametersLayout.addWidget(newItem.parameterName, i, 1)
                self._parametersLayout.addWidget(newItem.valueField, i, 2)
                self.parameterItems.append(newItem)
                i += 1

        self._parameterWidget.setVisible(len(self.parameterItems) > 0)
        self.UpdateInstanceView()

    def UpdateInstanceView(self):
        if not self.programInstance.program.description:
            text = "No description provided."
        else:
            text = self.programInstance.program.description
        if self._description.toPlainText() != text:
            self._description.setPlainText(text)

        if self.programNameWidget.text() != self.programInstance.program.name:
            self.programNameWidget.setText(self.programInstance.program.name)

        running = AppGlobals.ProgramRunner().IsRunning(self.programInstance)
        if not self._runVisible:
            self.runButton.setVisible(False)
            self.stopButton.setVisible(False)
        else:
            self.runButton.setVisible(not running)
            self.stopButton.setVisible(running)

        for item in self.parameterItems:
            if item.parameter not in self.programInstance.parameterValues:
                continue
            item.UpdateFields()
            if self._showAllParameters:
                item.parameterName.setVisible(True)
                item.valueField.setVisible(True)
                item.visibilityToggle.setVisible(self._editParameterVisibility)
            else:
                item.parameterName.setVisible(self.programInstance.parameterVisibility[item.parameter])
                item.valueField.setVisible(self.programInstance.parameterVisibility[item.parameter])
                item.visibilityToggle.setVisible(False)

    def RunProgram(self):
        if self.ownsInstance:
            AppGlobals.ProgramRunner().Run(self.programInstance, None)
        else:
            AppGlobals.ProgramRunner().Run(self.programInstance.Clone(), None)

    def StopProgram(self):
        AppGlobals.ProgramRunner().Stop(self.programInstance)


class ProgramParameterItem:
    def __init__(self, parameter: Parameter, instance: ProgramInstance):
        self.parameter = parameter
        self._programInstance = instance
        self.parameterName = QLabel()

        self.visibilityToggle = VisibilityToggle()
        self.visibilityToggle.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.visibilityToggle.clicked.connect(self.ToggleVisibility)

        self.valueField = DataValueWidget(self.parameter.dataType, self.parameter.listType)
        self.valueField.dataChanged.connect(self.UpdateParameterValue)

        self.valueField.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.UpdateFields()

    def deleteLater(self):
        self.visibilityToggle.deleteLater()
        self.valueField.deleteLater()
        self.parameterName.deleteLater()

    def ToggleVisibility(self):
        self._programInstance.parameterVisibility[self.parameter] = not self._programInstance.parameterVisibility[
            self.parameter]
        AppGlobals.Instance().onChipDataModified.emit()
        self.UpdateFields()

    def UpdateParameterValue(self):
        lastValue = self._programInstance.parameterValues[self.parameter]

        if self.parameter.dataType is DataType.INTEGER:
            value = self.parameter.ClampInteger(self.valueField.GetData())
        elif self.parameter.dataType is DataType.FLOAT:
            value = self.parameter.ClampFloat(self.valueField.GetData())
        else:
            value = self.valueField.GetData()
        self._programInstance.parameterValues[self.parameter] = value

        if self._programInstance.parameterValues[self.parameter] != lastValue:
            AppGlobals.Instance().onChipDataModified.emit()

    def UpdateFields(self):
        self.parameterName.setText(self.parameter.name)

        if self.parameter.dataType is DataType.LIST:
            self.parameterName.setAlignment(Qt.AlignTop)
        else:
            self.parameterName.setAlignment(Qt.AlignVCenter)

        if self._programInstance.parameterVisibility[self.parameter]:
            self.visibilityToggle.setIcon(QIcon("Assets/Images/eyeOpen.png"))
        else:
            self.visibilityToggle.setIcon(QIcon("Assets/Images/eyeClosed.png"))

        self.valueField.Update(self._programInstance.parameterValues[self.parameter])


class VisibilityToggle(QToolButton):
    pass
