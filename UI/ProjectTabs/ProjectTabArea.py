import typing
from enum import Enum, auto

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QMenu, QTabWidget, QSplitter, QWidget, QTabBar, QApplication
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Qt, QPoint, QPointF, QTimer

from ProjectSystem.Project import Project
from ProjectSystem.ProjectTypes import ProjectType

from UI.ProjectTabs.ProjectTab import ProjectTab
from UI.ProjectTabs.ChipProjectTab import ChipProjectTab
from UI.ProjectTabs.ChipProgramTab import ChipProgramTab
from UI.ProjectTabs.BlockGraphTab import BlockGraphTab
from UI.ProjectTabs.BlockScriptTab import BlockScriptTab


class ProjectTabArea(QFrame):
    def __init__(self):
        super().__init__()

        self._emptyWidget = QLabel("Create or open a project.")
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._emptyWidget)
        self.setLayout(self._layout)

        self._draggedTab: typing.Optional[DraggedTab] = None

        self._titleUpdateTimer = QTimer(self)
        self._titleUpdateTimer.timeout.connect(self.UpdateTitles)
        self._titleUpdateTimer.start(500)

    def OpenTab(self, project: Project):
        if self.GetActiveTabWidget() is None:
            newTabWidget = self.CreateTabWidget()
            self._layout.addWidget(newTabWidget)
            self._emptyWidget.setVisible(False)
        self.GetActiveTabWidget().addTab(tab, tab.GetFormattedTitle())

    def GetActiveTabWidget(self):
        focusWidget = QApplication.focusWidget()
        while focusWidget:
            if isinstance(focusWidget, QTabWidget):
                return focusWidget
            else:
                focusWidget = focusWidget.parent()
        tabWidgets = self.GetTabWidgets()
        if tabWidgets:
            return tabWidgets[0]
        else:
            return None

    def GetTabWidgets(self):
        tabWidgets = []
        widgetsToCheck = [self]
        while widgetsToCheck:
            widgetToCheck = widgetsToCheck.pop(0)
            if isinstance(widgetToCheck, QTabWidget):
                tabWidgets.append(widgetToCheck)
            elif isinstance(widgetToCheck, QWidget):
                widgetsToCheck += list(widgetToCheck.children())
        return tabWidgets

    def FindTab(self, tab: ProjectTab) -> typing.Tuple[typing.Optional[QTabWidget], int]:
        for tabWidget in self.GetTabWidgets():
            matches = [index for index in range(tabWidget.count()) if tabWidget.widget(index) == tab]
            if matches:
                return tabWidget, matches[0]
        return None, -1

    def GetTabs(self) -> typing.List[ProjectTab]:
        tabs = []
        for tabWidget in self.GetTabWidgets():
            tabs += [tabWidget.widget(index) for index in range(tabWidget.count())]
        return tabs

    def SelectTab(self, tab: ProjectTab):
        (widget, number) = self.FindTab(tab)
        widget.setCurrentIndex(number)
        widget.focusWidget()

    def GetActiveTab(self) -> typing.Optional[ProjectTab]:
        activeWidget = self.GetActiveTabWidget()
        if activeWidget is not None:
            return activeWidget.currentWidget()
        return None

    def CreateTabWidget(self):
        widget = QTabWidget()
        widget.setTabsClosable(True)
        widget.setMovable(True)
        widget.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        widget.tabBar().installEventFilter(self)
        widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        widget.tabBar().tabCloseRequested.connect(lambda index: self.CloseRequest(widget.widget(index)))
        widget.tabBar().customContextMenuRequested.connect(lambda pt: self.ShowTabContextMenu(widget, pt))
        return widget

    def eventFilter(self, watched, event) -> bool:
        if isinstance(event, QMouseEvent):
            if isinstance(watched, QTabBar):
                if event.type() == QMouseEvent.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                    projectTab = watched.parent().widget(watched.tabAt(event.pos()))
                    self.TabDragStart(projectTab, watched.parent(), event.globalPos())
                elif event.type() == QMouseEvent.MouseMove:
                    return self.TabDrag(event.globalPos())
                elif event.type() == QMouseEvent.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                    self.TabDragFinish()
                    return True
        return False

    def TabDragStart(self, tab: ProjectTab, originalWidget: QTabWidget, position: QPoint):
        self._draggedTab = DraggedTab(tab, position, self, originalWidget, originalWidget.tabBar().height() * 2)
        self._draggedTab.setVisible(False)

    def TabDrag(self, position: QPoint):
        if self._draggedTab is None:
            return False
        self._draggedTab.Reposition(position)
        return self._draggedTab.IsActive()

    def TabDragFinish(self):
        if self._draggedTab is None:
            return
        self._draggedTab.Finish()
        self._draggedTab = None
        self.CheckCollapses()

    def ShowTabContextMenu(self, tabWidget: QTabWidget, position):
        tabIndex = tabWidget.tabBar().tabAt(position)
        if tabIndex != -1:
            menu = QMenu()
            splitUpAction = menu.addAction("Split Up")
            splitUpAction.triggered.connect(
                lambda: self.SplitTabWidget(tabWidget, tabIndex, SplitDirection.UP))
            splitDownAction = menu.addAction("Split Down")
            splitDownAction.triggered.connect(
                lambda: self.SplitTabWidget(tabWidget, tabIndex, SplitDirection.DOWN))
            splitLeftAction = menu.addAction("Split Left")
            splitLeftAction.triggered.connect(
                lambda: self.SplitTabWidget(tabWidget, tabIndex, SplitDirection.LEFT))
            splitRightAction = menu.addAction("Split Right")
            splitRightAction.triggered.connect(
                lambda: self.SplitTabWidget(tabWidget, tabIndex, SplitDirection.RIGHT))
            if tabWidget.count() == 1:
                splitUpAction.setEnabled(False)
                splitDownAction.setEnabled(False)
                splitLeftAction.setEnabled(False)
                splitRightAction.setEnabled(False)
            closeAction = menu.addAction("Close")
            closeAction.triggered.connect(lambda: self.CloseRequest(tabWidget.widget(tabIndex)))
            menu.exec_(tabWidget.tabBar().mapToGlobal(position))

    def SplitTabWidget(self, oldTabWidget: QTabWidget, tabIndexToMove: int,
                       direction: 'SplitDirection'):
        newTabWidget = self.CreateTabWidget()
        widget = oldTabWidget.widget(tabIndexToMove)
        text = oldTabWidget.tabText(tabIndexToMove)
        oldTabWidget.removeTab(tabIndexToMove)
        newTabWidget.addTab(widget, text)

        oldSize = oldTabWidget.size()

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        if direction is SplitDirection.UP or direction is SplitDirection.DOWN:
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

        if direction is SplitDirection.DOWN or direction is SplitDirection.RIGHT:
            splitter.addWidget(newTabWidget)
        else:
            splitter.insertWidget(0, newTabWidget)

        if direction is SplitDirection.UP or direction is SplitDirection.DOWN:
            splitter.setSizes([oldSize.height() / 2, oldSize.height() / 2])
        else:
            splitter.setSizes([oldSize.width() / 2, oldSize.width() / 2])

    def CloseRequest(self, tab: ProjectTab):
        if tab is None or not tab.RequestClose():
            return
        self.DoClose(tab)

    def DoClose(self, tab: ProjectTab):
        (tabWidget, tabIndex) = self.FindTab(tab)
        if tabWidget:
            tabWidget.removeTab(tabIndex)
        self.CheckCollapses()

    def UpdateTitles(self):
        for tabWidget in self.GetTabWidgets():
            [tabWidget.setTabText(tabIndex, tabWidget.widget(tabIndex).GetFormattedTitle()) for tabIndex in
             range(tabWidget.count())]

        activeTab = self.GetActiveTab()
        if activeTab:
            self.topLevelWidget().setWindowTitle("uChip - " + activeTab.GetFormattedTitle())
        else:
            self.topLevelWidget().setWindowTitle("uChip")

    def CheckCollapses(self):
        for tabWidget in self.GetTabWidgets():
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


