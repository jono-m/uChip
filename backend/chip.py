"""The chip data model and the edits that can be made to it.

A chip is plain data: lists of valves, text annotations, images and programs, plus the user scripts
that have been imported into the project. Everything here is GUI-independent.
"""
import locale
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

BUILTIN_SCRIPTS_DIR = Path("assets/builtin_scripts")


@dataclass(eq=False)
class Valve:
    name: str = ""
    solenoid: int = 0
    rect: List[float] = field(default_factory=lambda: [0.0, 0.0, 100.0, 100.0])


@dataclass(eq=False)
class Text:
    text: str = "New text"
    font_size: int = 12
    # None uses the theme's text color.
    color: Optional[Tuple[int, int, int]] = None
    rect: List[float] = field(default_factory=lambda: [0.0, 0.0, 200.0, 50.0])


@dataclass(eq=False)
class Image:
    path: Path
    rect: List[float] = field(default_factory=lambda: [0.0, 0.0, 100.0, 100.0])


@dataclass(frozen=True)
class Script:
    """A script file on disk (path) or one bundled with uChip (builtin name). Exactly one is set."""
    path: Optional[Path] = None
    builtin: str = ""

    def is_builtin(self) -> bool:
        return self.path is None

    def file(self) -> Path:
        if self.is_builtin():
            return BUILTIN_SCRIPTS_DIR / (self.builtin + ".py")
        return self.path

    def name(self) -> str:
        return self.builtin if self.is_builtin() else self.path.stem

    def read(self) -> str:
        return read_script(self.file())


@dataclass(eq=False)
class Program:
    """An instance of a script placed on the chip, with its own parameter values."""
    script: Script
    name: str = ""
    position: List[float] = field(default_factory=lambda: [0.0, 0.0])
    scale: float = 1.0
    show_log: bool = True
    parameter_values: Dict[str, Any] = field(default_factory=dict)
    parameter_visibility: Dict[str, bool] = field(default_factory=dict)


Element = Union[Valve, Text, Image, Program]


def read_script(path: Path) -> str:
    """A script's text. Scripts are UTF-8; ones saved by older versions of uChip in the system encoding
    (e.g. cp1252) are read in that instead. Raises UnicodeDecodeError (a ValueError) if neither fits."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(path).read_text(encoding=locale.getpreferredencoding(False))


def write_script(path: Path, source: str):
    """Saves a script as UTF-8. The text is encoded before the file is opened, so text that can't be
    encoded raises UnicodeEncodeError without truncating the file."""
    source.encode("utf-8")
    Path(path).write_text(source, encoding="utf-8")


def builtin_scripts() -> List[Script]:
    return [Script(builtin=p.stem) for p in sorted(BUILTIN_SCRIPTS_DIR.glob("*.py"))]


def _offset(values: List[float], offset: Tuple[float, float]) -> List[float]:
    return [values[0] + offset[0], values[1] + offset[1], *values[2:]]


@dataclass(eq=False)
class Chip:
    valves: List[Valve] = field(default_factory=list)
    texts: List[Text] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    programs: List[Program] = field(default_factory=list)
    # User scripts imported into the project. Built-in scripts are always available and not listed.
    scripts: List[Script] = field(default_factory=list)

    def elements_of(self, element: Element) -> list:
        """The chip list that holds [element]'s type."""
        return {Valve: self.valves, Text: self.texts, Image: self.images, Program: self.programs}[type(element)]

    def all_elements(self) -> List[Element]:
        return [*self.images, *self.texts, *self.valves, *self.programs]

    # Scripts

    def available_scripts(self) -> List[Script]:
        """Built-in scripts first, then the project's scripts sorted by name."""
        return builtin_scripts() + sorted(self.scripts, key=Script.name)

    def script_in_use(self, script: Script) -> bool:
        return any(program.script == script for program in self.programs)

    def import_script(self, path: Path) -> Script:
        script = Script(path=Path(path).absolute())
        if script not in self.scripts:
            self.scripts.append(script)
        return script

    def remove_script(self, script: Script):
        if script.is_builtin():
            raise ValueError("Cannot remove a built-in script.")
        if self.script_in_use(script):
            raise ValueError("Cannot remove a script in use by the current project.")
        self.scripts.remove(script)

    def relocate_script(self, script: Script, new_path: Path) -> Script:
        """Points [script] (and every program using it) at a new file."""
        new_script = Script(path=Path(new_path).absolute())
        if new_script in self.scripts:
            raise ValueError("The script '%s' is already used in this project." % new_script.path)
        self.scripts[self.scripts.index(script)] = new_script
        for program in self.programs:
            if program.script == script:
                program.script = new_script
        return new_script

    # Adding, duplicating and removing elements

    def next_solenoid(self) -> int:
        return max([v.solenoid for v in self.valves] + [-1]) + 1

    def add_valve(self) -> Valve:
        number = self.next_solenoid()
        valve = Valve(name="Valve %d" % number, solenoid=number)
        self.valves.append(valve)
        return valve

    def add_text(self) -> Text:
        text = Text()
        self.texts.append(text)
        return text

    def add_image(self, path: Path, size: Tuple[float, float]) -> Image:
        image = Image(path=Path(path).absolute(), rect=[0.0, 0.0, float(size[0]), float(size[1])])
        self.images.append(image)
        return image

    def add_program(self, script: Script) -> Program:
        program = Program(script=script, name=script.name())
        self.programs.append(program)
        return program

    def remove_elements(self, elements: Sequence[Element]):
        for element in elements:
            self.elements_of(element).remove(element)

    def duplicate_element(self, element: Element, offset: Tuple[float, float] = (0, 0)) -> Element:
        if isinstance(element, Valve):
            # "Valve 3" duplicates to "Valve 4" on the next solenoid. Other names keep their name and
            # take the next free solenoid.
            match = re.match(r"(.*?)(\d+)", element.name)
            if match:
                copy = replace(element, name=match.group(1) + str(int(match.group(2)) + 1),
                               solenoid=element.solenoid + 1)
            else:
                copy = replace(element, solenoid=self.next_solenoid())
            copy.rect = _offset(element.rect, offset)
        elif isinstance(element, Program):
            copy = replace(element, position=_offset(element.position, offset),
                           parameter_values=element.parameter_values.copy(),
                           parameter_visibility=element.parameter_visibility.copy())
        else:
            copy = replace(element, rect=_offset(element.rect, offset))
        self.elements_of(element).append(copy)
        return copy

    def duplicate_elements(self, elements: Sequence[Element],
                           offset: Tuple[float, float] = (0, 0)) -> List[Element]:
        return [self.duplicate_element(element, offset) for element in elements]
