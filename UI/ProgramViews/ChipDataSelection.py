from typing import List

from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import QTimer
from Model.Valve import Valve
from Model.Program.Data import DataType
from UI.AppGlobals import AppGlobals


class ChipDataSelection(QComboBox):
    def __init__(self, dataType: DataType):
        super().__init__()

        self.dataType = dataType

        AppGlobals.Instance().onChipModified.connect(self.Repopulate)

        self.Repopulate()

        timer = QTimer(self)
        timer.timeout.connect(self.UpdateNames)
        timer.start(30)

    def Select(self, data):
        for index in range(self.count()):
            if self.itemData(index) is data:
                self.setCurrentIndex(index)
                return

    def ItemsToRepopulate(self) -> List:
        if self.dataType is DataType.VALVE:
            return AppGlobals.Chip().valves
        if self.dataType is DataType.PROGRAM:
            return AppGlobals.Chip().programs
        if self.dataType is DataType.PROGRAM_PRESET:
            return AppGlobals.Chip().programPresets

    def Repopulate(self):
        self.blockSignals(True)
        lastSelected = self.currentData()
        self.clear()
        self.addItem("None", None)
        for item in self.ItemsToRepopulate():
            self.addItem(item.name, item)
            if item is lastSelected:
                self.setCurrentIndex(self.count() - 1)
        self.blockSignals(False)

    def UpdateNames(self):
        for index in range(self.count()):
            item = self.itemData(index)
            if item:
                self.setItemText(index, item.name)
