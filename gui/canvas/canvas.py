"""The chip canvas: shows the chip's elements and lets the user arrange them.

The canvas mirrors the chip. Each refresh it creates widgets for new elements, removes widgets for
deleted elements and updates the rest, so edits only ever need to change the chip data.

In edit mode, left-dragging selects, moves and resizes elements. Otherwise clicks go to the element
widgets (valve buttons, program controls). Right-drag pans and the wheel zooms in both modes.
"""
from dataclasses import dataclass, field
from functools import reduce
from typing import Dict, List, Optional

from PySide6.QtCore import QMarginsF, QPoint, QPointF, QRectF, QSizeF, Qt
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QPainter, QPalette, QPen, QTransform
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QGraphicsProxyWidget, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsView)

from backend.chip import Element
from backend.runner import Runner
from backend.session import Session
from gui.canvas.canvas_item import CanvasItem, build_canvas_item, is_resizable, set_element_rect
from gui.widgets import ErrorReporter

GRID_SPACING = 50.0
GRID_MIN_ZOOM = 0.25
MIN_ZOOM, MAX_ZOOM = 0.05, 2.0
WHEEL_SENSITIVITY = 1 / 1000
HANDLE_PIXELS = 7
OVERLAY_Z = 1e9

# Resize handles, in order: top-left, top, top-right, left, right, bottom-left, bottom, bottom-right.
HANDLE_CURSORS = [Qt.SizeFDiagCursor, Qt.SizeVerCursor, Qt.SizeBDiagCursor, Qt.SizeHorCursor,
                  Qt.SizeHorCursor, Qt.SizeBDiagCursor, Qt.SizeVerCursor, Qt.SizeFDiagCursor]


@dataclass(eq=False)
class Drag:
    kind: str  # "pan", "move", "resize" or "band"
    start: QPointF  # Scene position where the drag started.
    start_rects: List[QRectF] = field(default_factory=list)
    handle: int = -1
    last_view_position: QPoint = field(default_factory=QPoint)


def _accent() -> QColor:
    """The theme's selection color (the Windows accent color)."""
    return QApplication.palette().color(QPalette.Highlight)


def _grid_color() -> QColor:
    """A faint line in the theme's text color, visible on light and dark backgrounds."""
    color = QColor(QApplication.palette().color(QPalette.WindowText))
    color.setAlpha(28)
    return color


def _bounds(rects: List[QRectF]) -> Optional[QRectF]:
    return reduce(QRectF.united, rects) if rects else None


def _handle_positions(r: QRectF) -> List[QPointF]:
    c = r.center()
    return [r.topLeft(), QPointF(c.x(), r.top()), r.topRight(), QPointF(r.left(), c.y()),
            QPointF(r.right(), c.y()), r.bottomLeft(), QPointF(c.x(), r.bottom()), r.bottomRight()]


def snap(x: float) -> float:
    if QGuiApplication.keyboardModifiers() & Qt.AltModifier:
        return x
    return round(x / GRID_SPACING) * GRID_SPACING


def snap_point(p: QPointF) -> QPointF:
    return QPointF(snap(p.x()), snap(p.y()))


def _is_multi_select() -> bool:
    return QGuiApplication.keyboardModifiers() == Qt.ShiftModifier


