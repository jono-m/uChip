import sys
from PySide6.QtWidgets import QMainWindow, QApplication
from UI.CustomGraphicsView import CustomGraphicsView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.view = CustomGraphicsView()
        self.setCentralWidget(self.view)

        self.resize(1600, 900)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
