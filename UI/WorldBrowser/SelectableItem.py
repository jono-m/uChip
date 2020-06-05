from PySide2.QtCore import *
from LogicBlocks.IOBlocks import *


# noinspection PyMethodMayBeStatic
class SelectableItem:
    def SetIsHovered(self, hoverOn):
        pass

    def SetIsSelected(self, isSelected):
        pass

    def TryDuplicate(self):
        return None

    def IsSelectable(self) -> bool:
        return True

    def IsMovableAtPoint(self, scenePosition: QPointF):
        return True

    def DoMove(self, currentPosition: QPointF, delta: QPointF):
        pass

    def TryDelete(self) -> bool:
        return False

    def MoveFinished(self):
        pass
