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
