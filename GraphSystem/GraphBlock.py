import typing
from GraphSystem.Data import Data
from enum import Enum, auto


class GraphBlock:
    def __init__(self):
        self._ports: typing.List['Port'] = []

        self._settings: typing.List[Data] = []

        self._isValid = True
        self._invalidReason = "Invalid Block!"

    def IsValid(self):
        return self._isValid

    def GetInvalidReason(self):
        return self._invalidReason

    def SetValid(self):
        self._isValid = True

    def SetInvalid(self, invalidReason: str):
        self._isValid = False
        self._invalidReason = invalidReason

    def GetPorts(self):
        return self._ports

    def AddPort(self, port: 'Port') -> 'Port':
        if port.GetBlock() is not None:
            raise PortException("Port already belongs to a block.")
        port._block = self
        self._ports.append(port)
        return port

    def RemovePort(self, port: 'Port'):
        if port.GetBlock() != self:
            raise PortException("Port does not belong to this block.")
        port._block = None
        self._ports.remove(port)

    def GetSettings(self):
        return self._settings

    def AddSetting(self, setting: Data):
        if setting not in self._settings:
            self._settings.append(setting)
        return setting

    def RemoveSetting(self, setting: Data):
        if setting in self._settings:
            self._settings.remove(setting)

    def Update(self):
        pass

    def GetName(self) -> str:
        return "Unnamed Block"


class PortClass(Enum):
    InputOutput = auto()
    BeginCompleted = auto()


class PortDirection(Enum):
    Sender = auto()
    Receiver = auto()


class PortException(Exception):
    pass


class Port:
    def __init__(self, name: str, data: Data, portDirection: PortDirection, portClass: PortClass):
        self._name = name
        self._data = data
        self._class = portClass
        self._direction = portDirection
        self._block: typing.Optional[GraphBlock] = None
        self._connectedPorts = []

    def GetConnectedPorts(self):
        return self._connectedPorts

    def IsSingleConnection(self):
        return self._class is PortClass.InputOutput and self._direction is PortDirection.Receiver

    def DisconnectAll(self):
        for port in self._connectedPorts.copy():
            self.Disconnect(self, port)

    def GetClass(self):
        return self._class

    def GetDirection(self):
        return self._direction

    def GetName(self):
        return self._name

    def SetName(self, newName: str):
        self._name = newName

    def GetBlock(self):
        return self._block

    def GetValue(self):
        return self._data.GetValue()

    def SetValue(self, value):
        self._data.SetValue(value)

    def GetDataReference(self):
        return self._data

    @staticmethod
    def CanConnect(portA: 'Port', portB: 'Port'):
        return portA.GetClass() == portB.GetClass() and portA.GetDirection() != portB.GetDirection()

    @staticmethod
    def Connect(portA: 'Port', portB: 'Port'):
        if not Port.CanConnect(portA, portB):
            raise PortException("Cannot connect ports.")

        if portA.IsSingleConnection():
            portA.DisconnectAll()

        if portB.IsSingleConnection():
            portB.DisconnectAll()

        if portA not in portB._connectedPorts:
            portB._connectedPorts.append(portA)
        if portB not in portA._connectedPorts:
            portA._connectedPorts.append(portB)

    @staticmethod
    def Disconnect(portA: 'Port', portB: 'Port'):
        if portA not in portB._connectedPorts or portB not in portA._connectedPorts:
            raise PortException("Ports are already disconnected.")

        portA._connectedPorts.remove(portB)
        portB._connectedPorts.remove(portA)
