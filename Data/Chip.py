from typing import Optional, List, Dict, Any, Union, Callable, Type
from pathlib import Path


class Chip:
    def __init__(self):
        self.valves: List[Valve] = []
        self.images: List[Image] = []
        self.text: List[Text] = []
        self.programs: List[Program] = []

        testP = Program()
        testP.name = "dummy"
        testP.path = Path(r"C:\Users\jonoj\Downloads\testChip.py")
        testP.scale = 1
        testP.position = [0, 0]
        self.programs.append(testP)


class Valve:
    def __init__(self):
        self.name = ""
        self.rect = [0, 0, 0, 0]
        self.solenoidNumber = 0


class Text:
    def __init__(self):
        self.rect = [0, 0, 0, 0]
        self.fontSize = 12
        self.text = "New annotation"
        self.color = (0, 0, 0)


class Image:
    def __init__(self):
        self.rect = [0, 0, 0, 0]
        self.path: Optional[Path] = None


class Program:
    def __init__(self):
        self.path: Optional[Path] = None
        self.position = [0, 0]
        self.scale = 1
        self.parameterValues: Dict[str, Any] = {}
        self.parameterVisibility: Dict[str, Any] = {}
        self.name = ""
