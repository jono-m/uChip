from typing import Set, Dict
import dill
from pathlib import Path
from Model.Rig.RigDevice import RigDevice
from Model.Rig.MockRigDevice import MockRigDevice


class Rig:
    def __init__(self):
        super().__init__()
        self.savedDevices: Set[RigDevice] = set()

        self.solenoidStates: Dict[int, bool] = {}

        self.Rescan()

        self.LoadDevices()

    def Rescan(self):
        foundSerialNumbers = RigDevice.Rescan()
        foundDevices = [device for device in self.savedDevices if device.IsDeviceAvailable() and device.isEnabled]
        if foundDevices:
            highestNumber = max(sum([device.startNumber for device in foundDevices], []))
        else:
            highestNumber = 0

        for foundSerialNumber in foundSerialNumbers:
            if foundSerialNumber not in [device.serialNumber for device in self.savedDevices]:
                newDevice = RigDevice(highestNumber, foundSerialNumber)
                newDevice.Connect()
                self.savedDevices.add(newDevice)
                highestNumber += 24

    def AddMock(self, start: int, serialNo: str):
        newDevice = MockRigDevice(start, serialNo)
        newDevice.Connect()
        self.savedDevices.add(newDevice)

    def SetSolenoidState(self, number: int, state: bool, flush=False):
        self.solenoidStates[number] = state
        if flush:
            self.FlushStates()

    def GetSolenoidState(self, number: int):
        if number not in self.solenoidStates:
            self.solenoidStates[number] = False
        return self.solenoidStates[number]

    def FlushStates(self):
        for device in self.savedDevices:
            if device.isConnected and device.isEnabled:
                states = [self.GetSolenoidState(i) for i in
                          range(device.startNumber, device.startNumber + len(device.solenoidPolarities))]
                device.SetStates(states)

    def SaveDevices(self):
        file = open("devices.pkl", "wb")
        dill.dump(self.savedDevices, file)
        file.close()

    def LoadDevices(self):
        if Path("devices.pkl").exists():
            file = open("devices.pkl", "rb")
            self.savedDevices = dill.load(file)
            file.close()
        else:
            self.savedDevices = set()

        for device in self.savedDevices:
            if device.IsDeviceAvailable() and device.isEnabled:
                device.Connect()
