"""The inspector panel: edits the properties of the single selected element.

What it shows for each element type is defined with that type's canvas view, in gui/elements. The
panel's contents are rebuilt when the selection changes and refreshed from the element's data on every
refresh. Edits write straight to the element's data.
"""
from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from backend.chip import Element, Script
from backend.runner import Runner
from backend.session import Session
from gui.canvas.canvas import Canvas
from gui.elements.element_ui import ElementInspector, build_element_inspector
from gui.elements.program import ChooseScript
from gui.widgets import clear_layout


@dataclass(eq=False)
class Inspector:
    widget: QWidget
    layout: QVBoxLayout
    session: Session
    runner: Runner
    choose_script: ChooseScript
    edit_script: Callable[[Script], None]
    element: Optional[Element] = None
    element_inspector: Optional[ElementInspector] = None
    message: str = ""

    def show_message(self, message: str):
        clear_layout(self.layout)
        self.element_inspector = None
        self.message = message
        label = QLabel(message)
        label.setWordWrap(True)
        self.layout.addWidget(label)
        self.layout.addStretch(1)

    def show_element(self, element: Element):
        clear_layout(self.layout)
        self.message = ""
        self.element_inspector = build_element_inspector(element, self.layout, self.session, self.runner,
                                                         self.choose_script, self.edit_script)
        self.layout.addStretch(1)


def build_inspector(session: Session, runner: Runner, choose_script: ChooseScript,
                    edit_script: Callable[[Script], None]) -> Inspector:
    """[edit_script] opens a script in the script editor."""
    widget = QWidget()
    widget.setMinimumWidth(280)
    layout = QVBoxLayout(widget)
    inspector = Inspector(widget, layout, session, runner, choose_script, edit_script)
    inspector.show_message("Select an element to edit it.")
    return inspector


def refresh_inspector(inspector: Inspector, canvas: Canvas):
    selection = canvas.selection if canvas.editing else []
    target = selection[0] if len(selection) == 1 else None
    if target is not inspector.element:
        inspector.element = target
        if target is not None:
            inspector.show_element(target)
    if target is None:
        if not canvas.editing:
            message = "Switch to edit mode to change the chip."
        elif selection:
            message = "%d elements selected." % len(selection)
        else:
            message = "Select an element to edit it."
        if message != inspector.message:
            inspector.show_message(message)
        return
    inspector.element_inspector.refresh()
