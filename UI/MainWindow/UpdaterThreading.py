from PySide2.QtCore import *
from UI.MainWindow.TabArea import *


class Updater:
    def __init__(self, tabArea: TabArea):
        self.tabArea = tabArea

        self.worker = Worker(tabArea)
        self.thread = QThreadPool()
        self.thread.start(self.worker)

    def Stop(self):
        self.worker.shouldStop = True


class Worker(QRunnable):
    def __init__(self, tabArea: TabArea):
        super().__init__()
        self.shouldStop = False
        self.tabArea = tabArea

    def run(self):
        while not self.shouldStop:
            if self.tabArea.chipTab.chipController is not None:
                self.tabArea.chipTab.chipController.SendToRig(self.tabArea.chipTab.rig)
        print("Done!")
