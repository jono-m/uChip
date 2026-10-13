from dataclasses import dataclass, field
from typing import Dict, List, Optional
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports import comports
import serial

SOLENOIDS_PER_DEVICE = 24

@dataclass(eq=False)
class Device:
    # Saved settings
    hwid: str
    start_number: int = 0
    polarities: List[bool] = field(default_factory=lambda: [False, False, False])
    enabled: bool = False

    # Runtime state
    available: bool = False
    error: str = ""
    port_info: Optional[ListPortInfo] = None
    serial_port: Optional[serial.Serial] = None
    pin_states: List[bool] = field(default_factory=lambda: [False] * SOLENOIDS_PER_DEVICE)
    sent_bytes: List[Optional[bytes]] = field(default_factory=lambda: [None, None, None])

    def is_connected(self) -> bool:
        return self.serial_port is not None and self.serial_port.is_open

    def connect(self):
        if self.is_connected() or self.port_info is None:
            return
        try:
            self.serial_port = serial.Serial(self.port_info.device,
                                             baudrate=115200,
                                             bytesize=serial.EIGHTBITS,
                                             parity=serial.PARITY_NONE,
                                             stopbits=serial.STOPBITS_ONE,
                                             timeout=0,  # non-blocking reads or small value like 0.1
                                             write_timeout=None,  # let writes block
                                             xonxoff=False,
                                             rtscts=False,
                                             dsrdtr=False,
                                             )
        except serial.SerialException as e:
            # Disable the device so the run loop doesn't retry every tick.
            self.enabled = False
            self.error = str(e)
            return
        self.error = ""
        port = self.serial_port
        for bank in b"ABC":
            port.write(b"!" + bytes([bank, 0]))
        port.write(b"a")
        a = port.read(1)
        port.write(b"b")
        b = port.read(1)
        port.write(b"c")
        c = port.read(1)
        self.sent_bytes = [a, b, c]

    def disconnect(self):
        if self.is_connected():
            self.serial_port.close()
        self.serial_port = None

    def get_solenoid_numbers(self):
        return range(self.start_number, self.start_number + SOLENOIDS_PER_DEVICE)

    def send_solenoids(self, solenoid_states: Dict[int, bool]):
        """Writes any changed pin banks to the serial port."""
        if not self.enabled or not self.is_connected():
            return
        for i in range(SOLENOIDS_PER_DEVICE):
            number = self.start_number + i
            if number in solenoid_states:
                self.pin_states[i] = solenoid_states[number]
        for bank, command in enumerate(b"ABC"):
            pins = self.pin_states[bank * 8:(bank + 1) * 8]
            state = _pins_to_byte([pin != self.polarities[bank] for pin in pins])
            if state != self.sent_bytes[bank]:
                self.serial_port.write(bytes([command]) + state)
                self.sent_bytes[bank] = state

    def summary(self) -> str:
        info = self.port_info
        if info is None:
            return "INVALID DEVICE"
        return ("Name: {}\nDevice: {}\nSerial Number: {}\nLocation: {}\nManufacturer: {}\nProduct: {}\n"
                "Interface: {}").format(info.name, info.device, info.serial_number, info.location,
                                        info.manufacturer, info.product, info.interface)

    def get_device_saved_fields(self):
        return {key: getattr(self, key) for key in _SAVED_FIELDS}

def get_available_devices() -> List[Device]:
    ports = comports()
    return [Device(hwid=port.hwid, available=True,
                                       port_info=port) for port in ports]

def load_device_from_fields(json):
    return Device(**{key: json[key] for key in _SAVED_FIELDS if key in json})

def _pins_to_byte(pins: List[bool]) -> bytes:
    return bytes([sum(1 << i for i, pin in enumerate(pins) if pin)])

_SAVED_FIELDS = ["hwid", "start_number", "polarities", "enabled"]
