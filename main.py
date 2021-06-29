from PySide6 import QtWidgets
from UI.MainWindow.MainWindow import *
import sys
import faulthandler

faulthandler.enable()
faulthandler.dump_traceback_later(5*60, True)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
