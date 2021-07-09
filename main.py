from PySide6 import QtWidgets
from UI.MainWindow.MainWindow import *
import os
import sys

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
