"""Undo and redo of chip edits, by snapshots of the chip.

A snapshot holds the chip's element lists and a copy of each element's fields. The elements
themselves are kept (not copied), so restoring writes values back into the same objects and
anything that refers to them (selection, canvas widgets, compiled programs, parameter values that
point at a valve or program) stays valid.

Each undo step is a (before, after) pair of snapshots. Undoing a step only reverts what that step
changed: the lists whose membership or order changed, and the element fields (and, for dicts such as
parameter values, the keys) that differ between before and after. Changes made outside of any step
(for example parameter values set while running) are left alone.
"""
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Tuple

from backend.chip import Chip

ELEMENT_LISTS = ("valves", "texts", "images", "programs")
HISTORY_LIMIT = 200

# {list name: [(element, {field name: value})]}, plus "scripts": [Script].
Snapshot = Dict[str, list]
Step = Tuple[Snapshot, Snapshot]

_MISSING = object()


def _copy_value(value: Any) -> Any:
    """Copies lists and dicts so later edits can't change a snapshot. Elements are kept by reference."""
    if isinstance(value, list):
        return [_copy_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _copy_value(v) for k, v in value.items()}
    return value


def take_snapshot(chip: Chip) -> Snapshot:
    snapshot = {name: [(e, {f.name: _copy_value(getattr(e, f.name)) for f in fields(e)})
                       for e in getattr(chip, name)] for name in ELEMENT_LISTS}
    snapshot["scripts"] = list(chip.scripts)
    return snapshot


def _merge(current: Any, old: Any, new: Any) -> Any:
    """[current] with the change from [old] to [new] applied, keeping anything else in [current]."""
    if old == new:
        return current
    if isinstance(current, dict) and isinstance(old, dict) and isinstance(new, dict):
        merged = {}
        for key in [*current, *(k for k in new if k not in current)]:
            value = _merge(current.get(key, _MISSING), old.get(key, _MISSING), new.get(key, _MISSING))
            if value is not _MISSING:
                merged[key] = value
        return merged
    return _copy_value(new)


def apply_change(chip: Chip, old: Snapshot, new: Snapshot):
    """Applies the change from snapshot [old] to snapshot [new] to [chip]."""
    for name in ELEMENT_LISTS:
        old_fields = dict(old[name])
        new_elements = [e for e, _ in new[name]]
        if [e for e, _ in old[name]] != new_elements:
            setattr(chip, name, new_elements)
        for element, values in new[name]:
            before = old_fields.get(element)
            for key, value in values.items():
                if before is None:
                    setattr(element, key, _copy_value(value))
                else:
                    merged = _merge(getattr(element, key), before[key], value)
                    if merged is not getattr(element, key):
                        setattr(element, key, merged)
    if old["scripts"] != new["scripts"]:
        chip.scripts = list(new["scripts"])


@dataclass(eq=False)
class History:
    # The chip as of the last recorded step (or the last accepted change).
    baseline: Snapshot = field(default_factory=dict)
    undo_steps: List[Step] = field(default_factory=list)
    redo_steps: List[Step] = field(default_factory=list)

    def reset(self, snapshot: Snapshot):
        self.baseline = snapshot
        self.undo_steps.clear()
        self.redo_steps.clear()

    def record(self, snapshot: Snapshot) -> bool:
        """Adds a step from the baseline to [snapshot], if they differ. Returns whether one was added."""
        if snapshot == self.baseline:
            return False
        self.undo_steps.append((self.baseline, snapshot))
        del self.undo_steps[:-HISTORY_LIMIT]
        self.redo_steps.clear()
        self.baseline = snapshot
        return True

    def accept(self, snapshot: Snapshot):
        """Makes [snapshot] the baseline without adding a step, so its changes can't be undone."""
        self.baseline = snapshot

    def pop_undo(self) -> Optional[Step]:
        if not self.undo_steps:
            return None
        step = self.undo_steps.pop()
        self.redo_steps.append(step)
        return step

    def pop_redo(self) -> Optional[Step]:
        if not self.redo_steps:
            return None
        step = self.redo_steps.pop()
        self.undo_steps.append(step)
        return step
