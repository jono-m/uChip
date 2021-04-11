from BaseConnectableBlock import BaseConnectableBlock
from Steps import StartStep
import typing


class Procedure:
    def __init__(self, startStep: StartStep):
        self._blocks: typing.List[BaseConnectableBlock] = [startStep]

    def GetBlocks(self):
        return self._blocksu
