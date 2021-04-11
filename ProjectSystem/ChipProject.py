from ProjectSystem.Project import Project
from BlockSystem.LogicBlocks import ValveLogicBlock
from RigSystem.Rig import Rig


class ChipProject(Project):
    def __init__(self):
        super().__init__()

    def GetValveBlocks(self):
        return [block for block in self.GetProjectBlocks() if isinstance(block, ValveLogicBlock)]

    def SendToRig(self, rig: Rig):
        for valveBlock in self.GetValveBlocks():
            rig.SetSolenoidState(valveBlock.solenoidNumberInput.GetValue(), valveBlock.openInput.GetValue())
        rig.Flush()
