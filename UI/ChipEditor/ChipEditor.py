from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton, QMenu, QHBoxLayout, QFileDialog, QInputDialog, QFrame
from PySide6.QtCore import QSize, Signal, QEvent
from UI.ChipEditor.ChipSceneViewer import ChipSceneViewer
from UI.ChipEditor.ValveChipItem import ValveChipItem, Valve
from UI.ChipEditor.ImageChipItem import ImageChipItem, Image
from UI.ChipEditor.ProgramPresetItem import ProgramPresetItem, ProgramPreset
from UI.ChipEditor.Inspector import Inspector
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
        self.setContentsMargins(0, 0, 0, 0)

        actionsLayout = QHBoxLayout()
        actionsLayout.setContentsMargins(0, 0, 0, 0)
        actionsLayout.setSpacing(0)
        self._actionsWidget = FloatingWidget(self)
        self._actionsWidget.onResize.connect(self.FloatWidgets)
        self._actionsWidget.setLayout(actionsLayout)

        self._lockButton = ActionButtonFrame("Assets/Images/checkIcon.png")
        self._lockButton.button.clicked.connect(lambda: self.SetEditing(False))
        self._editButton = ActionButtonFrame("Assets/Images/Edit.png")
        self._editButton.button.clicked.connect(lambda: self.SetEditing(True))

        self._plusButton = ActionButtonFrame("Assets/Images/plusIcon.png")
        self._plusButton.button.setPopupMode(QToolButton.InstantPopup)

        actionsLayout.addWidget(self._plusButton)
        actionsLayout.addWidget(self._lockButton)
        actionsLayout.addWidget(self._editButton)

        self._inspector = Inspector(self)
        self.viewer.selectionChanged.connect(self._inspector.SetSelection)
        inspectorLayout = QHBoxLayout()
        inspectorLayout.setContentsMargins(0, 0, 0, 0)
        inspectorLayout.setSpacing(0)
        inspectorLayout.addWidget(self._inspector)
        self._inspectorWidget = FloatingWidget(self)
        self._inspectorWidget.onResize.connect(self.FloatWidgets)
        self._inspectorWidget.setLayout(inspectorLayout)

        menu = QMenu(self._plusButton)
        menu.addAction("Valve").triggered.connect(self.AddValve)
        menu.addAction("Program Preset...").triggered.connect(self.SelectProgramPreset)
        menu.addAction("Image...").triggered.connect(self.BrowseForImage)

        self._plusButton.button.setMenu(menu)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.viewer)

        self.setLayout(layout)

        self._mode = Mode.VIEWING

        AppGlobals.Instance().onChipOpened.connect(self.LoadChip)

        self._actionsWidget.raise_()
        self._inspectorWidget.raise_()

        self.FloatWidgets()

    def AddValve(self):
        newValve = Valve()
        newValve.solenoidNumber = AppGlobals.Chip().NextSolenoidNumber()
        AppGlobals.Chip().valves.append(newValve)
        AppGlobals.Instance().onChipAddRemove.emit()
        self.viewer.CenterItem(self.viewer.AddItem(ValveChipItem(newValve)))

    def BrowseForImage(self):
        filename, filterType = QFileDialog.getOpenFileName(self, "Browse for Image",
                                                           filter="Images (*.png *.bmp *.jpg *.jpeg *.tif *.tiff)")
        if filename:
            newImage = Image(Path(filename))
            AppGlobals.Chip().images.append(newImage)
            AppGlobals.Instance().onChipAddRemove.emit()
            self.viewer.CenterItem(self.viewer.AddItem(ImageChipItem(newImage)))

    def SelectProgramPreset(self):
        if not AppGlobals.Chip().programs:
            return

        presetSelection, confirmed = QInputDialog.getItem(self, "Program Preset", "Select a program:",
                                                          [program.name for program in AppGlobals.Chip().programs], 0,
                                                          False)
        if confirmed:
            selected = [program for program in AppGlobals.Chip().programs if program.name == presetSelection][0]
            newPreset = ProgramPreset(selected)
            AppGlobals.Chip().programPresets.append(newPreset)
            AppGlobals.Instance().onChipAddRemove.emit()
            self.viewer.CenterItem(self.viewer.AddItem(ProgramPresetItem(newPreset)))

    def resizeEvent(self, event) -> None:
        self.FloatWidgets()
        super().resizeEvent(event)

    def SetEditing(self, editing):
        self.viewer.SetEditing(editing)

        self._lockButton.setVisible(editing)
        self._plusButton.setVisible(editing)
        self._editButton.setVisible(not editing)

        AppGlobals.Chip().editingMode = editing

        self.FloatWidgets()

    def FloatWidgets(self):
        self._actionsWidget.adjustSize()
        self._inspectorWidget.adjustSize()
        self._actionsWidget.move(self.rect().topRight() - self._actionsWidget.rect().topRight())
        self._inspectorWidget.move(self.rect().bottomRight() - self._inspectorWidget.rect().bottomRight())

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


class FloatingWidget(QFrame):
    onResize = Signal()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.onResize.emit()
        print("Resize")

    def event(self, e) -> bool:
        if e.type() == QEvent.LayoutRequest:
            self.onResize.emit()
        return super().event(e)


class ActionButtonFrame(QFrame):
    def __init__(self, icon):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.button = QToolButton()
        self.button.setProperty("Attention", True)
        self.button.setIcon(QIcon(icon))
        layout.addWidget(self.button)
