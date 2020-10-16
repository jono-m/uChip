from UI.LogicBlock.LogicBlockItem import *
from ChipController.ValveBlock import *


class ValveBlockItem(LogicBlockItem):
    def __init__(self, vb: ValveLogicBlock):
        super().__init__(vb)
        self.vb = vb

        self.vb.OnOutputsUpdated.Register(self.ChangeColor, True)

    def ChangeColor(self):
        lastStyle = self.container.property("valveState")
        if lastStyle is None or lastStyle != self.vb.IsOpen():
            self.container.setProperty("valveState", self.vb.IsOpen())
            self.setStyle(self.style())
