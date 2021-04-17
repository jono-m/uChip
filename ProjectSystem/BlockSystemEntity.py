from ProjectEntity import ProjectEntity
from GraphSystem.BaseConnectableBlock import GraphBlock


class BlockSystemEntity(ProjectEntity):
    def __init__(self, block: GraphBlock):
        super().__init__()
        self._block = block

    def GetBlock(self) -> GraphBlock:
        return self._block

    def SetBlock(self, block: GraphBlock):
        self._block = block

    def OnEntityRemoved(self):
        self._block.DisconnectAll()
