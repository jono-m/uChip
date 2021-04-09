import typing
from BlockSystem.LogicBlocks import OutputLogicBlock
from ProjectSystem.Project import Project
from ProjectSystem.BlockSystemEntity import BlockSystemEntity
from BlockSystem.DataPorts import InputPort
from BlockSystem.Data import Data


class BlockSystemProject(Project):
    def __init__(self):
        super().__init__()

        self._inputs: typing.List[Data] = []
        self._settings: typing.List[Data] = []

    def GetOutputs(self):
        return [block.GetOutput() for block in self.GetProjectBlocks() if
                isinstance(block, OutputLogicBlock)]

    def GetInputs(self):
        return self._inputs

    def GetSettings(self):
        return self._settings

    def AddInput(self, input: Data):
        if input not in self._inputs:
            self._inputs.append(input)
        return input

    def RemoveInput(self, input: Data):
        if input in self._inputs:
            self._inputs.remove(input)

    def AddSetting(self, setting: Data):
        if setting not in self._settings:
            self._settings.append(setting)
        return setting

    def RemoveSetting(self, setting: Data):
        if setting in self._settings:
            self._settings.remove(setting)

    def GetProjectBlocks(self):
        return [entity.GetBlock() for entity in self.GetEntities() if isinstance(entity, BlockSystemEntity)]

    def UpdateBlocks(self):
        blocksWaitingForUpdate = self.GetProjectBlocks()
        while blocksWaitingForUpdate:
            blocksReadyForUpdate = []
            for blockWaitingForUpdate in blocksWaitingForUpdate:
                parentBlocks = [port.GetOwnerBlock() for port in blockWaitingForUpdate.GetPorts(InputPort)]
                areAllParentsUpdated = all([parentBlock not in blocksWaitingForUpdate for parentBlock in parentBlocks])
                if areAllParentsUpdated:
                    blocksReadyForUpdate.append(blockWaitingForUpdate)

            for blockReadyForUpdate in blocksReadyForUpdate:
                blocksWaitingForUpdate.remove(blockReadyForUpdate)
                blockReadyForUpdate.Update()
