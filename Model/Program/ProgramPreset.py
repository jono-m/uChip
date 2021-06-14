from PySide6.QtCore import QPoint
from Model.Program.Program import Program
from Model.Program.ProgramInstance import ProgramInstance


class ProgramPreset:
    def __init__(self, program: Program):
        self.position = QPoint(0, 0)

        self.name = program.name + " Preset"

        self.instance = ProgramInstance(program)

