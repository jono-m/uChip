"""A session is an open chip together with the rig it controls.

This is the state a front end (the GUI, or a command-line tool) works with: the chip, where it is
saved and whether it has unsaved changes, and the rig. Running the chip's programs is the runner's job.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from backend import project_file
from backend.chip import Chip
from backend.history import History, apply_change, take_snapshot
from backend.rig import Rig


@dataclass(eq=False)
class Session:
    chip: Chip = field(default_factory=Chip)
    path: Optional[Path] = None
    rig: Rig = field(default_factory=Rig)
    # The chip as last saved or opened, used to tell whether it has unsaved changes.
    saved_json: dict = field(default_factory=dict)
    history: History = field(default_factory=History)

    def _base_dir(self) -> Path:
        return self.path.absolute().parent if self.path is not None else Path.cwd()

    def set_chip(self, chip: Chip, path: Optional[Path]):
        self.chip = chip
        self.path = Path(path) if path is not None else None
        self.saved_json = project_file.chip_to_json(chip, self._base_dir())
        self.history.reset(take_snapshot(chip))

    def new_chip(self):
        self.set_chip(Chip(), None)

    def open_chip(self, path: Path):
        self.set_chip(project_file.load_chip(path), path)

    def save_chip(self, path: Optional[Path] = None):
        """Saves to [path], or to the current path if none is given."""
        path = Path(path) if path is not None else self.path
        if path is None:
            raise ValueError("No path to save the chip to.")
        project_file.save_chip(self.chip, path)
        self.path = path
        self.saved_json = project_file.chip_to_json(self.chip, self._base_dir())

    def is_modified(self) -> bool:
        return project_file.chip_to_json(self.chip, self._base_dir()) != self.saved_json

    # Undo and redo

    def record_edit(self) -> bool:
        """Adds an undo step for the chip's changes since the last step. Returns whether there were any."""
        return self.history.record(take_snapshot(self.chip))

    def accept_changes(self):
        """Keeps the chip's changes since the last step without making them undoable."""
        self.history.accept(take_snapshot(self.chip))

    def undo(self):
        self.record_edit()
        step = self.history.pop_undo()
        if step is not None:
            apply_change(self.chip, step[1], step[0])
            self.accept_changes()

    def redo(self):
        self.record_edit()
        step = self.history.pop_redo()
        if step is not None:
            apply_change(self.chip, step[0], step[1])
            self.accept_changes()

    def chip_name(self) -> str:
        return "New Chip" if self.path is None else self.path.stem


def new_session(rig: Optional[Rig] = None) -> Session:
    session = Session(rig=rig if rig is not None else Rig())
    session.new_chip()
    return session
