from typing import Dict
from serial.tools.list_ports import comports
from typing import List, Optional
from serial import Serial
from serial.tools.list_ports_common import ListPortInfo


class Rig:
    def __init__(self):
        super().__init__()
        self.solenoidStates: Dict[int, bool] = {}


class DeviceSpecification:
    def __init__(self):
        self.portInfo: Optional[ListPortInfo] = None
        self.startNumber = 0
        self.polarities = [False, False, False]
        self.enabled = False
        self.serialPort: Optional[Serial] = None


def IsDeviceConnected(device: DeviceSpecification):
    return device.serialPort is not None and device.serialPort.is_open


def ConvertPinStatesToBytes(state: List[bool]):
    number = 0
    for i in range(8):
        if state[i]:
            number += 1 << i
    return bytes([number])


def SetPinStates(device: DeviceSpecification, solenoidStates: List[bool]):
    if not IsDeviceConnected(device):
        return
    polarizedStates = [state != device.polarities[int(i / 8)] for (i, state) in
                       enumerate(solenoidStates)]
    aState = ConvertPinStatesToBytes(polarizedStates[0:8])
    bState = ConvertPinStatesToBytes(polarizedStates[8:16])
    cState = ConvertPinStatesToBytes(polarizedStates[16:24])
    device.serialPort.write(b'A' + aState)
    device.serialPort.write(b'B' + bState)
    device.serialPort.write(b'C' + cState)


def ConnectDevice(device: DeviceSpecification):
    if IsDeviceConnected(device):
        return
    device.serialPort = Serial(device.portInfo.device, timeout=0, writeTimeout=0)
    device.serialPort.write(b'!A' + bytes([0]))
    device.serialPort.write(b'!B' + bytes([0]))
    device.serialPort.write(b'!C' + bytes([0]))


def DisconnectDevice(device: DeviceSpecification):
    if IsDeviceConnected(device):
        device.serialPort.close()
        device.serialPort = None


def RescanPorts():
    foundDevices = comports()
    return foundDevices


def SetSolenoidState(rig: Rig, number: int, state: bool):
    rig.solenoidStates[number] = state


def GetSolenoidState(rig: Rig, number: int):
    if number not in rig.solenoidStates:
        rig.solenoidStates[number] = False
    return rig.solenoidStates[number]


def UpdateDevicesFromSolenoidStates(rig: Rig, devices: List[DeviceSpecification]):
    for device in devices:
        if device.enabled and IsDeviceConnected(device):
            SetPinStates(device, [GetSolenoidState(rig, i) for i in
                                  range(device.startNumber, device.startNumber + 24)])
