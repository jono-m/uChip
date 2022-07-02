from typing import Optional, List, Dict
from Data.Program import ProgramInstance, ProgramSpecification, Parameter, FindObjectWithName, \
    ExceptionIfNone


class Valve:
    def __init__(self):
        self.name = ""
        self.position_x = 0
        self.position_y = 0
        self.solenoidNumber = 0


class ProgramPreset:
    def __init__(self):
        self.name = ""
        self.position_x = 0
        self.position_y = 0
        self.instance: Optional[ProgramInstance] = None
        self.parameterVisibility: Dict[Parameter, bool] = {}
        self.showDescription = False


class Annotation:
    def __init__(self):
        self.position_x = 0
        self.position_y = 0
        self.text = ""
        self.size = 1


class Image:
    def __init__(self):
        self.position_x = 0
        self.position_y = 0
        self.localPath = ""
        self.width = 0
        self.height = 0


class Chip:
    def __init__(self):
        self.valves: List[Valve] = []
        self.specifications: List[ProgramSpecification] = []
        self.programPresets: List[ProgramPreset] = []
        self.images: List[Image] = []
        self.annotations: List[Annotation] = []