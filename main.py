from PySide2 import QtWidgets
from UI.MainWindow.MainWindow import *
import faulthandler
import sys
# import cProfile

#
# sys.stdout = open("outLog.txt", "w")
# sys.stderr = open("errLog.txt", "w")

faulthandler.enable()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # cProfile.run('app.exec_()', filename="dataOut.prof")
    app.exec_()
