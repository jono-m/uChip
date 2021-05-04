from SerialSolenoidDevice import SerialSolenoidDevice
from Rig import Rig
import typing


class ElexolSerialDevice(SerialSolenoidDevice):
    def __init__(self, serialNumber: str):
        super().__init__(serialNumber)

        self.editableProperties['Invert A'] = False
        self.editableProperties['Invert B'] = False
        self.editableProperties['Invert C'] = False

    def Connect(self):
        super().Connect()
        self.Write(b'!A' + bytes([0]))
        self.Write(b'!B' + bytes([0]))
        self.Write(b'!C' + bytes([0]))

    def GetNumSolenoids(self):
        return 24

    def FlushStates(self):
        super().FlushStates()
        solenoidStates = self.GetSolenoidStates()
        aState = [state != self.editableProperties['Invert A'] for state in solenoidStates[0:8]]
        bState = [state != self.editableProperties['Invert B'] for state in solenoidStates[8:16]]
        cState = [state != self.editableProperties['Invert C'] for state in solenoidStates[16:24]]
        self.Write(b'A' + self.StateToByte(aState))
        self.Write(b'B' + self.StateToByte(bState))
        self.Write(b'C' + self.StateToByte(cState))

    @staticmethod
    def StateToByte(state):
        number = 0
        for i in range(8):
            if state[i]:
                number += 1 << i
        return bytes([number])

    @staticmethod
    def SearchForDevices() -> typing.List['Rig.RigDevice']:
        super().SearchForDevices()
        return [ElexolSerialDevice(device.serial_number) for device in SerialSolenoidDevice.lastScannedPorts if
                device.manufacturer == "Elexol"]
