from typing import Optional, List

import PySide6
from PySide6.QtGui import QKeyEvent, Qt
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QWidget, QToolButton, QMenu, QHBoxLayout, QFileDialog
from UI.ChipEditor.ChipSceneViewer import ChipSceneViewer, ChipItem
from UI.ChipEditor.ValveChipItem import ValveChipItem, Valve
from UI.ChipEditor.ImageChipItem import ImageChipItem, Image
from Model.Chip import Chip

from enum import Enum, auto


class Mode(Enum):
    VIEWING = auto()
    EDITING = auto()


class ChipEditor(QWidget):
    def __init__(self):
        super().__init__()

        self._chip: Optional[Chip] = None

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

        self.LoadChip(Chip())

    def AddValve(self):
        newValve = Valve()
        newValve.solenoidNumber = self._chip.NextSolenoidNumber()
        self._chip.valves.append(newValve)
        self._viewer.CenterItem(self._viewer.AddItem(ValveChipItem(self._chip, newValve)))

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

    def LoadChip(self, chip: Chip):
        self._viewer.RemoveAll()
        self._chip = chip

        for valve in self._chip.valves:
            self._viewer.AddItem(ValveChipItem(self._chip, valve))
        for image in self._chip.images:
            self._viewer.AddItem(ImageChipItem(self._chip, image))

        self._viewer.Recenter()
