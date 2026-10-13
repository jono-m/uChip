"""Reading and writing chip projects as JSON.

File paths are stored relative to the project file's folder. Parameter values that refer to a valve
or program are stored as {"valve": index} or {"program": index} into the chip's lists.
"""
from pathlib import Path
from typing import Any

from backend.chip import Chip, Valve, Text, Image, Program, Script
from backend.json_io import read_json, write_json, path_to_json, path_from_json, optional

FILE_EXTENSION = ".uchip"
FILE_FILTER = "uChip project (*%s)" % FILE_EXTENSION
FORMAT_VERSION = 1


def _script_to_json(script: Script, base_dir: Path) -> dict:
    if script.is_builtin():
        return {"builtin": script.builtin}
    return {"path": path_to_json(script.path, base_dir)}


def _script_from_json(data: dict, base_dir: Path) -> Script:
    if "builtin" in data:
        return Script(builtin=data["builtin"])
    return Script(path=path_from_json(data["path"], base_dir))


def _value_to_json(value: Any, chip: Chip) -> Any:
    if isinstance(value, Valve):
        return {"valve": chip.valves.index(value)} if value in chip.valves else None
    if isinstance(value, Program):
        return {"program": chip.programs.index(value)} if value in chip.programs else None
    if isinstance(value, list):
        return [_value_to_json(v, chip) for v in value]
    return value


def _value_from_json(value: Any, chip: Chip) -> Any:
    if isinstance(value, dict) and "valve" in value:
        return chip.valves[value["valve"]]
    if isinstance(value, dict) and "program" in value:
        return chip.programs[value["program"]]
    if isinstance(value, list):
        return [_value_from_json(v, chip) for v in value]
    return value


def chip_to_json(chip: Chip, base_dir: Path) -> dict:
    return {
        "format": "uchip",
        "version": FORMAT_VERSION,
        "valves": [{"name": v.name, "solenoid": v.solenoid, "rect": list(v.rect)} for v in chip.valves],
        "texts": [{"text": t.text, "font_size": t.font_size, "color": optional(list, t.color), "rect": list(t.rect)}
                  for t in chip.texts],
        "images": [{"path": path_to_json(i.path, base_dir), "rect": list(i.rect)} for i in chip.images],
        "scripts": [_script_to_json(s, base_dir) for s in chip.scripts],
        "programs": [{
            "name": p.name,
            "script": _script_to_json(p.script, base_dir),
            "position": list(p.position),
            "scale": p.scale,
            "show_log": p.show_log,
            "parameters": {symbol: {"value": _value_to_json(value, chip),
                                    "visible": p.parameter_visibility.get(symbol, True)}
                           for symbol, value in p.parameter_values.items()},
        } for p in chip.programs],
    }


def chip_from_json(data: dict, base_dir: Path) -> Chip:
    if not isinstance(data, dict) or data.get("format") != "uchip":
        raise ValueError("Not a uChip project file.")
    if data.get("version", 0) > FORMAT_VERSION:
        raise ValueError("This project was saved by a newer version of uChip.")
    chip = Chip(
        valves=[Valve(name=v["name"], solenoid=v["solenoid"], rect=v["rect"]) for v in data["valves"]],
        texts=[Text(text=t["text"], font_size=t["font_size"], color=optional(tuple, t["color"]), rect=t["rect"])
               for t in data["texts"]],
        images=[Image(path=path_from_json(i["path"], base_dir), rect=i["rect"]) for i in data["images"]],
        scripts=[_script_from_json(s, base_dir) for s in data["scripts"]],
        programs=[Program(script=_script_from_json(p["script"], base_dir), name=p["name"],
                          position=p["position"], scale=p["scale"], show_log=p["show_log"])
                  for p in data["programs"]])
    # Parameter values can refer to any valve or program, so they are filled in once all exist.
    for program, p in zip(chip.programs, data["programs"]):
        for symbol, parameter in p["parameters"].items():
            program.parameter_values[symbol] = _value_from_json(parameter["value"], chip)
            program.parameter_visibility[symbol] = parameter["visible"]
    return chip


def save_chip(chip: Chip, path: Path):
    path = Path(path)
    write_json(chip_to_json(chip, path.absolute().parent), path)


def load_chip(path: Path) -> Chip:
    """Raises OSError if the file can't be read, or ValueError if it isn't a valid project."""
    path = Path(path)
    try:
        data = read_json(path)
    except ValueError:  # Includes undecodable text and invalid JSON.
        raise ValueError("'%s' is not a uChip project file." % path)
    try:
        return chip_from_json(data, path.absolute().parent)
    except ValueError:
        raise
    except Exception as e:  # Missing or mistyped entries, or references to valves or programs that don't exist.
        raise ValueError("'%s' is not a valid uChip project file (%s: %s)." % (path, type(e).__name__, e)) from e
