from UI.WorldBrowser.SelectableItem import *
from UI.StylesheetLoader import *


class BlockItem(QFrame, SelectableItem):
    def __init__(self):
        super().__init__()

        StylesheetLoader.GetInstance().RegisterWidget(self)

        self.blockLayout = QVBoxLayout()
        self.blockLayout.setContentsMargins(0, 0, 0, 0)
        self.blockLayout.setSpacing(0)
        self.setLayout(self.blockLayout)

        self.container = QFrame()
        self.blockLayout.addWidget(self.container)

        self.displayHovered = False
        self.displaySelected = False

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.container.setLayout(layout)

        self.OnPosChange = Event()
        self.OnStyleUpdate = Event()

        self._scenePos = QPointF()

        self.UpdateStyle()

    def scenePos(self):
        return self._scenePos

    def setPos(self, point: QPointF):
        self._scenePos = point
        self.OnPosChange.Invoke(self._scenePos)

    def SetIsHovered(self, hoverOn):
        if self.displayHovered != hoverOn:
            self.displayHovered = hoverOn
            self.UpdateStyle()

    def SetIsSelected(self, isSelected):
        if self.displaySelected != isSelected:
            self.displaySelected = isSelected
            self.UpdateStyle()

    def UpdateStyle(self):
        oldProperty = self.container.property('state')
        if self.displaySelected:
            if self.displayHovered:
                self.container.setProperty('state', 'HoverAndSelect')
            else:
                self.container.setProperty('state', 'Select')
        else:
            if self.displayHovered:
                self.container.setProperty('state', 'Hover')
            else:
                self.container.setProperty('state', 'None')
        if oldProperty is None or oldProperty != self.container.property('state'):
            self.OnStyleUpdate.Invoke()


class BlockItemGraphicsWidget(QGraphicsProxyWidget, SelectableItem):
    def __init__(self, scene: QGraphicsScene, blockWidget: BlockItem, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.blockWidget = blockWidget
        self.blockWidget.OnPosChange.Register(lambda point: self.setPos(point))
        self.blockWidget.OnStyleUpdate.Register(lambda: self.setStyle(self.style()))
        self.setWidget(self.blockWidget)
        scene.addItem(self)
        self.setPos(self.blockWidget.scenePos())

    def IsContainerSelected(self, scenePos):
        childAt = self.blockWidget.childAt(self.mapFromScene(scenePos).toPoint())
        if childAt is None or isinstance(childAt, QLabel) or isinstance(childAt, QFrame):
            return True
        else:
            return False

    @staticmethod
    def IsChildFocused(widget: QWidget):
        for child in widget.children():
            if isinstance(child, QWidget):
                if child.hasFocus() or BlockItemGraphicsWidget.IsChildFocused(child):
                    return True
        return False

    @staticmethod
    def ClearFocusAll(widget):
        widget.clearFocus()
        for child in widget.children():
            if isinstance(child, QWidget):
                BlockItemGraphicsWidget.ClearFocusAll(child)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.ClearFocusAll(self.blockWidget)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        self.OnDoubleClick()
        super().mousePressEvent(event)

    def DoMove(self, currentPosition: QPointF, delta: QPointF):
        self.blockWidget.setPos(self.pos() + delta)

    def IsMovableAtPoint(self, scenePoint: QPointF):
        return self.IsContainerSelected(scenePoint)

    def TryDelete(self) -> bool:
        if not self.IsChildFocused(self.widget()):
            return self.blockWidget.TryDelete()
        return False

    def SetIsHovered(self, hoverOn):
        self.blockWidget.SetIsHovered(hoverOn)

    def SetIsSelected(self, isSelected):
        self.blockWidget.SetIsSelected(isSelected)

    def TryDuplicate(self):
        return self.blockWidget.TryDuplicate()

    def IsSelectable(self) -> bool:
        return self.blockWidget.IsSelectable()

    def MoveFinished(self):
        self.blockWidget.MoveFinished()

    def OnDoubleClick(self):
        pass
