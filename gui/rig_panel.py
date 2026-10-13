"""The rig panel: manual solenoid control and settings for the connected driver devices."""
from dataclasses import dataclass, field
from typing import List, Optional

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (QCheckBox, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QListWidget, QPushButton,
                               QSizePolicy, QSpinBox, QVBoxLayout, QWidget)

from backend.rig import Device, Rig
from gui.widgets import clear_layout, sync_checked, sync_label, sync_spin

COLUMNS = 8


@dataclass(eq=False)
class RigPanel:
    widget: QWidget
    rig: Rig
    solenoid_grid: QGridLayout
    none_label: QLabel
    device_list: QListWidget
    info: QLabel
    enabled: QCheckBox
    start_number: QSpinBox
    invert: List[QCheckBox]
    blink: QPushButton
    solenoid_buttons: List[tuple] = field(default_factory=list)  # (number, button)
    shown_numbers: List[int] = field(default_factory=list)
    shown_devices: List[Device] = field(default_factory=list)
    device: Optional[Device] = None

    def _rebuild_solenoids(self, numbers: List[int]):
        clear_layout(self.solenoid_grid)
        self.solenoid_buttons = []
        rig = self.rig

        def set_all(group: List[int], state: bool):
            for n in group:
                rig.set_solenoid(n, state)

        rows = [numbers[i:i + COLUMNS] for i in range(0, len(numbers), COLUMNS)]
        for r, row in enumerate(rows):
            for c, n in enumerate(row):
                button = _square_button(str(n), checkable=True)
                button.clicked.connect(lambda checked=False, n=n: rig.toggle_solenoid(n))
                self.solenoid_grid.addWidget(button, r, c)
                self.solenoid_buttons.append((n, button))
            for c, (text, state) in enumerate((("ON", True), ("OFF", False))):
                button = _square_button(text)
                button.clicked.connect(lambda checked=False, row=row, state=state: set_all(row, state))
                self.solenoid_grid.addWidget(button, r, COLUMNS + c)
        if numbers:
            for c, (text, state) in enumerate((("ALL ON", True), ("ALL OFF", False))):
                button = _square_button(text)
                button.clicked.connect(lambda checked=False, state=state: set_all(numbers, state))
                self.solenoid_grid.addWidget(button, len(rows), c * 5, 1, 5)

    def refresh(self):
        rig = self.rig
        numbers = rig.connected_solenoids()
        if numbers != self.shown_numbers:
            self.shown_numbers = numbers
            self._rebuild_solenoids(numbers)
        self.none_label.setVisible(not numbers)
        for n, button in self.solenoid_buttons:
            sync_checked(button, rig.get_solenoid(n))

        devices = [d for d in rig.devices if d.available]
        if devices != self.shown_devices:
            self.shown_devices = devices
            self.device_list.blockSignals(True)
            self.device_list.clear()
            self.device_list.addItems(["%s (%s)" % (d.port_info.name, d.port_info.device) for d in devices])
            if self.device in devices:
                self.device_list.setCurrentRow(devices.index(self.device))
            else:
                self.device = None
            self.device_list.blockSignals(False)

        device = self.device
        for w in [self.enabled, self.start_number, *self.invert]:
            w.setEnabled(device is not None)
        self.blink.setEnabled(device is not None and device.is_connected())
        if device is None:
            sync_label(self.info, "No device selected")
            return
        sync_label(self.info, device.summary() + ("\n\nError: " + device.error if device.error else ""))
        sync_checked(self.enabled, device.enabled)
        sync_spin(self.start_number, device.start_number)
        for box, inverted in zip(self.invert, device.polarities):
            sync_checked(box, inverted)


def _square_button(text: str, checkable: bool = False) -> QPushButton:
    # Solenoid buttons are checkable, so the theme shows on solenoids as checked (accent colored).
    button = QPushButton(text)
    button.setMinimumSize(QSize(30, 30))
    button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    button.setCheckable(checkable)
    return button


def build_rig_panel(rig: Rig, on_settings_changed=lambda: None) -> RigPanel:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel("<b>Solenoid Control</b>"))
    solenoid_grid = QGridLayout()
    solenoid_grid.setSpacing(2)
    layout.addLayout(solenoid_grid)
    none_label = QLabel("No solenoids available.")
    layout.addWidget(none_label)
    layout.addStretch(1)

    layout.addWidget(QLabel("<b>Available Devices</b>"))
    rescan = QPushButton("Rescan")
    layout.addWidget(rescan)
    device_list = QListWidget()
    info = QLabel()
    info.setWordWrap(True)
    devices_row = QHBoxLayout()
    devices_row.addWidget(device_list, 1)
    devices_row.addWidget(info, 1)
    layout.addLayout(devices_row)

    enabled, start_number = QCheckBox(), QSpinBox()
    start_number.setRange(0, 1000)
    invert = [QCheckBox() for _ in range(3)]
    settings = QFormLayout()
    settings.addRow("Enabled", enabled)
    settings.addRow("Start number", start_number)
    for i, box in enumerate(invert):
        settings.addRow("Invert %d-%d" % (i * 8, i * 8 + 7), box)
    layout.addLayout(settings)
    blink = QPushButton("Blink Solenoids")
    layout.addWidget(blink)

    panel = RigPanel(widget, rig, solenoid_grid, none_label, device_list, info, enabled, start_number, invert, blink)

    def settings_edited():
        device = panel.device
        if device is None:
            return
        device.enabled = enabled.isChecked()
        device.start_number = start_number.value()
        device.polarities = [box.isChecked() for box in invert]
        rig.apply_device_settings(device)
        on_settings_changed()

    def device_selected(row: int):
        panel.device = panel.shown_devices[row] if 0 <= row < len(panel.shown_devices) else None

    rescan.clicked.connect(lambda: rig.rescan_devices())
    device_list.currentRowChanged.connect(device_selected)
    for box in [enabled, *invert]:
        box.clicked.connect(settings_edited)
    start_number.valueChanged.connect(settings_edited)
    blink.clicked.connect(lambda: panel.device is not None and rig.blink(panel.device))
    return panel