@dataclass(eq=False)
class Canvas:
    session: Session
    runner: Runner
    view: "CanvasView"
    scene: QGraphicsScene
    selection_box: QGraphicsRectItem
    band: QGraphicsRectItem
    handles: List[QGraphicsRectItem]
    items: Dict[Element, CanvasItem] = field(default_factory=dict)
    selection: List[Element] = field(default_factory=list)
    editing: bool = True
    zoom: float = 1.0
    center: QPointF = field(default_factory=QPointF)
    drag: Optional[Drag] = None
    hovered: List[Element] = field(default_factory=list)
    # Errors refreshing each element's view, so one failing element doesn't stop the others refreshing.
    errors: ErrorReporter = field(default_factory=ErrorReporter)

    # View

    def apply_view(self):
        self.view.setTransform(QTransform.fromScale(self.zoom, self.zoom))
        # A tiny scene rect at the view center makes the view centered on it with nothing to scroll.
        self.view.setSceneRect(QRectF(self.center, QSizeF(1, 1)))
        self.update_overlays()

    def zoom_at(self, scene_anchor: QPointF, zoom: float):
        """Zooms keeping [scene_anchor] at the same place on screen."""
        view_anchor = self.view.mapFromScene(scene_anchor)
        self.zoom = min(max(zoom, MIN_ZOOM), MAX_ZOOM)
        self.apply_view()
        self.center -= self.view.mapToScene(view_anchor) - scene_anchor
        self.apply_view()

    def zoom_to_fit(self):
        bounds = _bounds([item.rect() for item in self.items.values()])
        if bounds is None or bounds.isEmpty():
            return
        viewport = self.view.viewport().size()
        self.zoom = min(max(0.9 * min(viewport.width() / bounds.width(), viewport.height() / bounds.height()),
                            MIN_ZOOM), MAX_ZOOM)
        self.center = bounds.center()
        self.apply_view()

    def center_on_selection(self):
        bounds = _bounds(self._selected_rects())
        if bounds is not None:
            self.center = bounds.center()
            self.apply_view()

    # Elements and selection

    def refresh(self):
        """Matches the canvas items to the chip's elements and updates them."""
        wanted = self.session.chip.all_elements()
        for element in [d for d in self.items if d not in wanted]:
            item = self.items.pop(element)
            self.errors.forget(element)
            self.scene.removeItem(item.proxy)
            self.scene.removeItem(item.border)
        for z, element in enumerate(wanted):
            self.errors.run(element, lambda: self._refresh_item(element, z, len(wanted)))
        self.selection = [d for d in self.selection if d in self.items]
        self.update_overlays()

    def _refresh_item(self, element: Element, z: int, count: int):
        """Creates [element]'s item if it has none, and updates it. It is stacked at [z] of [count]."""
        item = self.items.get(element)
        if item is None:
            item = self.items[element] = build_canvas_item(element, self.session, self.runner)
            self.scene.addItem(item.proxy)
            self.scene.addItem(item.border)
        item.refresh(self.editing)
        # Elements with something folded out (a program's log) are raised so it isn't hidden under others.
        if any(child.isVisible() for child in item.proxy.childItems()):
            z += count
        if item.proxy.zValue() != z:
            item.proxy.setZValue(z)

    def select(self, elements: List[Element]):
        self.scene.clearFocus()
        self.selection = list(elements)
        self.update_overlays()

    def set_editing(self, editing: bool):
        self.editing = editing
        self.drag = None
        self.select([])
        self.refresh()
        self.view.viewport().unsetCursor()
        self.scene.update()

    def place_at_center(self, element: Element):
        """Moves a newly added element to the middle of the view and selects it."""
        self.refresh()
        rect = self.items[element].rect()
        rect.moveCenter(self.center)
        rect.moveTopLeft(snap_point(rect.topLeft()))
        set_element_rect(element, rect)
        self.refresh()
        self.select([element])

    def _selected_rects(self) -> List[QRectF]:
        return [self.items[d].rect() for d in self.selection if d in self.items]

    def update_overlays(self):
        """Shows borders on selected/hovered elements, the selection box and the resize handles."""
        for element, item in self.items.items():
            selected, hovered = element in self.selection, element in self.hovered
            item.border.setVisible(self.editing and (selected or hovered))
            if item.border.isVisible():
                pen = QPen(_accent(), 3 if selected else 2)
                pen.setCosmetic(True)
                item.border.setPen(pen)
                item.border.setRect(item.rect())
                item.border.setZValue(OVERLAY_Z - 1)

        bounds = _bounds(self._selected_rects())
        pixel = 1 / self.zoom
        self.selection_box.setVisible(bounds is not None)
        show_handles = bounds is not None and any(is_resizable(d) for d in self.selection)
        if bounds is not None:
            bounds = bounds.marginsAdded(QMarginsF(4 * pixel, 4 * pixel, 4 * pixel, 4 * pixel))
            self.selection_box.setRect(bounds)
            for handle, position in zip(self.handles, _handle_positions(bounds)):
                size = HANDLE_PIXELS * pixel
                handle.setRect(QRectF(position - QPointF(size / 2, size / 2), QSizeF(size, size)))
        for handle in self.handles:
            handle.setVisible(show_handles)

    def element_at(self, position: QPointF) -> Optional[Element]:
        hits = [item for item in self.items.values() if item.rect().contains(position)]
        return max(hits, key=lambda item: item.proxy.zValue()).element if hits else None

    def elements_in(self, rect: QRectF) -> List[Element]:
        return [d for d, item in self.items.items() if item.rect().intersects(rect)]

    def handle_at(self, position: QPointF) -> int:
        return next((i for i, h in enumerate(self.handles) if h.isVisible() and h.rect().contains(position)), -1)

    # Moving and resizing

    def _move(self, position: QPointF):
        delta = position - self.drag.start
        for element, start in zip(self.selection, self.drag.start_rects):
            rect = start.translated(delta)
            # Snap whichever corner is closest to a grid point.
            corners = [rect.topLeft(), rect.topRight(), rect.bottomLeft(), rect.bottomRight()]
            offsets = [snap_point(c) - c for c in corners]
            set_element_rect(element, rect.translated(min(offsets, key=lambda o: o.x() ** 2 + o.y() ** 2)))

    def _resize(self, position: QPointF):
        delta = position - self.drag.start
        initial = _bounds(self.drag.start_rects)
        new = QRectF(initial)
        handle = self.drag.handle
        if handle == 0:
            new.setTopLeft(snap_point(new.topLeft() + delta))
        elif handle == 1:
            new.setTop(snap(new.top() + delta.y()))
        elif handle == 2:
            new.setTopRight(snap_point(new.topRight() + delta))
        elif handle == 3:
            new.setLeft(snap(new.left() + delta.x()))
        elif handle == 4:
            new.setRight(snap(new.right() + delta.x()))
        elif handle == 5:
            new.setBottomLeft(snap_point(new.bottomLeft() + delta))
        elif handle == 6:
            new.setBottom(snap(new.bottom() + delta.y()))
        elif handle == 7:
            new.setBottomRight(snap_point(new.bottomRight() + delta))
        new = new.normalized()
        if initial.width() <= 0 or initial.height() <= 0:
            return

        def transform(p: QPointF) -> QPointF:
            return QPointF((p.x() - initial.x()) / initial.width() * new.width() + new.x(),
                           (p.y() - initial.y()) / initial.height() * new.height() + new.y())

        # Every selected element scales with the selection box.
        for element, start in zip(self.selection, self.drag.start_rects):
            if is_resizable(element):
                set_element_rect(element, QRectF(transform(start.topLeft()), transform(start.bottomRight())))

    # Input

    def _scene_position(self, event) -> QPointF:
        return self.view.mapToScene(event.position().toPoint())

    def _update_cursor(self, position: QPointF):
        """Shows what a left click would do here: resize at a handle, select and move over an element."""
        drag = self.drag
        if drag is not None and drag.kind == "pan":
            shape = Qt.ClosedHandCursor
        elif not self.editing:
            shape = None
        elif drag is not None and drag.kind == "resize":
            shape = HANDLE_CURSORS[drag.handle]
        elif drag is not None and drag.kind == "move":
            shape = Qt.SizeAllCursor
        elif drag is None and self.handle_at(position) >= 0:
            shape = HANDLE_CURSORS[self.handle_at(position)]
        elif drag is None and self.element_at(position) is not None and not _is_multi_select():
            shape = Qt.SizeAllCursor
        else:
            shape = None
        if shape is None:
            self.view.viewport().unsetCursor()
        else:
            self.view.viewport().setCursor(shape)

    def on_mouse_press(self, event) -> bool:
        """Returns True if the canvas handled the press, False to pass it on to the element widgets."""
        position = self._scene_position(event)
        if self.drag is not None:
            return True
        if event.button() == Qt.RightButton:
            self.drag = Drag("pan", position, last_view_position=event.position().toPoint())
        elif event.button() != Qt.LeftButton or not self.editing:
            return False
        elif self.handle_at(position) >= 0:
            self.drag = Drag("resize", position, self._selected_rects(), self.handle_at(position))
        elif self.element_at(position) is not None:
            element = self.element_at(position)
            if _is_multi_select():
                self.select([d for d in self.selection if d is not element] +
                            ([] if element in self.selection else [element]))
            else:
                if element not in self.selection:
                    self.select([element])
                self.drag = Drag("move", position, self._selected_rects())
        else:
            self.drag = Drag("band", position)
            self.band.setRect(QRectF(position, QSizeF()))
            self.band.setVisible(True)
        self._update_cursor(position)
        return True

    def on_mouse_move(self, event) -> bool:
        position = self._scene_position(event)
        drag = self.drag
        if drag is None:
            hovered = self.element_at(position) if self.editing else None
            self.hovered = [hovered] if hovered is not None else []
            self.update_overlays()
            self._update_cursor(position)
            # In edit mode the move isn't passed on, so the element widgets' own cursors don't replace the canvas's.
            return self.editing
        if drag.kind == "pan":
            view_position = event.position().toPoint()
            self.center -= QPointF(view_position - drag.last_view_position) / self.zoom
            drag.last_view_position = view_position
            self.apply_view()
        elif drag.kind == "move":
            self._move(position)
            self.refresh()
        elif drag.kind == "resize":
            self._resize(position)
            self.refresh()
        elif drag.kind == "band":
            self.band.setRect(QRectF(drag.start, position).normalized())
            self.hovered = self.elements_in(self.band.rect())
            self.update_overlays()
        return True

    def on_mouse_release(self, event) -> bool:
        drag = self.drag
        if drag is None:
            return False
        if (drag.kind == "pan") != (event.button() == Qt.RightButton):
            return True
        self.drag = None
        if drag.kind == "band":
            self.band.setVisible(False)
            in_band = self.elements_in(self.band.rect())
            self.hovered = []
            if _is_multi_select():
                self.select([d for d in self.selection if d not in in_band] +
                            [d for d in in_band if d not in self.selection])
            else:
                self.select(in_band)
        self._update_cursor(self._scene_position(event))
        return True

    def _over_scroll_area(self, position: QPointF) -> bool:
        """Whether [position] is over a scrollable widget (e.g. a program log) that should get the wheel."""
        if self.editing:
            return False
        # The topmost widget there, which may be an element or something attached to one (a program's log).
        proxy = next((i for i in self.scene.items(position) if isinstance(i, QGraphicsProxyWidget)), None)
        if proxy is None:
            return False
        widget = proxy.widget().childAt(proxy.mapFromScene(position).toPoint())
        while widget is not None:
            if isinstance(widget, QAbstractScrollArea):
                return True
            widget = widget.parentWidget()
        return False

    def on_wheel(self, event) -> bool:
        position = self._scene_position(event)
        if self._over_scroll_area(position):
            return False
        self.zoom_at(position, self.zoom + event.angleDelta().y() * WHEEL_SENSITIVITY)
        event.accept()
        return True

    def draw_grid(self, painter: QPainter, rect: QRectF):
        if not self.editing or self.zoom <= GRID_MIN_ZOOM:
            return
        painter.setPen(QPen(_grid_color(), 1))
        x = rect.left() - rect.left() % GRID_SPACING
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += GRID_SPACING
        y = rect.top() - rect.top() % GRID_SPACING
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += GRID_SPACING


