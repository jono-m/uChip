"""The rig: serial solenoid-driver devices and the solenoid states sent to them.

Each device drives 24 solenoids in three 8-pin banks (A, B, C), numbered from its start number.
Device settings are saved to a JSON file and matched to serial ports by hardware ID.

All serial I/O happens in flush(), which the runner calls every tick, so it stays on one thread. Other
methods only change the rig's data and let the next flush act on it.
"""
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from backend.device import Device, get_available_devices, load_device_from_fields
from backend.json_io import read_json, write_json

BLINK_COUNT = 6
BLINK_PERIOD = 0.125  # seconds per on or off


@dataclass(eq=False)
class Rig:
    devices: List[Device] = field(default_factory=list)
    solenoid_states: Dict[int, bool] = field(default_factory=dict)
    blinking_device: Optional[Device] = None
    blink_start_time: float = 0

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

    def rescan_devices(self):
        """Marks saved devices as available if their port is present and adds newly found ports."""
        found_devices = get_available_devices()
        for device in self.devices:
            match = next((found for found in found_devices if _is_same_device(device, found)), None)
            device.available = match is not None
            if match is not None:
                device.port_info = match.port_info
        for found in found_devices:
            if not any(_is_same_device(device, found) for device in self.devices):
                self.devices.append(found)

    def disconnect_all(self):
        for device in self.devices:
            device.disconnect()

    def start_blink(self, device: Device):
        self.blink_start_time = time.perf_counter()
        self.blinking_device = device

    def _send_blink(self, current_time: float):
        on = int((current_time - self.blink_start_time) / BLINK_PERIOD) % 2 == 0
        self.blinking_device.send_solenoids({n: on for n in self.blinking_device.get_solenoid_numbers()})

    def flush(self, current_time: Optional[float] = None):
        """Connects or disconnects devices to match their enabled setting, and sends them the solenoid
        states (or the blink pattern) if they changed. [current_time] defaults to now."""
        if current_time is None:
            current_time = time.perf_counter()
        if self.blinking_device is not None and                 current_time - self.blink_start_time > BLINK_PERIOD * BLINK_COUNT:
            self.blinking_device = None

        for device in self.devices:
            device.update_connection_state()

            if device is self.blinking_device:
                self._send_blink(current_time)
            elif device.is_connected():
                device.send_solenoids(self.solenoid_states)

    def save_devices(self, path: Path):
        data = [device.get_device_saved_fields() for device in self.devices]
        write_json(data, path)


def _is_same_device(device: Device, found: Device) -> bool:
    """Whether [found] (from get_available_devices) is [device]'s port, by hardware ID."""
    return device.hwid == found.hwid


def load_rig_from_file(path: Path) -> Rig:
    """The rig saved at [path]. If the file can't be read it is kept as "<name>.bad" and an empty rig is
    returned, so a damaged file doesn't stop uChip from starting. Entries without a hardware ID are skipped."""
    path = Path(path)
    if not path.exists():
        return Rig()
    try:
        data = read_json(path)
        if not isinstance(data, list):
            raise ValueError("expected a list of devices")
        devices = [load_device_from_fields(d) for d in data if isinstance(d, dict) and "hwid" in d]
    except (OSError, ValueError, TypeError) as e:
        backup = path.with_name(path.name + ".bad")
        print("Could not read device settings from '%s' (%s). Starting with no devices; the file was kept as "
              "'%s'." % (path, e, backup), file=sys.stderr)
        try:
            path.replace(backup)
        except OSError:
            pass
        return Rig()
    return Rig(devices=devices)
