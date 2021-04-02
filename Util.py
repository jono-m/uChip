from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
import typing
from inspect import signature


class CleanSpinBox(QDoubleSpinBox):
    def textFromValue(self, val: float) -> str:
        if val.is_integer():
            return str(int(val))
        return repr(val)


class Event:
    class Listener:
        def __init__(self, discardOnSave, func: typing.Callable):
            self.discardOnSave = discardOnSave
            self.func = func

    def __init__(self):
        self._listeners: typing.List[Event.Listener] = []

    def Register(self, func: typing.Callable, discardOnSave=False):
        if func not in self._listeners:
            self._listeners.append(Event.Listener(discardOnSave, func))

    def Clear(self):
        self._listeners = []

    def Unregister(self, func: typing.Callable):
        for listener in self._listeners:
            if listener.func == func:
                self._listeners.remove(listener)
                return

    def Invoke(self, data: typing.Any = None):
        for listener in self._listeners.copy():
            sig = signature(listener.func)
            if len(sig.parameters) == 0:
                listener.func()
            else:
                listener.func(data)

    def __getstate__(self):
        state = self.__dict__.copy()
        state['_listeners'] = [x for x in state['_listeners'] if not x.discardOnSave]
        return state


class ColorIcon(QIcon):
    def __init__(self, filename, color: QColor):
        normalPixmap = QPixmap(filename)
        disabledPixmap = None

        if color is not None:
            tmp: QImage = normalPixmap.toImage()
            tmp2: QImage = normalPixmap.toImage()
            for x in range(tmp.height()):
                for y in range(tmp.width()):
                    normalColor = QColor(color)
                    normalColor.setAlpha(tmp.pixelColor(QPoint(x, y)).alpha())
                    tmp.setPixelColor(x, y, normalColor)
                    disabledColor = QColor(color)
                    disabledColor.setAlpha(tmp.pixelColor(QPoint(x, y)).alpha() / 2)
                    tmp2.setPixelColor(x, y, disabledColor)
            normalPixmap = QPixmap.fromImage(tmp)
            disabledPixmap = QPixmap.fromImage(tmp2)

        super().__init__(normalPixmap)

        if color is not None:
            self.addPixmap(disabledPixmap, QIcon.Disabled)
