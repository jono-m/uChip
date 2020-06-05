import serial
import serial.tools.list_ports
import typing
from serial.tools.list_ports_common import ListPortInfo


class Device:
    def __init__(self, portInfo: typing.Optional[ListPortInfo] = None):
        super().__init__()
        self.portInfo = portInfo

        self.ser = None

    def Connect(self):
        self.ser = serial.Serial(self.portInfo.device)
        self.ser.write_timeout = 5.0
        self.InitializeDevice()

    def Disconnect(self):
        if self.ser is None:
            return
        self.ser.close()

    def InitializeDevice(self):
        if self.ser is not None:
            self.ser.write(b'!A' + bytes([0]))
            self.ser.write(b'!B' + bytes([0]))
            self.ser.write(b'!C' + bytes([0]))

    def Flush(self, solenoidStates: typing.List[bool]):
        if self.ser is not None:
            aState = solenoidStates[0:8]
            bState = solenoidStates[8:16]
            cState = solenoidStates[16:24]
            self.ser.write(b'A' + self.StateToByte(aState))
            self.ser.write(b'B' + self.StateToByte(bState))
            self.ser.write(b'C' + self.StateToByte(cState))

    def __eq__(self, other):
        return self.portInfo.serial_number == other.portInfo.serial_number

    @staticmethod
    def StateToByte(state):
        number = 0
        for i in range(8):
            if state[i]:
                number += 1 << i
        return bytes([number])

    @staticmethod
    def FindConnectedDevices() -> typing.List[ListPortInfo]:
        foundDevices = []

        ports = serial.tools.list_ports.comports()

        for port in ports:
            if type(port.serial_number) == str:
                if len(port.serial_number) >= 2:
                    if port.serial_number[:2] == 'EL':
                        foundDevices.append(port)
            else:
                if type(port.manufacturer) == str:
                    if port.manufacturer == 'Electronic Team':
                        if int(port.device[3]) % 2 == 0:
                            port.serial_number = port.description
                            foundDevices.append(port)

        return foundDevices
