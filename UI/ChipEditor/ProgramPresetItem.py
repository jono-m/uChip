from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QLabel, QHBoxLayout, QCheckBox

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from UI.ProgramViews.ProgramInstanceWidget import ProgramInstanceWidget
from Model.Program.ProgramPreset import ProgramPreset
from UI.AppGlobals import AppGlobals


class ProgramPresetItem(WidgetChipItem):
    def __init__(self, preset: ProgramPreset):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.CheckForPreset)

        self._preset = preset

        self._presetNameLabel = QLabel(preset.name)
        self._presetNameLabel.setAlignment(Qt.AlignCenter)

        self._instanceWidget = ProgramInstanceWidget(preset.instance)
        self._instanceWidget.SetTitleVisible(False)
        self._instanceWidget.ownsInstance = True

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._presetNameLabel)
        layout.addWidget(self._instanceWidget)
        self.containerWidget.setLayout(layout)

        inspLayout = QVBoxLayout()
        inspLayout.setContentsMargins(0, 0, 0, 0)
        inspLayout.setSpacing(0)
        nameLayout = QHBoxLayout()
        nameLayout.setContentsMargins(0, 0, 0, 0)
        nameLayout.setSpacing(0)
        inspLayout.addLayout(nameLayout)
        self.HoverWidget().setLayout(inspLayout)
        nameLayout.addWidget(QLabel("Preset Name"))
        self._presetNameField = QLineEdit(preset.name)
        self._presetNameField.textChanged.connect(self.UpdatePreset)
        self._showDescriptionField = QCheckBox("Show Description")
        self._showDescriptionField.setChecked(self._preset.showDescription)
        self._showDescriptionField.stateChanged.connect(self.UpdatePreset)
        nameLayout.addWidget(self._presetNameField)
        inspLayout.addWidget(self._showDescriptionField)

        self._inspectorInstance = ProgramInstanceWidget(preset.instance)
        self._inspectorInstance.SetShowAllParameters(True)
        self._inspectorInstance.SetEditParameterVisibility(True)
        self._inspectorInstance.SetDescriptionVisible(False)
        self._inspectorInstance.ownsInstance = True
        inspLayout.addWidget(self._inspectorInstance)

        self.UpdatePresetView()
        self.CheckForPreset()

    def Move(self, delta: QPointF):
        if delta != QPointF():
            AppGlobals.Instance().onChipDataModified.emit()
        self._preset.position += delta
        self.GraphicsObject().setPos(self._preset.position)
        super().Move(delta)

    def CanMove(self, scenePoint: QPointF) -> bool:
        childAt = self.bigContainer.childAt(self.GraphicsObject().mapFromScene(scenePoint).toPoint())
        return isinstance(childAt, QLabel)

    def UpdatePreset(self):
        self._preset.name = self._presetNameField.text()
        self._preset.showDescription = self._showDescriptionField.isChecked()
        AppGlobals.Instance().onChipDataModified.emit()
        self.UpdatePresetView()

    def UpdatePresetView(self):
        self._presetNameLabel.setText(
            "<b>" + self._preset.name + "</b> <i>(" + self._preset.instance.program.name + ")</i>")
        if self._instanceWidget.DescriptionVisible() != self._preset.showDescription:
            self._instanceWidget.SetDescriptionVisible(self._preset.showDescription)

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
