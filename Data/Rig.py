from typing import Dict
from serial.tools.list_ports import comports
from typing import List, Optional
from serial import Serial
from serial.tools.list_ports_common import ListPortInfo


class Rig:
    def __init__(self):
        super().__init__()
        self.solenoidStates: Dict[int, bool] = {}

    def SetSolenoidState(self, number: int, state: bool):
        self.solenoidStates[number] = state

    def GetSolenoidState(self, number: int):
        if number not in self.solenoidStates:
            self.solenoidStates[number] = False
        return self.solenoidStates[number]


class Device:
    def __init__(self):
        self.portInfo: Optional[ListPortInfo] = None
        self.startNumber = 0
        self.polarities = [False, False, False]
        self.enabled = False
        self.serialPort: Optional[Serial] = None

    def IsConnected(self):
        return self.serialPort is not None and self.serialPort.is_open

    def SetPinStates(self, solenoidStates: List[bool]):
        if not self.IsConnected():
            return
        polarizedStates = [state != self.polarities[int(i / 8)] for (i, state) in
                           enumerate(solenoidStates)]
        aState = ConvertPinStatesToBytes(polarizedStates[0:8])
        bState = ConvertPinStatesToBytes(polarizedStates[8:16])
        cState = ConvertPinStatesToBytes(polarizedStates[16:24])
        self.serialPort.write(b'A' + aState)
        self.serialPort.write(b'B' + bState)
        self.serialPort.write(b'C' + cState)

    def Connect(self):
        if self.IsConnected():
            return
        self.serialPort = Serial(self.portInfo.device, timeout=0, writeTimeout=0)
        self.serialPort.write(b'!A' + bytes([0]))
        self.serialPort.write(b'!B' + bytes([0]))
        self.serialPort.write(b'!C' + bytes([0]))

    def Disconnect(self):
        if self.IsConnected():
            self.serialPort.close()
            self.serialPort = None


def ConvertPinStatesToBytes(state: List[bool]):
    number = 0
    for i in range(8):
        if state[i]:
            number += 1 << i
    return bytes([number])


def RescanPorts():
    foundDevices = comports()
    return foundDevices


def UpdateDevicesFromRig(rig: Rig, devices: List[Device]):
    for device in devices:
        if device.enabled and device.IsConnected():
            device.SetPinStates([rig.GetSolenoidState(i) for i in
                                 range(device.startNumber, device.startNumber + 24)])
