import typing

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QMenu, QTabWidget, QSplitter, QWidget, QTabBar, QApplication
from PySide6.QtGui import QColor, QAction, QMouseEvent
from PySide6.QtCore import Qt, QEvent, QPoint, QPointF
from random import randint
from enum import Enum, auto


class ProjectWindow(QFrame):
    class SplitDirection(Enum):
        NONE = auto()
        UP = auto()
        DOWN = auto()
        LEFT = auto()
        RIGHT = auto()

    class DraggingTab(QLabel):
        def __init__(self, initialPosition, widget: QWidget, text: str, mainWindow: QWidget,
                     originalTabWidget: QTabWidget, projectWindow: 'ProjectWindow'):
            super().__init__(text)
            self.widget = widget
            self.text = text
            self.initialPosition = initialPosition
            self.active = False
            self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
            self._originalTabWidget = originalTabWidget
            self._mainWindow = mainWindow
            self._projectWindow = projectWindow

            self._overlay = QFrame(self._mainWindow)
            self._overlay.setStyleSheet("""background-color: rgba(3, 248, 252, 0.5);""")

            self._currentPosition = initialPosition

            self._oldTab = None

        def Reposition(self, globalPos: QPoint):
            self._currentPosition = globalPos
            self.move(globalPos.x() - self.width() / 2, globalPos.y() - self.height() / 2)

            (tab, side) = self.GetTabUnder()
            if tab:
                if side is ProjectWindow.SplitDirection.DOWN:
                    leftCorner = QPointF(0, 0.5)
                    size = QPointF(1, 0.5)
                elif side is ProjectWindow.SplitDirection.UP:
                    leftCorner = QPointF(0, 0)
                    size = QPointF(1, 0.5)
                elif side is ProjectWindow.SplitDirection.LEFT:
                    leftCorner = QPointF(0, 0)
                    size = QPointF(0.5, 1)
                elif side is ProjectWindow.SplitDirection.RIGHT:
                    leftCorner = QPointF(0.5, 0)
                    size = QPointF(0.5, 1)
                else:
                    leftCorner = QPointF(0, 0)
                    size = QPointF(1, 1)
                currentWidget = tab.currentWidget()
                if currentWidget is None:
                    currentWidget = tab

                self._overlay.setParent(currentWidget)
                self._overlay.setVisible(True)
                self._overlay.move(QPoint(leftCorner.x() * currentWidget.width(),
                                          leftCorner.y() * currentWidget.height()))
                self._overlay.setFixedSize(size.x() * currentWidget.width(),
                                           size.y() * currentWidget.height())
            else:
                self._overlay.setVisible(False)

        def GetTabUnder(self):
            widget = self._mainWindow.childAt(self._mainWindow.mapFromGlobal(self._currentPosition))
            while widget:
                if isinstance(widget, QTabWidget):
                    currentWidget = widget.currentWidget()
                    if currentWidget is None:
                        break
                    # Figure out what side:
                    localPos = currentWidget.mapFromGlobal(self._currentPosition)
                    percentX = localPos.x() / currentWidget.width() - 0.5
                    percentY = localPos.y() / currentWidget.height() - 0.5

                    if abs(percentX) < 0.25 and abs(percentY) < 0.25:
                        side = ProjectWindow.SplitDirection.NONE
                    elif abs(percentX) > abs(percentY):
                        if percentX < 0:
                            side = ProjectWindow.SplitDirection.LEFT
                        else:
                            side = ProjectWindow.SplitDirection.RIGHT
                    else:
                        if percentY < 0:
                            side = ProjectWindow.SplitDirection.UP
                        else:
                            side = ProjectWindow.SplitDirection.DOWN
                    return widget, side
                else:
                    widget = widget.parent()

            return self._originalTabWidget, ProjectWindow.SplitDirection.NONE

        def Activate(self):
            self.active = True
            self.setVisible(True)
            self.widget.setParent(self)
            self.widget.setVisible(False)

        def Finish(self):
            if self.active:
                (tab, side) = self.GetTabUnder()
                tab.addTab(self.widget, self.text)
                tab.setCurrentWidget(self.widget)
                if side is not ProjectWindow.SplitDirection.NONE:
                    self._projectWindow.Split(tab, tab.indexOf(self.widget), side)
            self.deleteLater()
            self._overlay.deleteLater()

    def __init__(self):
        super().__init__()

        self._emptyWidget = QLabel("Create or open a project.")
        self._layout = QVBoxLayout()
        self._layout.addWidget(self._emptyWidget)
        self.setLayout(self._layout)

        self._draggingTab: typing.Optional[ProjectWindow.DraggingTab] = None

        for n in range(4):
            frame = QLabel("Frame " + str(n))
            self.AddTab(frame, "Frame " + str(n))

    def AddTab(self, widget: QWidget, text: str):
        if self.GetActiveTab() is None:
            newTabWidget = self.CreateTabWidget()
            self._layout.addWidget(newTabWidget)
            self._emptyWidget.setVisible(False)
        self.GetActiveTab().addTab(widget, text)

    def GetActiveTab(self):
        focusWidget = QApplication.focusWidget()
        print(focusWidget)
        while focusWidget:
            if isinstance(focusWidget, QTabWidget):
                return focusWidget
            else:
                focusWidget = focusWidget.parent()
        return self.GetFirstTab()

    def GetFirstTab(self):
        childrenToCheck = [self]
        while childrenToCheck:
            child = childrenToCheck.pop(0)
            if isinstance(child, QTabWidget):
                return child
            elif isinstance(child, QWidget):
                childrenToCheck += list(child.children())
        return None

    def CreateTabWidget(self):
        widget = QTabWidget()
        widget.setTabsClosable(True)
        widget.setMovable(True)
        widget.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        widget.tabBar().installEventFilter(self)
        widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        widget.tabBar().tabCloseRequested.connect(lambda index: self.CloseRequest(widget, index))
        widget.tabBar().customContextMenuRequested.connect(lambda pt: self.ShowContextMenu(widget, pt))
        return widget

    def eventFilter(self, watched: QTabBar, event) -> bool:
        if isinstance(event, QMouseEvent):
            if event.type() == QMouseEvent.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                widget = watched.parent().widget(watched.tabAt(event.pos()))
                text = watched.parent().tabText(watched.tabAt(event.pos()))
                self._draggingTab = ProjectWindow.DraggingTab(event.globalPos(), widget, text, self.topLevelWidget(),
                                                              watched.parent(), self)
                self._draggingTab.setVisible(False)
            elif event.type() == QMouseEvent.MouseMove and self._draggingTab is not None:
                if not self._draggingTab.active:
                    deltaY = abs(event.globalPos().y() - self._draggingTab.initialPosition.y())
                    if deltaY > watched.height() * 2:
                        self._draggingTab.Activate()
                else:
                    self._draggingTab.Reposition(event.globalPos())
                    return True
            elif event.type() == QMouseEvent.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                if self._draggingTab is not None:
                    self._draggingTab.Finish()
                    self._draggingTab = None
                    self.CheckCollapse(watched.parent())
        return False

    def ShowContextMenu(self, tabWidget: QTabWidget, position):
        tabIndex = tabWidget.tabBar().tabAt(position)
        if tabIndex != -1:
            menu = QMenu()
            splitUpAction = menu.addAction("Split Up")
            splitUpAction.triggered.connect(
                lambda: self.Split(tabWidget, tabIndex, ProjectWindow.SplitDirection.UP))
            splitDownAction = menu.addAction("Split Down")
            splitDownAction.triggered.connect(
                lambda: self.Split(tabWidget, tabIndex, ProjectWindow.SplitDirection.DOWN))
            splitLeftAction = menu.addAction("Split Left")
            splitLeftAction.triggered.connect(
                lambda: self.Split(tabWidget, tabIndex, ProjectWindow.SplitDirection.LEFT))
            splitRightAction = menu.addAction("Split Right")
            splitRightAction.triggered.connect(
                lambda: self.Split(tabWidget, tabIndex, ProjectWindow.SplitDirection.RIGHT))
            if tabWidget.count() == 1:
                splitUpAction.setEnabled(False)
                splitDownAction.setEnabled(False)
                splitLeftAction.setEnabled(False)
                splitRightAction.setEnabled(False)
            closeAction = menu.addAction("Close")
            closeAction.triggered.connect(lambda: self.CloseRequest(tabWidget, tabIndex))
            menu.exec_(tabWidget.tabBar().mapToGlobal(position))

    def Split(self, oldTabWidget: QTabWidget, tabIndex: int, direction: 'ProjectWindow.SplitDirection'):
        newTabWidget = self.CreateTabWidget()
        widget = oldTabWidget.widget(tabIndex)
        text = oldTabWidget.tabText(tabIndex)
        oldTabWidget.removeTab(tabIndex)
        newTabWidget.addTab(widget, text)

        oldSize = oldTabWidget.size()

        splitter = QSplitter()
        if direction is ProjectWindow.SplitDirection.UP or direction is ProjectWindow.SplitDirection.DOWN:
            splitter.setOrientation(Qt.Orientation.Vertical)
        else:
            splitter.setOrientation(Qt.Orientation.Horizontal)

        parent = oldTabWidget.parent()
        if parent == self:
            self._layout.removeWidget(oldTabWidget)
            self._layout.addWidget(splitter)
            splitter.addWidget(oldTabWidget)
        elif isinstance(parent, QSplitter):
            index = parent.indexOf(oldTabWidget)
            lastSizes = parent.sizes()
            splitter.addWidget(oldTabWidget)
            parent.insertWidget(index, splitter)
            parent.setSizes(lastSizes)

        if direction is ProjectWindow.SplitDirection.DOWN or direction is ProjectWindow.SplitDirection.RIGHT:
            splitter.addWidget(newTabWidget)
        else:
            splitter.insertWidget(0, newTabWidget)

        if direction is ProjectWindow.SplitDirection.UP or direction is ProjectWindow.SplitDirection.DOWN:
            splitter.setSizes([oldSize.height() / 2, oldSize.height() / 2])
        else:
            splitter.setSizes([oldSize.width() / 2, oldSize.width() / 2])

    def CloseRequest(self, tabWidget: QTabWidget, tabIndex: int):
        self.DoClose(tabWidget, tabIndex)

    def DoClose(self, tabWidget: QTabWidget, tabIndex: int):
        tabWidget.removeTab(tabIndex)
        self.CheckCollapse(tabWidget)

    def CheckCollapse(self, tabWidget: QTabWidget):
        if tabWidget.count() == 0:
            parent = tabWidget.parent()
            if parent == self:
                self._layout.removeWidget(tabWidget)
                self._emptyWidget.setVisible(True)
            elif isinstance(parent, QSplitter):
                widgetToKeep = parent.widget(1 - parent.indexOf(tabWidget))
                grandParent = parent.parent()
                if grandParent == self:
                    self._layout.removeWidget(parent)
                    self._layout.addWidget(widgetToKeep)
                elif isinstance(grandParent, QSplitter):
                    grandParent.replaceWidget(grandParent.indexOf(parent), widgetToKeep)
                parent.deleteLater()
            tabWidget.deleteLater()
