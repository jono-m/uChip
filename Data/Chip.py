from typing import Optional, List, Dict
from Data.Program import ProgramInstance, ProgramSpecification, Parameter
from PySide6.QtGui import QImage


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


class Text:
    def __init__(self):
        self.rect = [0, 0, 0, 0]
        self.text = "New annotation"
        self.color = (0, 0, 0)


class Image:
    def __init__(self):
        self.rect = [0, 0, 0, 0]
        self.original_image: Optional[QImage] = None

    def __setstate__(self, state):
        self.original_image = QImage(state['data'], *state['size'], QImage.Format(state['format']))
        self.rect = state['rect']

    def __getstate__(self):
        data = self.__dict__.copy()
        del data['original_image']
        data['data'] = self.original_image.bits().tobytes()
        data['format'] = int(self.original_image.format())
        data['size'] = (self.original_image.width(), self.original_image.height())
        return data


class Chip:
    def __init__(self):
        self.valves: List[Valve] = []
        self.specifications: List[ProgramSpecification] = []
        self.programPresets: List[ProgramPreset] = []
        self.images: List[Image] = []
        self.text: List[Text] = []
