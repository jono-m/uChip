from typing import Optional, List, Dict
from Data.Program import ProgramInstance, ProgramSpecification, Parameter


class Valve:
    def __init__(self):
        self.name = ""
        self.rect = [0, 0, 0, 0]
        self.solenoidNumber = 0
        self.textSize = 12


class ProgramPreset:
    def __init__(self):
        self.name = ""
        self.rect = [0, 0, 0, 0]
        self.instance: Optional[ProgramInstance] = None
        self.parameterVisibility: Dict[Parameter, bool] = {}
        self.showDescription = False
        self.textSize = 12


class Text:
    def __init__(self):
        self.rect = [0, 0, 0, 0]
        self.text = "New annotation"
        self.textSize = 12


class Image:
    def __init__(self):
        self.rect = [0, 0, 0, 0]
        self.localPath = ""


class Chip:
    def __init__(self):
        self.valves: List[Valve] = []
        self.specifications: List[ProgramSpecification] = []
        self.programPresets: List[ProgramPreset] = []
        self.images: List[Image] = []
        self.text: List[Text] = []