# Subclassed because Qt only delivers mouse input and background painting through these overrides.
class CanvasView(QGraphicsView):
    canvas: Canvas = None

    def mousePressEvent(self, event):
        if not self.canvas.on_mouse_press(event):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.canvas.on_mouse_move(event):
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.canvas.on_mouse_release(event):
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if not self.canvas.on_wheel(event):
            super().wheelEvent(event)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if self.canvas is not None:
            self.canvas.draw_grid(painter, rect)


def build_canvas(session: Session, runner: Runner) -> Canvas:
    scene = QGraphicsScene()
    # No spatial index: the scene is small and its items move and resize all the time. With the default BSP
    # index, the index kept pointers to removed (and deleted) element items, and the next render crashed
    # (e.g. after File > New or Open, or deleting most of a chip's elements).
    scene.setItemIndexMethod(QGraphicsScene.NoIndex)
    view = CanvasView(scene)
    view.setMouseTracking(True)
    view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    view.setBackgroundBrush(view.palette().color(QPalette.Base))

    def overlay(filled: bool) -> QGraphicsRectItem:
        rect = QGraphicsRectItem()
        pen = QPen(_accent(), 1 if filled else 2)
        pen.setCosmetic(True)  # Constant width on screen regardless of zoom.
        rect.setPen(pen)
        rect.setBrush(QBrush(QApplication.palette().color(QPalette.Base)) if filled else Qt.NoBrush)
        rect.setZValue(OVERLAY_Z)
        rect.setVisible(False)
        scene.addItem(rect)
        return rect

    canvas = Canvas(session, runner, view, scene, overlay(False), overlay(False), [overlay(True) for _ in range(8)])
    view.canvas = canvas
    canvas.apply_view()
    return canvas
