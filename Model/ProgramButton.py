from PySide6.QtCore import QPointF
from Model.Program.Program import Program
from Model.Program.ProgramInstance import ProgramInstance


class ProgramButton:
    def __init__(self, program: Program):
        self.position = QPointF(0, 0)

        self.instance = ProgramInstance(program)
