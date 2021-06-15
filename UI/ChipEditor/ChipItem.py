from PySide6.QtWidgets import QGraphicsObject
from PySide6.QtCore import QPointF, QTimer, Signal, QObject
from abc import abstractmethod


class ChipItem(QObject):
    onRemoved = Signal(QObject)

    def __init__(self, graphicsObject: QGraphicsObject):
        super().__init__()
        self._graphicsObject = graphicsObject

        timer = QTimer(self.GraphicsObject())
        timer.timeout.connect(self.Update)
        timer.start(30)

    def GraphicsObject(self):
        return self._graphicsObject

    def SetEditDisplay(self, editing: bool):
        pass

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

    def Update(self):
        pass
