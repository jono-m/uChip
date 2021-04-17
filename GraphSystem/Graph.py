from GraphSystem.GraphBlock import Port, GraphBlock, PortDirection
from GraphSystem.Data import Data
import typing


class Graph:
    def __init__(self):
        self._inputs: typing.Dict[str, Data] = {}
        self._outputs: typing.Dict[str, Data] = {}
        self._blocks: typing.List[GraphBlock] = []

    def GetOutputs(self):
        return self._outputs

    def GetInputs(self):
        return self._inputs

    def AddInput(self, name: str, inputData: Data):
        self._inputs[name] = inputData

    def RemoveInput(self, name: str):
        self._inputs.pop(name, None)

    def GetBlocks(self):
        return self._blocks

    def UpdateBlocks(self):
        blocksWaitingForUpdate = self.GetBlocks()
        while blocksWaitingForUpdate:
            blocksReadyForUpdate = []
            for blockWaitingForUpdate in blocksWaitingForUpdate:
                parentBlocks = [port. for port in blockWaitingForUpdate.GetPorts() if
                                port.GetDirection() is PortDirection.Receiver]
                areAllParentsUpdated = all([parentBlock not in blocksWaitingForUpdate for parentBlock in parentBlocks])
                if areAllParentsUpdated:
                    blocksReadyForUpdate.append(blockWaitingForUpdate)

            for blockReadyForUpdate in blocksReadyForUpdate:
                blocksWaitingForUpdate.remove(blockReadyForUpdate)
                blockReadyForUpdate.Update()
