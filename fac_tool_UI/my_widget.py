from PyQt4 import QtCore, QtGui

class MyComboBox(QtGui.QComboBox):
    clicked = QtCore.pyqtSignal(QtGui.QComboBox)
    currentIndexChanged = QtCore.pyqtSignal(QtGui.QComboBox, QtCore.QString)
    last_index = 0
    def mousePressEvent(self, event):
        """ QComboBox.mousePressEvent(QMouseEvent) """
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self)
            self.showPopup()
            
            
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
                

# reference for filter
class WarningBox(QtGui.QDialog):
    def __init__(self,str_title,str_text,input_box_bool,list_bool):
        super(WarningBox,self).__init__(parent = None)
        #self.setWindowFlags(QtCore.Qt.Popup)
        
        self.return_value = list_bool
        self.setWindowTitle(_translate("WarningBox", str_title, None))
        self.setMinimumSize(QtCore.QSize(280, 160))
        self.setMaximumSize(QtCore.QSize(280, 160))
        self.resize(280, 160)
        self.buttonSure = QtGui.QPushButton(self)
        self.buttonSure.setGeometry(QtCore.QRect(110, 120, 75, 23))
        self.buttonSure.setText(_translate("WarningBox", "Sure", None))
        self.buttonCancel = QtGui.QPushButton(self)
        self.buttonCancel.setText(_translate("WarningBox", "Cancel", None))
        self.buttonCancel.setGeometry(QtCore.QRect(190, 120, 75, 23))
        self.leVerify = QtGui.QLineEdit(self)
        self.leVerify.setGeometry(QtCore.QRect(50, 60, 181, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.leVerify.setFont(font)
        self.label = QtGui.QLabel(self)
        self.label.setText(_translate("WarningBox", str_text, None))  
        self.label.setGeometry(QtCore.QRect(70, 30, 121, 21))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.buttonSure.clicked.connect(self.sureOpra)
        self.buttonCancel.clicked.connect(self.cancelOpra)
        
        self.filter = Filter()
        self.setFocusPolicy(QtCore.Qt.WheelFocus)
        self.installEventFilter(self.filter)
        self.filter.message.connect(self.activiteEvent)
        self.show()
        
    def activiteEvent(self, value):
        print value
        if value == 3: # activite state change
            self.activateWindow() # active the window
            self.raise_()   # pop dialog            
    
    def sureOpra(self):
        self.close()
        self.return_value.append(1)

    def cancelOpra(self):
        self.close()
        self.return_value.append(0)
        
class Filter(QtCore.QObject):
    message = QtCore.pyqtSignal(int)
    def __init__(self):
        super(Filter, self).__init__()
        self.counter = 0
        
    def eventFilter(self, obj, event):
        #popupVisible = obj != self
        if event.type() == QtCore.QEvent.FocusOut:
            self.message.emit(-1)
        if event.type()==QtCore.QEvent.FocusIn:
            self.counter += 1
            self.message.emit(1)
        if event.type()==QtCore.QEvent.WindowActivate:
            self.message.emit(2)
        if event.type() ==QtCore.QEvent.WindowDeactivate:
            self.message.emit(3)
        if event.type()==QtCore.QEvent.KeyPress:
            print event.key()
            if event.key() == QtCore.Qt.Key_Tab:
                print  QtCore.Qt.AltModifier
        return False 

