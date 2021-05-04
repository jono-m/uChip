import typing

from Valve import Valve
from Program.Program import Program
from ProgramButton import ProgramButton
from Image import Image
from Annotation import Annotation


class Chip:
    def __init__(self):
        self.valves: typing.List[Valve] = []
        self.programs: typing.List[Program] = []
        self.programButtons: typing.List[ProgramButton] = []
        self.images: typing.List[Image] = []
        self.annotations: typing.List[Annotation] = []
