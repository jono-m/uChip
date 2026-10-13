"""General helpers for reading and writing JSON files, shared by project and rig settings files."""
import json
import os
import re
from pathlib import Path
from typing import Any

_SCALAR = r"(?:-?[\d.eE+-]+|true|false|null)"
_SCALAR_LIST = re.compile(r"\[\s*(%s(?:,\s*%s)*)\s*\]" % (_SCALAR, _SCALAR))


def dumps(data) -> str:
    """Indented JSON, with lists of numbers/booleans (e.g. rects) kept on one line."""
    return _SCALAR_LIST.sub(lambda m: "[" + ", ".join(re.split(r",\s*", m.group(1))) + "]",
                            json.dumps(data, indent=2))


def write_json(data, path: Path):
    Path(path).write_text(dumps(data))


def read_json(path: Path) -> Any:
    """Raises ValueError if the file is not valid JSON text."""
    return json.loads(Path(path).read_text())


def path_to_json(path: Path, base_dir: Path) -> str:
    """[path] relative to [base_dir] where possible, with forward slashes."""
    try:
        return Path(os.path.relpath(path, base_dir)).as_posix()
    except ValueError:  # Different drive on Windows; relative path impossible.
        return Path(path).as_posix()


def path_from_json(text: str, base_dir: Path) -> Path:
    return Path(os.path.normpath(base_dir / text))


def optional(convert, value):
    """[convert](value), passing None through unchanged."""
    return convert(value) if value is not None else None
