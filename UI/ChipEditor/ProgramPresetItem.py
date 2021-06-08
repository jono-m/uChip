from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QLabel

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from UI.ProgramViews.ProgramInstanceWidget import ProgramInstanceWidget
from Model.Program.ProgramPreset import ProgramPreset
from UI.AppGlobals import AppGlobals


class ProgramPresetItem(WidgetChipItem):
    def __init__(self, preset: ProgramPreset):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.CheckForPreset)

        self._preset = preset

        self._presetNameField = QLineEdit()
        self._presetNameField.textChanged.connect(self.UpdatePreset)

        self._presetNameLabel = QLabel()

        self._instanceWidget = ProgramInstanceWidget(preset.instance, True)

        layout = QVBoxLayout()
        layout.addWidget(self._presetNameField)
        layout.addWidget(self._presetNameLabel)
        layout.addWidget(self._instanceWidget)
        self.containerWidget.setLayout(layout)

        self.Update()
        self.CheckForPreset()

    def SetEditDisplay(self, editing: bool):
        self._presetNameField.setVisible(editing)
        self._presetNameLabel.setVisible(not editing)
        super().SetEditDisplay(editing)

    def Move(self, delta: QPointF):
        self._preset.position += delta
        self.GraphicsObject().setPos(self._preset.position)

    def UpdatePreset(self):
        self._preset.name = self._presetNameField.text()

    def CheckForPreset(self):
        if self._preset not in AppGlobals.Chip().programPresets:
            self.RemoveItem()

    def RequestDelete(self):
        super().RequestDelete()
        AppGlobals.Chip().programPresets.remove(self._preset)
        AppGlobals.Instance().onChipModified.emit()

    def Duplicate(self) -> 'ChipItem':
        newPreset = ProgramPreset(self._preset.instance.program)
        newPreset.instance = self._preset.instance.Clone()
        newPreset.position = QPointF(self._preset.position)
        newPreset.name = self._preset.name

        AppGlobals.Chip().programPresets.append(newPreset)
        AppGlobals.Instance().onChipModified.emit()
        return ProgramPresetItem(newPreset)

    def Update(self):
        if self._presetNameField.text() != self._preset.name:
            self._presetNameField.setText(self._preset.name)
        self._presetNameLabel.setText(self._preset.name)

    def RunPreset(self):
        AppGlobals.ProgramRunner().Run(self._preset.instance)
