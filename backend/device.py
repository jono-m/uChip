"""A serial solenoid-driver device: 24 solenoids in three 8-pin banks (A, B, C).

Protocol: "!", a bank letter and a zero byte sets a bank up on connecting; a bank letter (A, B or C) and
a byte sets that bank's 8 pins.
"""
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
    current_state: List[Optional[bytes]] = field(default_factory=lambda: [None, None, None])

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
        for bank in b"ABC":
            self.serial_port.write(b"!" + bytes([bank, 0]))
        self.current_state = [None, None, None]

    def disconnect(self):
        if self.is_connected():
            self.serial_port.close()
        self.serial_port = None

    def update_connection_state(self):
        if self.enabled and self.available and not self.is_connected():
            self.connect()
        elif not self.enabled and self.is_connected():
            self.disconnect()

    def get_solenoid_numbers(self):
        return range(self.start_number, self.start_number + SOLENOIDS_PER_DEVICE)

    def send_solenoids(self, solenoid_states: Dict[int, bool]):
        """Writes any changed pin banks to the serial port, in one write so they change together.

        Solenoids missing from [solenoid_states] are off. If the write fails (e.g. the device was
        unplugged), the device is disconnected and the error kept.
        """
        if not self.enabled or not self.is_connected():
            return

        # Updates our local pin states
        for i, number in enumerate(self.get_solenoid_numbers()):
            self.pin_states[i] = solenoid_states.get(number, False)

        # Writes each changed bank
        message = b""
        for bank, command in enumerate(b"ABC"):
            pins = self.pin_states[bank * 8:(bank + 1) * 8]
            state = _pins_to_state([pin != self.polarities[bank] for pin in pins])
            if state != self.current_state[bank]:
                message += bytes([command]) + state
                self.current_state[bank] = state
        if message:
            try:
                self.serial_port.write(message)
            except serial.SerialException as e:
                self.error = str(e)
                self.disconnect()

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


def _pins_to_state(pins: List[bool]) -> bytes:
    return bytes([sum(1 << i for i, pin in enumerate(pins) if pin)])


_SAVED_FIELDS = ["hwid", "start_number", "polarities", "enabled"]
