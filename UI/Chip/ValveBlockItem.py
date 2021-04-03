from UI.LogicBlock.LogicBlockItem import *
from BlockSystem.ValveLogicBlock import *


class ValveBlockItem(LogicBlockItem):
    def __init__(self, scene, vb: ValveLogicBlock):
        super().__init__(scene, vb)
        self.vb = vb

        self.vb.OnOutputsUpdated.Register(self.ChangeColor, True)

    def ChangeColor(self):
        lastStyle = self.container.property("valveState")
        if lastStyle is None or lastStyle != self.vb.IsOpen():
            self.container.setProperty("valveState", self.vb.IsOpen())
            self.container.setStyle(self.container.style())
