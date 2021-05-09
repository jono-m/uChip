from typing import Optional

from PySide6.QtCore import QPointF
from Program import Program
from ProgramInstanceState import ProgramInstanceState
from enum import Enum, auto


class GraphBlock(Program):
    def __init__(self, name="Graph Block", position=QPointF()):
        super().__init__(name)
        self._position = position

        self._beginPorts = []
        self._completedPorts = []

    def GetPosition(self):
        return self._position

    def SetPosition(self, position: QPointF):
        self._position = position

    def GetBeginPorts(self):
        return self._beginPorts

    def GetCompletedPorts(self):
        return self._completedPorts

    def GetNextPort(self, state: ProgramInstanceState) -> Optional['StepPort']:
        if self._completedPorts:
            return self._completedPorts[-1]

    def AddBeginPort(self, name: str):
        self._beginPorts.append(StepPort(StepPort.PortType.BEGIN, name, self))
        return self._beginPorts[-1]

    def AddCompletedPort(self, name: str):
        self._completedPorts.append(StepPort(StepPort.PortType.COMPLETED, name, self))
        return self._completedPorts[-1]

    def RemovePort(self, port: 'StepPort'):
        if port in self._beginPorts:
            self._beginPorts.remove(port)
        if port in self._completedPorts:
            self._completedPorts.remove(port)


class StepPort:
    class PortType(Enum):
        BEGIN = auto()
        COMPLETED = auto()

    def __init__(self, portType: 'StepPort.PortType', name, block: GraphBlock):
        self._name = name
        self._portType = portType
        self._block = block

    def GetBlock(self):
        return self._block

    def GetName(self):
        return self._name

    def SetName(self, name: str):
        self._name = name

    def GetPortType(self):
        return self._portType

    def IsCompatible(self, other: 'StepPort'):
        return self._portType != other._portType
