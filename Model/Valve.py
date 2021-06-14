from PySide6.QtCore import QPoint


class Valve:
    def __init__(self):
        self.name = "Valve"
        self.position = QPoint()
        self.solenoidNumber = 0
