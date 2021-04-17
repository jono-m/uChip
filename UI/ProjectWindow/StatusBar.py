from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *


class StatusBar(QStatusBar):
    globalStatusBar: 'StatusBar' = None

    def __init__(self):
        super().__init__()
        self.infoMessage = QLabel("Status bar info")
        self.coordinatesMessage = QLabel("Coordinates")
        self.addPermanentWidget(self.coordinatesMessage)
        self.addWidget(self.infoMessage, stretch=1)

        StatusBar.globalStatusBar = self

        self.SetInfoMessage("Welcome to μChip!")
        self.SetCoordinates(QPoint(0, 0))

    def SetInfoMessage(self, message):
        self.infoMessage.setText(message)

    def SetCoordinates(self, coordinates: QPoint):
        self.coordinatesMessage.setText("[" + str(coordinates.x()) + ", " + str(coordinates.y()) + "]")