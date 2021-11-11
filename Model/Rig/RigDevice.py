from typing import List, Optional
from serial import Serial
from serial.tools.list_ports_common import ListPortInfo


class RigDevice:
    def __init__(self):
        self.serialNumber = "None"
        self.startNumber = 0
        self.polarities = [False, False, False]
        self.enabled = False

        self.livePortInfo: Optional[ListPortInfo] = None
        self._serialPort: Optional[Serial] = None

        self.errorMessage = ""

    def IsAvailable(self):
        return self.livePortInfo is not None

    def IsActive(self):
        return self.enabled and self._serialPort is not None and self._serialPort.is_open

    def __getstate__(self):
        state = self.__dict__
        del state["_serialPort"]
        del state["livePortInfo"]
        del state["errorMessage"]
        return state

    def __setstate__(self, state):
        state["_serialPort"] = None
        state["livePortInfo"] = None
        state["errorMessage"] = ""
        self.__dict__ = state

    @staticmethod
    def _StateToByte(state):
        number = 0
        for i in range(8):
            if state[i]:
                number += 1 << i
        return bytes([number])

    def _Write(self, data: bytes):
        if self._serialPort:
            try:
                self._serialPort.write(data)
            except Exception as e:
                self.ReportError("Could not write to device. Error: \n" + str(e))

    def SetStates(self, solenoidStates: List[bool]):
        solenoidStates = [state != self.polarities[int(i / 8)] for (i, state) in enumerate(solenoidStates)]
        aState = solenoidStates[0:8]
        bState = solenoidStates[8:16]
        cState = solenoidStates[16:24]
        self._Write(b'A' + self._StateToByte(aState))
        self._Write(b'B' + self._StateToByte(bState))
        self._Write(b'C' + self._StateToByte(cState))

    def Connect(self):
        try:
            self._serialPort = Serial(self.livePortInfo.device)
        except Exception as e:
            self.ReportError("Could not connect to " + self.livePortInfo.device + ". Error:\n" + str(e))

        self._Write(b'!A' + bytes([0]))
        self._Write(b'!B' + bytes([0]))
        self._Write(b'!C' + bytes([0]))

    def Disconnect(self):
        if self._serialPort is not None and self._serialPort.is_open:
            self._serialPort.close()
        self._serialPort = None

    def ReportError(self, error, fatal=True):
        if fatal:
            self.Disconnect()
        raise DeviceError(self, error)


class DeviceError(Exception):
    def __init__(self, device: RigDevice, *args):
        super().__init__(*args)

        self.device = device

        device.errorMessage = str(self)
