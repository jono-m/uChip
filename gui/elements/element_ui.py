"""Picks the canvas view and the inspector for an element's type, giving each only what it uses."""
from typing import Callable, Union

from PySide6.QtWidgets import QVBoxLayout

from backend.chip import Element, Image, Program, Script, Text, Valve
from backend.runner import Runner
from backend.session import Session
from gui.elements.image import ImageInspector, ImageView, build_image_inspector, build_image_view
from gui.elements.program import (ChooseScript, ProgramInspector, ProgramView, build_program_inspector,
                                  build_program_view)
from gui.elements.text import TextInspector, TextView, build_text_inspector, build_text_view
from gui.elements.valve import ValveInspector, ValveView, build_valve_inspector, build_valve_view

ElementView = Union[ValveView, TextView, ImageView, ProgramView]
ElementInspector = Union[ValveInspector, TextInspector, ImageInspector, ProgramInspector]


def build_element_view(element: Element, session: Session, runner: Runner) -> ElementView:
    if isinstance(element, Valve):
        return build_valve_view(element, session.rig)
    if isinstance(element, Text):
        return build_text_view(element)
    if isinstance(element, Image):
        return build_image_view(element)
    if isinstance(element, Program):
        return build_program_view(element, session.chip, runner)
    raise TypeError("No view for %r" % element)


def build_element_inspector(element: Element, layout: QVBoxLayout, session: Session, runner: Runner,
                            choose_script: ChooseScript, edit_script: Callable[[Script], None]) -> ElementInspector:
    """Adds the fields for editing [element] to [layout]."""
    if isinstance(element, Valve):
        return build_valve_inspector(element, layout)
    if isinstance(element, Text):
        return build_text_inspector(element, layout)
    if isinstance(element, Image):
        return build_image_inspector(element, layout)
    if isinstance(element, Program):
        return build_program_inspector(element, layout, session.chip, runner, choose_script, edit_script)
    raise TypeError("No inspector for %r" % element)
