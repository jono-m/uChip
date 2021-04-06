from BaseLogicBlock import BaseLogicBlock, InputPort, OutputPort
from BaseConnectableBlock import BaseConnectableBlock
from BlockSystem.BaseConnectableBlock import Parameter
from Util import DatatypeToName
import typing


class CompoundLogicBlock(BaseLogicBlock):
    def __init__(self):
        super().__init__()

        self._subBlocks: typing.Set[BaseConnectableBlock] = set()

        self.name = "Unnamed Compound Block"

    def GetSubBlocks(self):
        return self._subBlocks

    def IsValid(self):
        if not super().IsValid():
            return False

        return all([block.IsValid() for block in self.GetSubBlocks()])

    def GetInvalidReason(self):
        if not super().IsValid():
            return super().GetInvalidReason()

        return "Error in sub-blocks!"

    def AddSubBlock(self, newBlock: BaseConnectableBlock):
        if newBlock in self.GetSubBlocks():
            return

        if isinstance(newBlock, InputLogicBlock):
            newBlock.SetCompoundPort(self.CreateInputPort("", newBlock.dataType))
        if isinstance(newBlock, OutputLogicBlock):
            newBlock.SetCompoundPort(self.CreateOutputPort("", newBlock.dataType))

        self._subBlocks.add(newBlock)

    def RemoveSubBlock(self, block: BaseConnectableBlock):
        if block not in self._subBlocks:
            return

        if isinstance(block, InputLogicBlock) or isinstance(block, OutputLogicBlock):
            self.RemovePort(block.compoundPort)

        self._subBlocks.remove(block)

    def GetName(self):
        if self is None:
            return None
        else:
            return self.name

    def Update(self):
        super().Update()

        blocksWaitingForUpdate = self.GetSubBlocks()
        while blocksWaitingForUpdate:
            blocksReadyForUpdate = []
            for blockWaitingForUpdate in blocksWaitingForUpdate:
                if isinstance(blockWaitingForUpdate, BaseLogicBlock):
                    parentBlocks = [port.ownerBlock for port in blockWaitingForUpdate.GetInputPorts()]
                    areAllParentsUpdated = all(
                        parentBlock not in blocksWaitingForUpdate for parentBlock in parentBlocks)
                else:
                    areAllParentsUpdated = True
                if areAllParentsUpdated:
                    blocksReadyForUpdate.append(blockWaitingForUpdate)

            for blockReadyForUpdate in blocksReadyForUpdate:
                blocksWaitingForUpdate.remove(blockReadyForUpdate)
                blockReadyForUpdate.Update()


# Dummy logic block that represents an input to the compound logic block

class InputLogicBlock(BaseLogicBlock):
    def __init__(self, dataType, compoundInputPort: typing.Optional[InputPort] = None):
        super().__init__()
        self.dataType = dataType

        self.nameParameter = self.AddParameter(Parameter("Name", str, "New" + DatatypeToName(self.dataType)))
        self.output = self.CreateOutputPort("Value", self.dataType)
        self.compoundPort = compoundInputPort

    def SetCompoundPort(self, compoundPort: InputPort):
        self.compoundPort = compoundPort

    def GetName(self):
        if self is None:
            return None
        return self.nameParameter.GetValue()

    def Update(self):
        super().Update()
        if self.compoundPort is None:
            return
        self.output.SetValue(self.compoundPort.GetValue())
        self.compoundPort.name = self.nameParameter.GetValue()


class OutputLogicBlock(BaseLogicBlock):
    def __init__(self, dataType, compoundOutputPort: typing.Optional[OutputPort] = None):
        super().__init__()
        self.dataType = dataType

        self.nameParameter = self.AddParameter(Parameter("Name", str, "New" + DatatypeToName(self.dataType)))
        self.input = self.CreateInputPort("Value", self.dataType)

        self.compoundPort = compoundOutputPort

    def SetCompoundPort(self, compoundPort: OutputPort):
        self.compoundPort = compoundPort

    def Update(self):
        if self.compoundPort is None:
            return
        self.compoundPort.SetValue(self.input.GetValue())
        self.compoundPort.name = self.nameParameter.GetValue()
