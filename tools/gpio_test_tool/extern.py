from PyQt4 import QtCore, QtGui

class MyPushButton(QtGui.QPushButton):
    myClicked = QtCore.pyqtSignal(QtGui.QPushButton)
    def mousePressEvent(self, event):
        """ QComboBox.mousePressEvent(QMouseEvent) """
        if event.button() == QtCore.Qt.LeftButton:
            self.setDown(True)
            self.myClicked.emit(self)