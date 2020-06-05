from UI.LogicBlock.LogicBlockItem import *
from ChipController.ValveBlock import *


class ValveBlockItem(LogicBlockItem):
    def __init__(self, s: QGraphicsScene, vb: ValveLogicBlock):
        super().__init__(s, vb)
        self.vb = vb
        self.container.setStyleSheet(self.container.styleSheet() + """
            *[valveState=true] {
                background-color: rgba(160, 191, 101, 1);
            }
            *[valveState=false] {
                background-color: rgba(191, 99, 103, 1);
            }
        """)
        self.container.setProperty("valveState", self.vb.IsOpen())
        self.container.setStyle(self.container.style())

        self.vb.OnOutputsUpdated.Register(self.ChangeColor, True)

    def ChangeColor(self):
        lastStyle = self.container.property("valveState")
        if lastStyle != self.vb.IsOpen():
            self.container.setProperty("valveState", self.vb.IsOpen())
            self.container.setStyle(self.container.style())
