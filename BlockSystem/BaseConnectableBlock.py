import typing

ParameterTypeSpec = typing.Union[typing.Type, typing.List]


class BaseConnectableBlock:
    def __init__(self):
        self._ports: typing.List[Port] = []

        self._parameters: typing.List[Parameter] = []

        self._isValid = True
        self._invalidReason = "Invalid Block!"

    def IsValid(self):
        return self._isValid

    def GetInvalidReason(self):
        return self._invalidReason

    def SetValid(self):
        self._isValid = True

    def SetInvalid(self, invalidReason: str):
        self._invalidReason = invalidReason

    def GetPorts(self):
        return self._ports

    def AddPorts(self, ports: typing.List['Port']):
        for port in ports:
            self.AddPort(port)

    def AddPort(self, port: 'Port'):
        port.ownerBlock = self
        if port not in self._ports:
            self._ports.append(port)
        return port

    def RemovePort(self, port: 'Port'):
        port.DisconnectAll()
        port.ownerBlock = None
        self._ports.remove(port)

    def GetParameters(self):
        return self._parameters

    def CreateParameter(self, name: str, dataType: ParameterTypeSpec, initialValue=None):
        return self.AddParameter(Parameter(name, dataType, initialValue))

    def AddParameter(self, parameter: 'Parameter'):
        if parameter not in self._parameters:
            self._parameters.append(parameter)
        return parameter

    def RemoveParameter(self, parameter: 'Parameter'):
        self._parameters.remove(parameter)

    def Update(self):
        pass

    def DisconnectAll(self):
        for port in self._ports:
            port.DisconnectAll()

    def GetName(self) -> str:
        return "Unnamed Block"


class Parameter:
    def __init__(self, name: str, dataType: ParameterTypeSpec, initialValue=None):
        self.name = name
        self.dataType = dataType
        if type(self.dataType) == list:
            self._value = 0
        else:
            self._value = dataType()

        if initialValue is not None:
            self.SetValue(initialValue)

    def GetValue(self):
        return self._value

    def SetValue(self, value):
        if type(self.dataType) == list:
            self._value = max(0, min(len(self.dataType) - 1, int(value)))
        else:
            self._value = self.dataType(value)


class Port:
    def __init__(self, name: str):
        self.name: str = name
        self.ownerBlock: typing.Optional[BaseConnectableBlock] = None
        self._connectedPorts: typing.List['Port'] = []

    def GetConnectedPorts(self):
        return self._connectedPorts

    def CanConnect(self, port: 'Port'):
        return port is not None and self.ownerBlock is not None and port.ownerBlock is not None \
               and self.ownerBlock.IsValid() and port.ownerBlock.IsValid()

    def Connect(self, port: 'Port'):
        if not self.CanConnect(port):
            return

        if port not in self._connectedPorts:
            if self not in port._connectedPorts:
                port._connectedPorts.append(port)
            self._connectedPorts.append(port)

    def Disconnect(self, port: 'Port'):
        self._connectedPorts.remove(port)
        port._connectedPorts.remove(self)

    def DisconnectAll(self):
        for port in self.GetConnectedPorts().copy():
            self.Disconnect(port)
