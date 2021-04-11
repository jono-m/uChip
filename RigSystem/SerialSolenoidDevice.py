from serial import Serial
from serial.tools import list_ports
from RigSystem.Rig import Rig
import typing
from serial.tools.list_ports_common import ListPortInfo


class SerialSolenoidDevice(Rig.RigDevice):
    lastScannedPorts: typing.List[ListPortInfo] = []

    def __init__(self, serialNumber: str):
        super().__init__()

        self._serialNumber = serialNumber
        self._serialPort: typing.Optional[Serial] = None

    def Connect(self):
        super().Connect()
        self._serialPort = Serial([port.device for port in SerialSolenoidDevice.lastScannedPorts])

    def Write(self, data: bytes):
        if self.IsConnected():
            self._serialPort.write(data)

    def Disconnect(self):
        super().Disconnect()
        self._serialPort.close()

    def IsDeviceAvailable(self) -> bool:
        return self._serialNumber in [port.serial_number for port in SerialSolenoidDevice.lastScannedPorts]

    def IsSameDevice(self, other: 'Rig.RigDevice'):
        return isinstance(other, SerialSolenoidDevice) and self._serialNumber == other._serialNumber

    def GetName(self):
        return "Unknown Serial Device"

    @staticmethod
    def SearchForDevices() -> typing.List['Rig.RigDevice']:
        SerialSolenoidDevice.lastScannedPorts = list_ports.comports()

        return [SerialSolenoidDevice(port.serial_number) for port in SerialSolenoidDevice.lastScannedPorts if
                isinstance(port.serial_number, str)]
