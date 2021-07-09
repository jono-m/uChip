from typing import List, Optional
from serial import Serial
from serial.tools import list_ports

from serial.tools.list_ports_common import ListPortInfo


class RigDevice:
    lastScannedPorts: List[ListPortInfo] = []

    def __init__(self, startNumber, serialNumber: str):
        self.isConnected = False
        self.isEnabled = True
        self.solenoidPolarities = [False] * 24
        self.startNumber = startNumber
        self.serialNumber = serialNumber
        self.serialPort: Optional[Serial] = None

        self.errorMessage = ""

    def SetEnabled(self, enabled: bool):
        self.isEnabled = enabled
        if self.isConnected and not self.isEnabled:
            self.Disconnect()
        if not self.isConnected and self.isEnabled:
            self.Connect()

    @staticmethod
    def StateToByte(state):
        number = 0
        for i in range(8):
            if state[i]:
                number += 1 << i
        return bytes([number])

    def Write(self, data: bytes):
        if self.isConnected:
            try:
                self.serialPort.write(data)
            except Exception as e:
                self.isConnected = False
                if self.serialPort.is_open:
                    self.serialPort.close()
                raise DeviceError(self, "Could not write to device " + self.GetName() + ". Error: \n" + str(e))

    def SetStates(self, solenoidStates: List[bool]):
        solenoidStates = [solenoidStates[i] != self.solenoidPolarities[i] for i in range(24)]
        aState = solenoidStates[0:8]
        bState = solenoidStates[8:16]
        cState = solenoidStates[16:24]
        self.Write(b'A' + self.StateToByte(aState))
        self.Write(b'B' + self.StateToByte(bState))
        self.Write(b'C' + self.StateToByte(cState))

    def IsDeviceAvailable(self) -> bool:
        return self.serialNumber in [port.serial_number for port in self.lastScannedPorts]

    def __getstate__(self):
        myDict = self.__dict__.copy()
        del myDict["serialPort"]
        myDict["isConnected"] = False
        return myDict

    def __setstate__(self, state):
        state["serialPort"] = None
        self.__dict__ = state

    def Connect(self):
        if not self.IsDeviceAvailable():
            raise DeviceError(self, "Could not find device " + self.GetName())

        if self.isConnected:
            return

        try:
            self.serialPort = Serial(
                [port.device for port in self.lastScannedPorts if port.serial_number == self.serialNumber][0])
        except Exception as e:
            self.isConnected = False
            raise DeviceError(self, "Could not connect to " + self.GetName() + ". Error:\n" + str(e))

        self.isConnected = True
        self.Write(b'!A' + bytes([0]))
        self.Write(b'!B' + bytes([0]))
        self.Write(b'!C' + bytes([0]))

    def Disconnect(self):
        if self.isConnected and self.serialPort.isOpen():
            self.serialPort.close()
        self.isConnected = False

    def GetName(self):
        return "Elexol Device: " + self.serialNumber

    @staticmethod
    def Rescan() -> List[str]:
        RigDevice.lastScannedPorts = list_ports.comports()

        return [port.serial_number for port in RigDevice.lastScannedPorts if
                isinstance(port.serial_number, str) and port.serial_number[:3] == "ELX"]


class DeviceError(Exception):
    def __init__(self, device: RigDevice, *args):
        super().__init__(*args)

        self.device = device

        device.errorMessage = str(self)
