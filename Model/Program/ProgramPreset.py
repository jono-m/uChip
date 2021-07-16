from PySide6.QtCore import QPointF
from Model.Program.Program import Program
from Model.Program.ProgramInstance import ProgramInstance


class ProgramPreset:
    def __init__(self, program: Program):
        self.position = QPointF(0, 0)

        self.name = program.name + " Preset"

        self.instance = ProgramInstance(program)

        self.showDescription = True
