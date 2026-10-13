"""The rig: serial solenoid-driver devices and the solenoid states sent to them.

Each device drives 24 solenoids in three 8-pin banks (A, B, C), numbered from its start number.
Device settings are saved to a JSON file and matched to serial ports by hardware ID.
"""
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from backend.device import Device, get_available_devices, load_device_from_fields
from backend.json_io import read_json, write_json

DEVICES_FILE = Path("devices.json")


@dataclass(eq=False)
class Rig:
    devices: List[Device] = field(default_factory=list)
    solenoid_states: Dict[int, bool] = field(default_factory=dict)

    # Solenoid states

    def get_solenoid(self, number: int) -> bool:
        return self.solenoid_states.get(number, False)

    def set_solenoid(self, number: int, state: bool):
        self.solenoid_states[number] = state

    def toggle_solenoid(self, number: int):
        self.set_solenoid(number, not self.get_solenoid(number))

    def connected_solenoids(self) -> List[int]:
        numbers = set()
        for device in self.devices:
            if device.enabled and device.is_connected():
                numbers.update(device.get_solenoid_numbers())
        return sorted(numbers)

    # Devices

    def rescan_devices(self):
        """Marks saved devices as available if their port is present and adds newly found ports."""
        available_devices = get_available_devices()
        for known_devices in self.devices:
            match = next((d for d in available_devices if d.hwid == known_devices.hwid), None)
            known_devices.available = match is not None
            if match is not None:
                known_devices.port_info = match.port_info
        known_hwid = [d.hwid for d in self.devices]
        for available_device in available_devices:
            if available_device.hwid not in known_hwid or available_device.hwid == "":
                self.devices.append(available_device)

    def disconnect_all(self):
        for device in self.devices:
            device.disconnect()

    def apply_device_settings(self, device: Device):
        """Connects or disconnects [device] to match its enabled setting and sends current states."""
        if device.enabled and not device.is_connected():
            device.connect()
        elif not device.enabled and device.is_connected():
            device.disconnect()
        self.flush()

    def flush(self):
        """Connects enabled devices as needed and sends them the current solenoid states."""
        for device in self.devices:
            if device.enabled and device.available and not device.is_connected():
                device.connect()
            device.send_solenoids(self.solenoid_states)

    def blink(self, device: Device):
        """Toggles all of [device]'s solenoids a few times so it can be identified. Blocks ~1 second."""
        numbers = device.get_solenoid_numbers()
        for i in range(5):
            device.send_solenoids({n: i % 2 == 0 for n in numbers})
            time.sleep(0.25)
        device.send_solenoids(self.solenoid_states)

    def save_devices(self, path: Path = DEVICES_FILE):
        data = [device.get_device_saved_fields() for device in self.devices]
        write_json(data, path)


def load_rig_from_file(path: Path = DEVICES_FILE) -> Rig:
    path = Path(path)
    if not path.exists():
        return Rig()
    return Rig(devices=[load_device_from_fields(d) for d in read_json(path)])
