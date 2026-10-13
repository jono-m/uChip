"""Documentation of the scripting API, read from ucscript's signatures and docstrings.

Editors use it for completions and hover help, so ucscript's docstrings are the one place the API is
described.
"""
import builtins
import inspect
import keyword
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List

from backend import ucscript

# The names scripts use, in the order they're documented. Members are completed after a ".".
API_NAMES = ["Parameter", "OptionsParameter", "ListParameter", "Valve", "Program", "ProgramFunction",
             "WaitForSeconds", "WaitForMinutes", "WaitForHours", "display", "onStop", "onPause", "onResume",
             "SetDescription", "FindValve", "FindProgram", "Log"]
API_MEMBERS = {"Parameter": ["Get", "Set"],
               "Valve": ["Open", "Close", "SetOpen", "IsOpen", "IsClosed", "Name", "SetName", "SolenoidNumber",
                         "SetSolenoidNumber"],
               "Program": ["Name", "SetName"],
               "ProgramFunction": ["IsRunning", "IsPaused", "Pause", "Resume", "Stop"]}


@dataclass(frozen=True)
class ApiSymbol:
    name: str
    signature: str  # e.g. "FindValve(name: str) -> Valve" or "Valve.Open()"
    doc: str
    member: bool  # A method of one of the API's classes.


def _signature(obj, drop_self: bool) -> str:
    try:
        signature = inspect.signature(obj)
    except (TypeError, ValueError):
        return "()"
    if drop_self:
        signature = signature.replace(parameters=list(signature.parameters.values())[1:])
    return str(signature).replace("typing.", "").replace("backend.ucscript.", "")


@lru_cache(maxsize=None)
def api_symbols() -> List[ApiSymbol]:
    symbols = []
    for name in API_NAMES:
        obj = getattr(ucscript, name)
        symbols.append(ApiSymbol(name, name + _signature(obj, False), inspect.getdoc(obj) or "", False))
        for member in API_MEMBERS.get(name, []):
            method = getattr(obj, member)
            symbols.append(ApiSymbol(member, "%s.%s%s" % (name, member, _signature(method, True)),
                                     inspect.getdoc(method) or "", True))
    return symbols


@lru_cache(maxsize=None)
def api_docs() -> Dict[str, List[ApiSymbol]]:
    """API symbols by name. A name can have several (e.g. Valve.Name and Program.Name)."""
    docs: Dict[str, List[ApiSymbol]] = {}
    for symbol in api_symbols():
        docs.setdefault(symbol.name, []).append(symbol)
    return docs


PYTHON_KEYWORDS = sorted(keyword.kwlist)
PYTHON_BUILTINS = sorted(name for name in dir(builtins) if not name.startswith("_"))
