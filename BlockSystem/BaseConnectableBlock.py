import typing
from BlockSystem.Data import Data


class BaseConnectableBlock:
    _T = typing.TypeVar('_T', bound='BaseConnectableBlock.Port')

    def __init__(self):
        self._ports: typing.List[BaseConnectableBlock.Port] = []

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

    def GetPorts(self, portType: typing.Type[_T] = None):
        if portType is None:
            return self._ports
        return [port for port in self._ports if isinstance(port, portType)]

    def AddPort(self, port: _T) -> _T:
        if port.GetOwnerBlock() is None:
            port._ownerBlock = self
            self._ports.append(port)
        return port

    def RemovePort(self, port: 'BaseConnectableBlock.Port'):
        if port.GetOwnerBlock() == self:
            port._ownerBlock = None
            self._ports.remove(port)
            port.DisconnectAll()

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

    def DisconnectAll(self):
        for port in self._ports:
            port.DisconnectAll()

    def GetName(self) -> str:
        return "Unnamed Block"

    class Port:
        def __init__(self):
            self._ownerBlock: typing.Optional[BaseConnectableBlock] = None
            self._connectedPorts: typing.List['BaseConnectableBlock.Port'] = []

        def GetConnectedPorts(self):
            return self._connectedPorts

        def GetOwnerBlock(self):
            return self._ownerBlock

        def CanConnect(self, port: 'BaseConnectableBlock.Port'):
            return port is not None and self._ownerBlock is not None and port._ownerBlock is not None \
                   and self._ownerBlock.IsValid() and port._ownerBlock.IsValid()

        def Connect(self, port: 'BaseConnectableBlock.Port'):
            if not self.CanConnect(port):
                return

            if port not in self._connectedPorts:
                if self not in port._connectedPorts:
                    port._connectedPorts.append(port)
                self._connectedPorts.append(port)

        def Disconnect(self, port: 'BaseConnectableBlock.Port'):
            self._connectedPorts.remove(port)
            port._connectedPorts.remove(self)

        def DisconnectAll(self):
            for port in self.GetConnectedPorts().copy():
                self.Disconnect(port)
