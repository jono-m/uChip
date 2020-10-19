from UI.WorldBrowser.SelectableItem import *
from UI.StylesheetLoader import *


class BlockItem(QGraphicsProxyWidget, SelectableItem):
    def __init__(self, scene: QGraphicsScene):
        super().__init__()

        self.blockWidget = QFrame()
        self.blockWidget.setObjectName("BlockItem")
        self.setWidget(self.blockWidget)
        scene.addItem(self)

        StylesheetLoader.GetInstance().RegisterWidget(self.blockWidget)

        self.blockLayout = QVBoxLayout()
        self.blockLayout.setContentsMargins(0, 0, 0, 0)
        self.blockLayout.setSpacing(0)
        self.blockWidget.setLayout(self.blockLayout)

        self.container = QFrame()
        self.blockLayout.addWidget(self.container)

        self.displayHovered = False
        self.displaySelected = False

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.container.setLayout(layout)

        self.UpdateStyle()

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
            self.container.setStyle(self.container.style())

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
                if child.hasFocus() or BlockItem.IsChildFocused(child):
                    return True
        return False

    @staticmethod
    def ClearFocusAll(widget):
        widget.clearFocus()
        for child in widget.children():
            if isinstance(child, QWidget):
                BlockItem.ClearFocusAll(child)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.ClearFocusAll(self.blockWidget)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        self.OnDoubleClick()
        super().mousePressEvent(event)

    def DoMove(self, currentPosition: QPointF, delta: QPointF):
        self.setPos(self.pos() + delta)

    def IsMovableAtPoint(self, scenePoint: QPointF):
        return self.IsContainerSelected(scenePoint)

    def TryDelete(self) -> bool:
        if not self.IsChildFocused(self.widget()):
            return self.blockWidget.TryDelete()
        return False

    def OnDoubleClick(self):
        pass
