import typing

from Model.Valve import Valve
from Model.Program.Program import Program
from Model.ProgramButton import ProgramButton
from Model.Image import Image
from Model.Annotation import Annotation


class Chip:
    def __init__(self):
        self.valves: typing.List[Valve] = []
        self.programs: typing.List[Program] = []
        self.programButtons: typing.List[ProgramButton] = []
        self.images: typing.List[Image] = []
        self.annotations: typing.List[Annotation] = []

    def NextSolenoidNumber(self):
        number = 0
        while True:
            if number not in [valve.solenoidNumber for valve in self.valves]:
                return number
            number += 1
