from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from UI.ProgramViews.ProgramParameterList import ProgramParameterList
from Model.Program.ProgramPreset import ProgramPreset
from UI.AppGlobals import AppGlobals


class ProgramPresetItem(WidgetChipItem):
    def __init__(self, preset: ProgramPreset):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.CheckForProgram)

        self._preset = preset

        self._programNameLabel = QLabel()
        self._presetNameField = QLineEdit()
        self._presetNameField.textChanged.connect(self.UpdatePreset)

        self._parameterList = ProgramParameterList(preset.instance)
        self._runButton = QPushButton("Run")
        self._runButton.clicked.connect(self.RunPreset)

        layout = QVBoxLayout()
        layout.addWidget(self._presetNameField)
        layout.addWidget(self._programNameLabel)
        layout.addWidget(self._parameterList)
        layout.addWidget(self._runButton)
        self.containerWidget.setLayout(layout)

        self.containerWidget.adjustSize()
        self.Update()
        self.CheckForProgram()

    def Move(self, delta: QPointF):
        self._preset.position += delta
        self.GraphicsObject().setPos(self._preset.position)

    def UpdatePreset(self):
        self._preset.name = self._presetNameField.text()

    def CheckForProgram(self):
        if self._preset.instance.program not in AppGlobals.Chip().programs:
            self.Delete()

    def Delete(self):
        super().Delete()
        AppGlobals.Chip().programPresets.remove(self._preset)
        AppGlobals.Instance().onChipModified.emit()

    def Duplicate(self) -> 'ChipItem':
        newPreset = ProgramPreset(self._preset.instance.program)
        newPreset.instance = self._preset.instance.Clone()
        newPreset.position = QPointF(self._preset.position)
        newPreset.name = self._preset.name

        AppGlobals.Chip().programPresets.append(newPreset)
        AppGlobals.Instance().onChipModified.emit()
        return ProgramPresetItem(newPreset, self._programRunner)

    def Update(self):
        self._runButton.setEnabled(not self._programRunner.IsRunning(self._preset.instance))

        if self._presetNameField.text() != self._preset.name:
            self._presetNameField.setText(self._preset.name)

        self._programNameLabel.setText(self._preset.instance.program.name)

    def RunPreset(self):
        AppGlobals.ProgramRunner().Run(self._preset.instance)
