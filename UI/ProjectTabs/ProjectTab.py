from pathlib import Path

from PySide6.QtWidgets import QWidget, QToolButton, QVBoxLayout, QHBoxLayout, QSizePolicy, QMessageBox
from PySide6.QtCore import Qt

from ProjectSystem.Project import Project


class ProjectTab(QWidget):
    def __init__(self, project: Project):
        super().__init__()

        self._project = project

        self.leftBar = self.CreateLeftBar()
        self.rightBar = self.CreateRightBar()
        self.bottomBar = self.CreateBottomBar()
        self.centerView = self.CreateCenterView()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sub = QVBoxLayout()
        sub.setContentsMargins(0, 0, 0, 0)
        sub.setSpacing(0)
        sub.addWidget(self.centerView, stretch=1)
        sub.addWidget(Collapsible(self.bottomBar, Qt.AlignBottom), stretch=0)
        layout.addWidget(Collapsible(self.leftBar, Qt.AlignLeft), stretch=0)
        layout.addLayout(sub, stretch=1)
        layout.addWidget(Collapsible(self.rightBar, Qt.AlignRight), stretch=0)
        self.setLayout(layout)

    def CreateLeftBar(self):
        return QWidget()

    def CreateRightBar(self):
        return QWidget()

    def CreateBottomBar(self):
        return QWidget()

    def CreateCenterView(self):
        return QWidget()

    def GetProject(self):
        return self._project

    def GetPath(self):
        return self._project.GetProjectPath()

    def Save(self):
        self._project.Save()

    def SaveAs(self, filename: Path):
        if filename is None:
            return
        self._project.SaveAs(filename)

    def RequestClose(self):
        if self.PromptClose():
            self._project.Close()
            return True
        else:
            return False

    def PromptClose(self):
        if self.HasBeenModified():
            confirmBox = QMessageBox.warning(self, "Confirm Close",
                                             "'" + self.GetTitle() + "' has been modified. Do you want to save changes?",
                                             QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                             QMessageBox.Save)
            if confirmBox == QMessageBox.Save:
                self.Save()
                return True
            elif confirmBox == QMessageBox.Discard:
                return True
            else:
                return False
        return True

    def GetTitle(self):
        return self._project.GetProjectName()

    def GetFormattedTitle(self):
        if self.HasBeenModified():
            return self.GetTitle() + " * "
        else:
            return self.GetTitle()

    def HasBeenModified(self):
        return self._project.HasBeenModified()


class Collapsible(QWidget):
    arrows = {'left': u"\u02C2",
              'right': u"\u02C3",
              'up': u"\u02C4",
              'down': u"\u02C5"}

    def __init__(self, content: QWidget, side: Qt.Alignment):
        super().__init__()

        self.content = content
        self.side = side
        self.toggleButton = QToolButton()
        self.toggleButton.clicked.connect(self.Toggle)
        self._collapsed = False

        if side == Qt.AlignTop:
            layout = QVBoxLayout()
            layout.addWidget(self.content)
            layout.addWidget(self.toggleButton, stretch=0)
            self.toggleButton.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        elif side == Qt.AlignBottom:
            layout = QVBoxLayout()
            layout.addWidget(self.toggleButton, stretch=0)
            layout.addWidget(self.content)
            self.toggleButton.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        elif side == Qt.AlignRight:
            layout = QHBoxLayout()
            layout.addWidget(self.toggleButton, stretch=0)
            layout.addWidget(self.content)
            self.toggleButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        elif side == Qt.AlignLeft:
            layout = QHBoxLayout()
            layout.addWidget(self.content)
            layout.addWidget(self.toggleButton, stretch=0)
            self.toggleButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        else:
            return
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.Update()

    def Toggle(self):
        self._collapsed = not self._collapsed
        self.Update()

    def Update(self):
        self.content.setVisible(not self._collapsed)

        if self.side == Qt.AlignRight:
            if self._collapsed:
                text = self.arrows['left']
            else:
                text = self.arrows['right']
        elif self.side == Qt.AlignLeft:
            if self._collapsed:
                text = self.arrows['right']
            else:
                text = self.arrows['left']
        elif self.side == Qt.AlignTop:
            if self._collapsed:
                text = self.arrows['down']
            else:
                text = self.arrows['up']
        elif self.side == Qt.AlignBottom:
            if self._collapsed:
                text = self.arrows['up']
            else:
                text = self.arrows['down']
        else:
            return

        self.toggleButton.setText(text)
