"""A chip element on the canvas: its view (the widgets that show it, from gui/elements) in a graphics
proxy, placed at the element's position, plus the border the canvas shows when it's selected or hovered.
"""
from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt
from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsRectItem

from backend.chip import Element, Program
from backend.runner import Runner
from backend.session import Session
from gui.elements.element_ui import ElementView, build_element_view
from gui.elements.program import ProgramView


@dataclass(eq=False)
class CanvasItem:
    element: Element
    view: ElementView
    proxy: QGraphicsProxyWidget
    border: QGraphicsRectItem

    def rect(self) -> QRectF:
        return self.proxy.sceneBoundingRect()

    def refresh(self, editing: bool):
        """Updates the view and places it at the element's position."""
        # In edit mode the canvas takes all mouse input itself; widgets stay at full color but don't
        # react to hovering or take keyboard focus.
        if self.proxy.acceptHoverEvents() == editing:
            # Includes fold-outs attached to the element, such as a program's log.
            for item in [self.proxy, *self.proxy.childItems()]:
                if isinstance(item, QGraphicsProxyWidget):
                    item.setAcceptHoverEvents(not editing)
                    item.widget().setAttribute(Qt.WA_TransparentForMouseEvents, editing)
                    if editing:
                        item.clearFocus()
        self.view.refresh()

        # Programs size themselves, and have a scale instead.
        if isinstance(self.element, Program):
            position, size, scale = self.element.position, None, self.element.scale
        else:
            position, size, scale = self.element.rect[:2], self.element.rect[2:], 1.0
        if (self.proxy.pos().x(), self.proxy.pos().y()) != tuple(position):
            self.proxy.setPos(*position)
        if self.proxy.scale() != scale:
            self.proxy.setScale(scale)
        if size is not None and (self.proxy.size().width(), self.proxy.size().height()) != tuple(size):
            self.proxy.resize(*size)


def build_canvas_item(element: Element, session: Session, runner: Runner) -> CanvasItem:
    view = build_element_view(element, session, runner)
    proxy = QGraphicsProxyWidget()
    proxy.setWidget(view.widget)
    if isinstance(view, ProgramView):
        view.attach(proxy)
    return CanvasItem(element, view, proxy, QGraphicsRectItem())


def set_element_rect(element: Element, rect: QRectF):
    """Stores a moved/resized rect on the element. Programs size themselves, so only move."""
    # Rounded so snapped positions don't carry floating point noise into saved files.
    x, y, w, h = (round(v, 3) for v in (rect.x(), rect.y(), rect.width(), rect.height()))
    if isinstance(element, Program):
        element.position = [x, y]
    else:
        element.rect = [x, y, w, h]


def is_resizable(element: Element) -> bool:
    return not isinstance(element, Program)
