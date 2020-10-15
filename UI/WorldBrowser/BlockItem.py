from UI.WorldBrowser.SelectableItem import *
from UI.StylesheetLoader import *


class BlockItem(QGraphicsProxyWidget, SelectableItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        blockWidget = QFrame()
        StylesheetLoader.GetInstance().RegisterWidget(blockWidget)

        self.blockLayout = QVBoxLayout()
        self.blockLayout.setContentsMargins(0, 0, 0, 0)
        self.blockLayout.setSpacing(0)
        blockWidget.setLayout(self.blockLayout)

        self.container = QFrame()
        self.blockLayout.addWidget(self.container)

        self.displayHovered = False
        self.displaySelected = False

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.container.setLayout(layout)

        self.setWidget(blockWidget)
        self.UpdateStyle()

    def IsContainerSelected(self, scenePos):
        childAt = self.widget().childAt(self.mapFromScene(scenePos).toPoint())
        if childAt is None:
            return True
        else:
            if childAt.property("PreventMove") is not None:
                return False
            else:
                if isinstance(childAt, QLabel) or isinstance(childAt, QFrame):
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
            self.setStyle(self.style())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.ClearFocusAll(self.widget())
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
            return True
        return False

    def OnDoubleClick(self):
        pass
