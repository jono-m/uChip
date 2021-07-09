from PySide6.QtCore import QPointF, Qt
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

        self._presetNameField = QLineEdit(preset.name)
        self._presetNameField.textChanged.connect(self.UpdatePreset)

        self._presetNameLabel = QLabel(preset.name)
        self._presetNameLabel.setAlignment(Qt.AlignCenter)

        self._instanceWidget = ProgramInstanceWidget(preset.instance, True, False)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._presetNameField)
        layout.addWidget(self._presetNameLabel)
        layout.addWidget(self._instanceWidget)
        self.containerWidget.setLayout(layout)

        self.CheckForPreset()

    def SetEditDisplay(self, editing: bool):
        self._presetNameField.setVisible(editing)
        self._presetNameLabel.setVisible(not editing)
        self._instanceWidget.programNameWidget.setVisible(editing)
        self._instanceWidget.editingParameterVisibility = editing
        self._instanceWidget.UpdateParameterVisibility()
        super().SetEditDisplay(editing)

    def Move(self, delta: QPointF):
        if delta != QPointF():
            AppGlobals.Instance().onChipDataModified.emit()
        self._preset.position += delta
        self.GraphicsObject().setPos(self._preset.position)
        super().Move(delta)

    def UpdatePreset(self):
        self._preset.name = self._presetNameField.text()
        AppGlobals.Instance().onChipDataModified.emit()
        self._presetNameLabel.setText(self._preset.name)

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

    def RunPreset(self):
        AppGlobals.ProgramRunner().Run(self._preset.instance)
