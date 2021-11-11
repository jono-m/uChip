from typing import Set, Dict, Optional
import dill
from pathlib import Path
from Model.Rig.RigDevice import RigDevice
from serial.tools.list_ports import comports


class Rig:
    def __init__(self):
        super().__init__()
        self.allDevices: Set[RigDevice] = set()

        self.solenoidStates: Dict[int, bool] = {}

        self.LoadDevices()

        self.RescanPorts()

        self.FlushStates()

    def RescanPorts(self):
        foundDevices = comports()

        for device in self.allDevices:
            matches = [foundDevice for foundDevice in foundDevices if foundDevice.serial_number == device.serialNumber]
            if len(matches) > 0:
                device.livePortInfo = matches[0]
                foundDevices.remove(matches[0])
            else:
                device.livePortInfo = None
                device.Disconnect()

        for foundDevice in foundDevices:
            newDevice = RigDevice()
            newDevice.livePortInfo = foundDevice
            newDevice.serialNumber = foundDevice.serial_number
            self.allDevices.add(newDevice)

        [device.Connect() for device in self.GetActiveDevices()]

    def SetSolenoidState(self, number: int, state: bool, flush=False):
        self.solenoidStates[number] = state
        if flush:
            self.FlushStates()

    def GetSolenoidState(self, number: int):
        if number not in self.solenoidStates:
            self.solenoidStates[number] = False
        return self.solenoidStates[number]

    def GetActiveDevices(self):
        return [device for device in self.allDevices if device.IsActive()]

    def GetAvailableDevices(self):
        return [device for device in self.allDevices if device.livePortInfo is not None]

    def FlushStates(self):
        for device in self.GetActiveDevices():
            states = [self.GetSolenoidState(i) for i in
                      range(device.startNumber, device.startNumber + 24)]
            device.SetStates(states)

    def SaveDevices(self):
        file = open("devices.pkl", "wb")
        dill.dump((self.allDevices, self.solenoidStates), file)
        file.close()

    def LoadDevices(self):
        if Path("devices.pkl").exists():
            file = open("devices.pkl", "rb")
            try:
                self.allDevices, self.solenoidStates = dill.load(file)
            except Exception as e:
                print("Error loading device: " + str(e))
                self.allDevices, self.solenoidStates = (set(), {})
            file.close()
        else:
            self.allDevices = set()
            self.solenoidStates = {}
