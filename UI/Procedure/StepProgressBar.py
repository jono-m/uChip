from PySide2.QtWidgets import *
from PySide2.QtCore import *


class StepProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setRange(0, 100)
        self.setOrientation(Qt.Vertical)
        self.setInvertedAppearance(True)
        self.setTextVisible(False)

    def SetProgress(self, fraction):
        self.setValue(fraction*100)
