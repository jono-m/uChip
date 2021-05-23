from typing import Optional

import PySide6
from PySide6.QtGui import QKeyEvent, Qt
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QWidget, QToolButton, QMenu, QHBoxLayout, QFileDialog
from UI.ChipEditor.ChipSceneViewer import ChipSceneViewer
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
        self._viewer.setParent(self)

        actionsLayout = QHBoxLayout()
        self._actionsWidget = QWidget(self)
        self._actionsWidget.setLayout(actionsLayout)

        self._lockButton = QToolButton()
        self._lockButton.setText("Lock")
        self._lockButton.clicked.connect(lambda: self.SetMode(Mode.VIEWING))
        self._editButton = QToolButton()
        self._editButton.setText("Edit")
        self._editButton.clicked.connect(lambda: self.SetMode(Mode.EDITING))

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

        self.SetMode(Mode.VIEWING)

        self.LoadChip(Chip())

    def SetMode(self, mode: Mode):
        self._mode = mode
        self._lockButton.setVisible(self._mode is Mode.EDITING)
        self._plusButton.setVisible(self._mode is Mode.EDITING)
        self._editButton.setVisible(self._mode is Mode.VIEWING)

        self._viewer.selectionEnabled = self._mode is Mode.EDITING
        if self._mode is Mode.VIEWING:
            self._viewer.DeselectAll()

        self.FloatActionsWidget()

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

    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.FloatActionsWidget()

    def FloatActionsWidget(self):
        self._actionsWidget.adjustSize()
        self._actionsWidget.move(self.rect().topRight() - self._actionsWidget.rect().topRight())

    def LoadChip(self, chip: Chip):
        self._viewer.RemoveAll()
        self._chip = chip

        for valve in self._chip.valves:
            self._viewer.AddItem(ValveChipItem(self._chip, valve))
        for image in self._chip.images:
            self._viewer.AddItem(ImageChipItem(self._chip, image))

        self._viewer.Recenter()

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.DeleteSelected()

        if event.key() == Qt.Key.Key_D and event.modifiers() == Qt.Modifier.CTRL:
            self.DuplicateSelected()

        super().keyReleaseEvent(event)

    def DeleteSelected(self):
        for item in self._viewer.GetSelectedItems():
            if item.CanDelete():
                item.Delete()
                self._viewer.RemoveItem(item)

    def DuplicateSelected(self):
        newItems = []
        for item in self._viewer.GetSelectedItems():
            if item.CanDuplicate():
                newItem = item.Duplicate()
                newItem.Move(QPointF(50, 50))
                self._viewer.AddItem(newItem)
                newItems.append(newItem)
        if newItems:
            self._viewer.DeselectAll()
            [self._viewer.SelectItem(item) for item in newItems]
