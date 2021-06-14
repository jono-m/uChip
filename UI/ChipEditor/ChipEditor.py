import PySide6
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QToolButton, QMenu, QHBoxLayout, QFileDialog, QInputDialog, QFrame
from UI.ChipEditor.ChipSceneViewer import ChipSceneViewer
from UI.ChipEditor.ValveChipItem import ValveChipItem, Valve
from UI.ChipEditor.ImageChipItem import ImageChipItem, Image
from UI.ChipEditor.ProgramPresetItem import ProgramPresetItem, ProgramPreset
from UI.AppGlobals import AppGlobals
from pathlib import Path

from enum import Enum, auto


class Mode(Enum):
    VIEWING = auto()
    EDITING = auto()


class ChipEditor(QFrame):
    def __init__(self):
        super().__init__()
        self.viewer = ChipSceneViewer()

        actionsLayout = QHBoxLayout()
        actionsLayout.setContentsMargins(0, 0, 0, 0)
        actionsLayout.setSpacing(0)
        self._actionsWidget = QFrame(self.viewer)
        self._actionsWidget.setLayout(actionsLayout)

        self._lockButton = QToolButton()
        self._lockButton.setText("Done")
        self._lockButton.clicked.connect(lambda: self.SetEditing(False))
        self._editButton = QToolButton()
        self._editButton.setText("Edit")
        self._editButton.clicked.connect(lambda: self.SetEditing(True))

        self._plusButton = QToolButton()
        self._plusButton.setText("+")
        self._plusButton.setPopupMode(QToolButton.InstantPopup)

        actionsLayout.addWidget(self._plusButton)
        actionsLayout.addWidget(self._lockButton)
        actionsLayout.addWidget(self._editButton)

        menu = QMenu(self._plusButton)
        menu.addAction("Valve").triggered.connect(self.AddValve)
        menu.addAction("Program Preset...").triggered.connect(self.SelectProgramPreset)
        menu.addAction("Image...").triggered.connect(self.BrowseForImage)

        self._plusButton.setMenu(menu)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.viewer)

        self.setLayout(layout)

        self._mode = Mode.VIEWING

        AppGlobals.Instance().onChipOpened.connect(self.LoadChip)

    def AddValve(self):
        newValve = Valve()
        newValve.solenoidNumber = AppGlobals.Chip().NextSolenoidNumber()
        AppGlobals.Chip().valves.append(newValve)
        AppGlobals.Instance().onChipModified.emit()
        self.viewer.CenterItem(self.viewer.AddItem(ValveChipItem(newValve)))

    def BrowseForImage(self):
        filename, filterType = QFileDialog.getOpenFileName(self, "Browse for Image",
                                                           filter="Images (*.png *.bmp *.jpg *.jpeg *.tif *.tiff)")
        if filename:
            newImage = Image(Path(filename))
            AppGlobals.Chip().images.append(newImage)
            AppGlobals.Instance().onChipModified.emit()
            self.viewer.CenterItem(self.viewer.AddItem(ImageChipItem(newImage)))

    def SelectProgramPreset(self):
        if not AppGlobals.Chip().programs:
            return

        presetSelection, confirmed = QInputDialog.getItem(self, "Program Preset", "Program",
                                                          [program.name for program in AppGlobals.Chip().programs], 0,
                                                          False)
        if confirmed:
            selected = [program for program in AppGlobals.Chip().programs if program.name == presetSelection][0]
            newPreset = ProgramPreset(selected)
            AppGlobals.Chip().programPresets.append(newPreset)
            AppGlobals.Instance().onChipModified.emit()
            self.viewer.CenterItem(self.viewer.AddItem(ProgramPresetItem(newPreset)))

    def SetEditing(self, editing):
        self.viewer.SetEditing(editing)

        self._lockButton.setVisible(editing)
        self._plusButton.setVisible(editing)
        self._editButton.setVisible(not editing)

        AppGlobals.Chip().editingMode = editing

        self.FloatWidgets()

    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.FloatWidgets()

    def FloatWidgets(self):
        self._actionsWidget.adjustSize()
        self._actionsWidget.move(self.viewer.rect().topRight() - self._actionsWidget.rect().topRight())

    def LoadChip(self):
        self.viewer.RemoveAll()

        for valve in AppGlobals.Chip().valves:
            self.viewer.AddItem(ValveChipItem(valve))
        for image in AppGlobals.Chip().images:
            self.viewer.AddItem(ImageChipItem(image))
        for preset in AppGlobals.Chip().programPresets:
            self.viewer.AddItem(ProgramPresetItem(preset))

        self.viewer.Recenter()

        self.SetEditing(AppGlobals.Chip().editingMode)
