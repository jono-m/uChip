from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsProxyWidget, QLabel, QWidget
from UI.ChipEditor.ChipItem import ChipItem, Chip
from UI.StylesheetLoader import StylesheetLoader


class WidgetChipItem(ChipItem):
    def __init__(self):
        self.graphicsWidget = ClearingProxy()

        super().__init__(self.graphicsWidget)

        self.containerWidget = WidgetChipItemContainer()
        self.graphicsWidget.setWidget(self.containerWidget)

        StylesheetLoader.RegisterWidget(self.containerWidget)

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
        childAt = self.containerWidget.childAt(self.GraphicsObject().mapFromScene(scenePoint).toPoint())
        return childAt is None or isinstance(childAt, QLabel)

    def CanDelete(self) -> bool:
        return True

    def Delete(self):
        StylesheetLoader.UnregisterWidget(self.containerWidget)

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
            toClear += [child for child in w.children() if isinstance(child, QWidget)]
        super().mousePressEvent(event)


class WidgetChipItemContainer(QWidget):
    pass
