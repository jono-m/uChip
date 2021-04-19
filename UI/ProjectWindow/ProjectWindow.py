from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QMenu, QTabWidget, QSplitter
from PySide6.QtGui import QColor, QAction
from PySide6.QtGui import Qt
from random import randint


class ProjectWindow(QFrame):
    def __init__(self):
        super().__init__()

        rootTab = ProjectWindow.TabFrame()

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(rootTab)

        for n in range(4):
            frame = QLabel("Frame " + str(n))
            color = QColor(randint(0, 255),
                           randint(0, 255),
                           randint(0, 255))
            frame.setStyleSheet("background-color: " + color.name().upper())
            rootTab.tabs.addTab(frame, "Frame " + str(n))

    class TabFrame(QFrame):
        def __init__(self):
            super().__init__()

            self.tabs = QTabWidget()

            self.tabs.setMovable(True)
            self.tabs.setTabsClosable(True)
            self.tabs.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
            self.tabs.tabBar().customContextMenuRequested.connect(self.ShowContextMenu)
            self.tabs.tabCloseRequested.connect(self.CloseRequest)

            self._layout = QVBoxLayout()
            self._layout.addWidget(self.tabs)
            self.setLayout(self._layout)

        def ShowContextMenu(self, position):
            tab = self.tabs.tabBar().tabAt(position)
            if tab != -1:
                menu = QMenu()
                splitRightAction = menu.addAction("Split Right")
                splitRightAction.triggered.connect(lambda: self.SplitRight(tab))
                splitDownAction = menu.addAction("Split Down")
                splitDownAction.triggered.connect(lambda: self.SplitDown(tab))
                if self.tabs.count() == 1:
                    splitDownAction.setEnabled(False)
                    splitRightAction.setEnabled(False)
                closeAction = menu.addAction("Close")
                closeAction.triggered.connect(lambda: self.CloseRequest(tab))
                menu.exec_(self.tabs.mapToGlobal(position))

        def CloseRequest(self, tabIndex):
            self.tabs.removeTab(tabIndex)
            if self.tabs.count() == 0:
                self.deleteLater()

        def Split(self, tabIndex, orientation):
            self._layout.removeWidget(self.tabs)
            splitter = QSplitter()
            splitter.setOrientation(orientation)
            self._layout.addWidget(splitter)
            newA = ProjectWindow.TabFrame()
            newB = ProjectWindow.TabFrame()
            splitter.addWidget(newA)
            splitter.addWidget(newB)
            for index in reversed(range(self.tabs.count())):
                tab = self.tabs.widget(index)
                text = self.tabs.tabText(index)
                self.tabs.removeTab(index)
                if index == tabIndex:
                    newB.tabs.addTab(tab, text)
                else:
                    newA.tabs.addTab(tab, text)

        def SplitRight(self, tabIndex):
            self.Split(tabIndex, Qt.Orientation.Horizontal)

        def SplitDown(self, tabIndex):
            self.Split(tabIndex, Qt.Orientation.Vertical)
