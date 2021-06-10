from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsProxyWidget, QLabel, QWidget, QVBoxLayout
from UI.ChipEditor.ChipItem import ChipItem
from UI.StylesheetLoader import StylesheetLoader


class WidgetChipItem(ChipItem):

    def __init__(self):
        self.graphicsWidget = ClearingProxy()

        super().__init__(self.graphicsWidget)

        self._bigContainer = WidgetChipItemContainer()

        self.containerWidget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.containerWidget)

        self._bigContainer.setLayout(layout)
        self.graphicsWidget.setWidget(self._bigContainer)

        StylesheetLoader.RegisterWidget(self._bigContainer)

        self._displayHovered = False
        self._displaySelected = False

        self.UpdateStyle()

    def SetEditDisplay(self, editing: bool):
        self.containerWidget.adjustSize()
        self._bigContainer.adjustSize()

    def SetHovered(self, isHovered: bool):
        self._displayHovered = isHovered
        self.UpdateStyle()

    def SetSelected(self, isSelected: bool):
        self._displaySelected = isSelected
        self.UpdateStyle()

    def CanSelect(self) -> bool:
        return True

    def CanMove(self, scenePoint: QPointF) -> bool:
        childAt = self._bigContainer.childAt(self.GraphicsObject().mapFromScene(scenePoint).toPoint())
        return childAt is None or childAt is self.containerWidget or isinstance(childAt, QLabel)

    def CanDelete(self) -> bool:
        return True

    def RemoveItem(self):
        super().RemoveItem()
        StylesheetLoader.UnregisterWidget(self._bigContainer)

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