class SplitDirection(Enum):
    STACK = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


class DraggedTab(QLabel):
    def __init__(self, projectTab: ProjectTab, initialPosition: QPoint, projectTabFrame: ProjectTabArea,
                 originalTabWidget: QTabWidget, activeThreshold: int):
        super().__init__(projectTab.GetFormattedTitle())
        self._projectTab = projectTab
        self._initialPosition = initialPosition
        self._originalTabWidget = originalTabWidget
        self._projectTabFrame = projectTabFrame
        self._activeThreshold = activeThreshold

        self._isActive = False
        self._overlay = QFrame(self._projectTabFrame.topLevelWidget())
        self._overlay.setStyleSheet("""background-color: rgba(3, 248, 252, 0.5);""")

        self._currentPosition = initialPosition

        self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)

    def IsActive(self):
        return self._isActive

    def Reposition(self, globalPos: QPoint):
        if not self._isActive:
            deltaY = abs(globalPos.y() - self._initialPosition.y())
            if deltaY > self._activeThreshold:
                self.Activate()
            else:
                return

        self._currentPosition = globalPos
        self.move(globalPos - QPoint(self.width(), self.height()) / 2)
        self.UpdateOverlay()

    def UpdateOverlay(self):
        tabWidget = self.GetTabWidgetUnder()
        side = self.ComputeSide(tabWidget)
        if tabWidget:
            if side is SplitDirection.DOWN:
                leftCorner = QPointF(0, 0.5)
                size = QPointF(1, 0.5)
            elif side is SplitDirection.UP:
                leftCorner = QPointF(0, 0)
                size = QPointF(1, 0.5)
            elif side is SplitDirection.LEFT:
                leftCorner = QPointF(0, 0)
                size = QPointF(0.5, 1)
            elif side is SplitDirection.RIGHT:
                leftCorner = QPointF(0.5, 0)
                size = QPointF(0.5, 1)
            else:
                leftCorner = QPointF(0, 0)
                size = QPointF(1, 1)

            targetWidget = tabWidget.currentWidget()
            if targetWidget is None:
                targetWidget = tabWidget

            self._overlay.setParent(targetWidget)
            self._overlay.setVisible(True)
            self._overlay.move(QPoint(leftCorner.x() * targetWidget.width(),
                                      leftCorner.y() * targetWidget.height()))
            self._overlay.setFixedSize(size.x() * targetWidget.width(),
                                       size.y() * targetWidget.height())
        else:
            self._overlay.setVisible(False)

    def ComputeSide(self, tabWidget: QTabWidget) -> SplitDirection:
        currentTab = tabWidget.currentWidget()
        if currentTab is None:
            return SplitDirection.STACK

        # Figure out what side:
        localPos = currentTab.mapFromGlobal(self._currentPosition)
        percentX = localPos.x() / currentTab.width() - 0.5
        percentY = localPos.y() / currentTab.height() - 0.5

        if abs(percentX) < 0.25 and abs(percentY) < 0.25:
            return SplitDirection.STACK
        elif abs(percentX) > abs(percentY):
            if percentX < 0:
                return SplitDirection.LEFT
            else:
                return SplitDirection.RIGHT
        else:
            if percentY < 0:
                return SplitDirection.UP
            else:
                return SplitDirection.DOWN

    def GetTabWidgetUnder(self):
        widget = self._projectTabFrame.topLevelWidget().childAt(
            self._projectTabFrame.topLevelWidget().mapFromGlobal(self._currentPosition))
        while widget:
            if isinstance(widget, QTabWidget):
                return widget
            else:
                widget = widget.parent()

        return self._originalTabWidget

    def Activate(self):
        self._isActive = True
        self.setVisible(True)
        self._projectTab.setParent(self)
        self._projectTab.setVisible(False)

    def Finish(self):
        if self._isActive:
            tabWidget = self.GetTabWidgetUnder()
            side = self.ComputeSide(tabWidget)
            tabWidget.addTab(self._projectTab, self._projectTab.GetFormattedTitle())
            tabWidget.setCurrentWidget(self._projectTab)
            if side is not SplitDirection.STACK:
                self._projectTabFrame.SplitTabWidget(tabWidget, tabWidget.indexOf(self._projectTab), side)
        self.deleteLater()
        self._overlay.deleteLater()
