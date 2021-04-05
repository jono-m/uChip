from ProjectEntity import ProjectEntity
from BlockSystem.BaseConnectableBlock import BaseConnectableBlock


class BlockSystemEntity(ProjectEntity):
    def __init__(self, block: BaseConnectableBlock):
        super().__init__()
        self._block = block

    def GetBlock(self) -> BaseConnectableBlock:
        self.UpdateEntity()
        return self._block

    def SetBlock(self, block: BaseConnectableBlock):
        self._block = block
