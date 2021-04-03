from ProjectEntity import ProjectEntity
from BlockSystem.BaseConnectableBlock import BaseConnectableBlock


class BlockSystemEntity(ProjectEntity):
    def __init__(self, block: BaseConnectableBlock):
        super().__init__()
        self.block = block
