from UI.LogicBlock.LogicBlockEditor import *
from ChipController.ChipController import *
from UI.Chip.ValveBlockItem import *


class ChipEditor(LogicBlockEditor):
    def __init__(self):
        super().__init__()

        self.chipController: typing.Optional[ChipController] = None

    def Clear(self):
        self.chipController = None
        super().Clear()

    def LoadChipController(self, chipController: ChipController):
        super().LoadBlock(chipController.GetLogicBlock())
        self.chipController = chipController

    def CreateBlockItem(self, newBlock: LogicBlock):
        if isinstance(newBlock, ValveLogicBlock):
            return ValveBlockItem(self.worldBrowser.scene(), newBlock)
        else:
            return super().CreateBlockItem(newBlock)
