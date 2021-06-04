from PySide6.QtCore import QPointF


class Valve:
    def __init__(self):
        self.name = "Valve"
        self.position = QPointF()
        self.solenoidNumber = 0
