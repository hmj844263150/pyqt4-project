from PyQt4 import QtCore, QtGui

class MyComboBox(QtGui.QComboBox):
    clicked = QtCore.pyqtSignal(QtGui.QComboBox)
    def mousePressEvent(self, event):
        """ QComboBox.mousePressEvent(QMouseEvent) """
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self)

class MyPushButton(QtGui.QPushButton):
    clicked = QtCore.pyqtSignal(QtGui.QPushButton)
    def mousePressEvent(self, event):
        """ QComboBox.mousePressEvent(QMouseEvent) """
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self)
            if event.type() == QtCore.QEvent.MouseButtonPress:
                self.setDown(True)
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                self.setDown(False)        