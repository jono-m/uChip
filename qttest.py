import sys
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from Util import *
import faulthandler

faulthandler.enable()


class Data:
    def __init__(self):
        self.OnRemove = Event()

    def Remove(self):
        self.OnRemove.Invoke()


class TestLabel(QLabel):
    def __init__(self, data: Data):
        super().__init__()
        self.setText("Hello!")

        self.data = data
        self.data.OnRemove.Register(self.DoDestroy, True)

        self.destroyed.connect(self.OnDestroyed, type=Qt.DirectConnection)

    def closeEvent(self, event: QCloseEvent):
        print("Label Closed")
        super().closeEvent(event)

    def DoDestroy(self):
        self.deleteLater()

    def OnDestroyed(self):
        self.data.OnRemove.Unregister(self.DoDestroy, True)


class TestButton(QPushButton):
    def __init__(self, text, data: Data):
        super().__init__()
        self.setText(text)

        self.clicked.connect(data.Remove)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        container = QFrame()
        self.setCentralWidget(container)

        layout = QVBoxLayout()
        container.setLayout(layout)

        d = Data()
        self.testLabel = TestLabel(d)

        self.testButton = TestButton("Delete", d)

        layout.addWidget(self.testLabel)
        layout.addWidget(self.testButton)

        self.testButton.clicked.connect(self.DoThing)

    def DoThing(self):
        self.testLabel.deleteLater()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec_()
