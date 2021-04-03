from BlockSystem.Procedure import Procedure
from BlockSystem.BaseLogicBlock import BaseLogicBlock
from BlockSystem.CompoundLogicBlock import CompoundLogicBlock
from BlockSystem.ValveLogicBlock import ValveLogicBlock
from RigSystem.Rig import Rig
import typing


class Chip(CompoundLogicBlock):
    def __init__(self):
        super().__init__()
        self._procedures: typing.List[Procedure] = []
        self._valveBlocks: typing.List[ValveLogicBlock] = []

    def GetProcedures(self):
        return self._procedures

    def AddProcedure(self, procedure: Procedure):
        if procedure not in self._procedures:
            self._procedures.append(procedure)

    def RemoveProcedure(self, procedure: Procedure):
        self._procedures.remove(procedure)

    def AddSubBlock(self, newBlock: BaseLogicBlock):
        super().AddSubBlock(newBlock)
        if isinstance(newBlock, ValveLogicBlock):
            if newBlock not in self._valveBlocks:
                self._valveBlocks.append(newBlock)

    def RemoveSubBlock(self, block: 'BaseLogicBlock'):
        if isinstance(block, ValveLogicBlock):
            self._valveBlocks.remove(block)

    def SendToRig(self, rig: Rig):
        rig.drivenSolenoids = []
        for valveBlock in self._valveBlocks:
            rig.SetSolenoid(int(valveBlock.solenoidNumber.GetValue()), valveBlock.openInput.GetValue())
            rig.drivenSolenoids.append(valveBlock.solenoidNumber.GetValue())
        rig.Flush()
