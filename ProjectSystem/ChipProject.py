from ProjectSystem.BlockSystemProject import BlockSystemProject
from ProjectSystem.BlockSystemEntity import BlockSystemEntity
from BlockSystem.ValveLogicBlock import ValveLogicBlock
from RigSystem.Rig import Rig


class ChipProject(BlockSystemProject):
    def __init__(self):
        super().__init__()

    def GetValveBlocks(self):
        return [block for block in
                [entity.GetBlock() for entity in self.GetEntities() if isinstance(entity, BlockSystemEntity)] if
                isinstance(block, ValveLogicBlock)]

    def SendToRig(self, rig: Rig):
        rig.drivenSolenoids = []
        for valveBlock in self.GetValveBlocks():
            rig.SetSolenoid(valveBlock.solenoidNumberInput.GetValue(), valveBlock.openInput.GetValue())
            rig.drivenSolenoids.append(valveBlock.solenoidNumberInput.GetValue())
        rig.Flush()
