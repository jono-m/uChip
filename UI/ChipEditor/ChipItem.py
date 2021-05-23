from Model.Chip import Chip
from PySide6.QtWidgets import QGraphicsObject, QWidget, QVBoxLayout
from PySide6.QtCore import QPointF, QTimer
from abc import ABC, abstractmethod


class ChipItem(ABC):
    def __init__(self, chip: Chip, graphicsObject: QGraphicsObject):
        self._chip = chip
        self._graphicsObject = graphicsObject

        self._inspectorWidget = QWidget()
        self._inspectorLayout = QVBoxLayout()
        self._inspectorWidget.setLayout(self._inspectorWidget)

        self._inspectorWidget.setVisible(False)

        timer = QTimer(self.GraphicsObject())
        timer.timeout.connect(self.Update)
        timer.start(30)

    def InspectorLayout(self):
        return self._inspectorLayout

    def InspectorWidget(self):
        return self._inspectorWidget
    
    def GraphicsObject(self):
        return self._graphicsObject

    def Chip(self):
        return self._chip

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

    def Delete(self):
        pass

    @abstractmethod
    def CanDuplicate(self) -> bool:
        pass

    def Duplicate(self) -> 'ChipItem':
        pass

    def Update(self):
        pass
