import typing
import dill
from pathlib import Path


class Rig:
    def __init__(self, deviceTypesToScan: typing.List[typing.Type['Rig.RigDevice']]):
        super().__init__()
        self._devices: typing.List[Rig.RigDevice] = []

        self._deviceTypesToScan = deviceTypesToScan

        self._solenoidStates = []

        self.LoadDevices()

        self.Rescan()

    def Rescan(self):
        for deviceType in self._deviceTypesToScan:
            [self.AddDevice(device) for device in deviceType.SearchForDevices()]
        for device in self._devices:
            if device.IsActive():
                device.TryConnect()

    def AddDevice(self, device: 'Rig.RigDevice'):
        if device not in self._devices:
            self._devices.append(device)

    def RemoveDevice(self, device: 'Rig.RigDevice'):
        if device in self._devices:
            self._devices.remove(device)

    def SetSolenoidState(self, number: int, state: bool):
        if number < 0:
            return
        if number >= len(self._solenoidStates):
            self._solenoidStates += [False] * (number - len(self._solenoidStates) + 1)
            self._solenoidStates[-1] = state
            self.Flush()
            return

        if self._solenoidStates[number] != state:
            self._solenoidStates[number] = state
            self.Flush()

    def GetDevices(self):
        return self._devices

    def Promote(self, device: 'Rig.RigDevice', other: 'Rig.RigDevice'):
        self._devices.remove(device)
        index = self._devices.index(other)
        self._devices.insert(index + 1, device)
        self.Flush()

    def Demote(self, device: 'Rig.RigDevice', other: 'Rig.RigDevice'):
        self._devices.remove(device)
        index = self._devices.index(other)
        self._devices.insert(index, device)
        self.Flush()

    def Flush(self):
        index = 0
        for device in self.GetDevices():
            if device.IsActive():
                device.SetStates(self._solenoidStates[index:(index + device.GetNumSolenoids())])
                index += device.GetNumSolenoids()

    def SaveDevices(self):
        file = open("devices.pkl", "wb")
        dill.dump(self._devices, file)
        file.close()

    def LoadDevices(self):
        if Path("devices.pkl").exists():
            file = open("devices.pkl", "rb")
            self._devices = dill.load(file)
            file.close()
        else:
            self._devices = []

    class RigDevice:
        class DeviceError(Exception):
            pass

        def __init__(self):
            self._isConnected = False
            self._solenoidStates = [False] * self.GetNumSolenoids()

            self.editableProperties: typing.Dict[str, typing.Any] = {'isActive': False}

        def IsActive(self):
            return self.editableProperties['isActive']

        @staticmethod
        def GetNumSolenoids():
            return 0

        def SetStates(self, solenoidStates: typing.List[bool]):
            if solenoidStates != self._solenoidStates[:len(solenoidStates)]:
                self._solenoidStates[:len(solenoidStates)] = solenoidStates
                if self.IsConnected():
                    self.FlushStates()

        def SetSolenoid(self, number: int, state: bool):
            if 0 <= number < self.GetNumSolenoids():
                if self._solenoidStates[number] != state:
                    self._solenoidStates[number] = state
                    if self.IsConnected():
                        self.FlushStates()

        def IsSameDevice(self, other: 'Rig.RigDevice'):
            return True

        def IsDeviceAvailable(self) -> bool:
            return False

        def __eq__(self, other):
            return self.IsSameDevice(other)

        def FlushStates(self):
            pass

        def GetSolenoidStates(self):
            return self._solenoidStates

        def __getstate__(self):
            self.Disconnect()
            return self.__dict__

        def IsConnected(self):
            return self._isConnected

        def TryConnect(self):
            if self.IsDeviceAvailable():
                if not self.IsConnected():
                    self.Connect()
                    self.FlushStates()
            else:
                self._isConnected = False

        def TryDisconnect(self):
            if self.IsConnected():
                self.Disconnect()

        def Connect(self):
            self._isConnected = True

        def Disconnect(self):
            self._isConnected = False

        def GetName(self):
            return "Unknown Device"

        @staticmethod
        def SearchForDevices() -> typing.List['Rig.RigDevice']:
            return []
