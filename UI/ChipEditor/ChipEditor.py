from typing import Optional, List

import PySide6
from PySide6.QtGui import QKeyEvent, Qt
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QWidget, QToolButton, QMenu, QHBoxLayout, QFileDialog, QSplitter
from UI.ChipEditor.ChipSceneViewer import ChipSceneViewer, ChipItem
from UI.ChipEditor.ValveChipItem import ValveChipItem, Valve
from UI.ChipEditor.ImageChipItem import ImageChipItem, Image
from Model.Chip import Chip
from UI.AppGlobals import AppGlobals

from enum import Enum, auto

from UI.ProgramEditor.ProgramEditor import ProgramEditor


class Mode(Enum):
    VIEWING = auto()
    EDITING = auto()


class ChipEditor(QWidget):
    def __init__(self):
        super().__init__()
        self._viewer = ChipSceneViewer()

        actionsLayout = QHBoxLayout()
        self._actionsWidget = QWidget(self._viewer)
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
        menu.addAction("Image...").triggered.connect(self.BrowseForImage)

        self._plusButton.setMenu(menu)

        self._plusButton.setFixedSize(50, 50)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._viewer)
        self.setLayout(layout)

        self._mode = Mode.VIEWING

        self.SetEditing(False)

        AppGlobals.onChipOpened().connect(self.LoadChip)

    def AddValve(self):
        newValve = Valve()
        newValve.solenoidNumber = AppGlobals.Chip().NextSolenoidNumber()
        AppGlobals.Chip().valves.append(newValve)
        self._viewer.CenterItem(self._viewer.AddItem(ValveChipItem(newValve)))

    def BrowseForImage(self):
        filename, filterType = QFileDialog.getOpenFileName(self, "Browse for Image",
                                                           filter="Images (*.png *.bmp *.jpg *.jpeg *.tif *.tiff)")
        if filename:
            newImage = Image()
            newImage.filename = filename
            newImage.InitializeSize()
            self._chip.images.append(newImage)
            self._viewer.CenterItem(self._viewer.AddItem(ImageChipItem(self._chip, newImage)))

    def SetEditing(self, editing):
        self._viewer.SetEditing(editing)

        self._lockButton.setVisible(editing)
        self._plusButton.setVisible(editing)
        self._editButton.setVisible(not editing)

        self.FloatActionsWidget()

    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.FloatActionsWidget()

    def FloatActionsWidget(self):
        self._actionsWidget.adjustSize()
        self._actionsWidget.move(self._viewer.rect().topRight() - self._actionsWidget.rect().topRight())

    def LoadChip(self):
        self._viewer.RemoveAll()

        for valve in AppGlobals.Chip().valves:
            self._viewer.AddItem(ValveChipItem(valve))
        for image in AppGlobals.Chip().images:
            self._viewer.AddItem(ImageChipItem(image))

        self._viewer.Recenter()

        self.SetEditing(AppGlobals.Chip().editingMode)
