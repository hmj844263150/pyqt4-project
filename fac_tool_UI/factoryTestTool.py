import sys
import os
from factoryTestToolUI import *
from submitDialogUI import *
import time

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)
    
#class myWidget(QtGui.QWidget)

class WarningBox(QtGui.QDialog):
    def __init__(self,str_title,str_text,input_box_bool,list_bool):#####自己写一个warningbox
        super(WarningBox,self).__init__(parent = None)
        #self.setWindowFlags(QtCore.Qt.Popup)
        
        self.return_value = list_bool
        self.setWindowTitle(_translate("WarningBox", str_title, None))
        self.setMinimumSize(QtCore.QSize(280, 160))
        self.setMaximumSize(QtCore.QSize(280, 160))
        self.resize(280, 160)
        #self.widget = QtGui.QWidget(self)
        #self.widget.setGeometry(QtCore.QRect(0, 0, 281, 161))
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
        
class FactoryToolUI(Ui_MainWindow, QtGui.QMainWindow):
    _SP_SIGN = '$$'
    _VerifyDialog = None
    def __init__(self, params={}, parent=None):
        super(QtGui.QMainWindow, self).__init__(parent=parent)
        self.setupUi(self)
        self.addMyUI()
        self.setupSignal()
        self.testFlowInit()
    
    def addMyUI(self):
        pass
    
    def testFlowInit(self):
        self.updateTestFlow('./config/tmp_testFlow')
        try:
            if self.pbResetTestFlow('./config/testFlow') != 0:
                print ('Test Flow file was broken, load with default config')
                self.pbResetTestFlow('./config/tmp_testFlow')
        except:
            print ('Test Flow file was broken, load with default config')
            self.pbResetTestFlow('./config/tmp_testFlow')
        os.remove('./config/tmp_testFlow')
        
    
    def setupSignal(self):
        p = self.trwTestFlow.children()[0]
        QtCore.QObject.connect(self.trwTestFlow, QtCore.SIGNAL(_fromUtf8("itemChanged(QTreeWidgetItem*,int)")), self.testFlowCheck)
        QtCore.QObject.connect(self.pbSubmit, QtCore.SIGNAL(_fromUtf8("clicked()")), self.pbSubmitFunc)
        QtCore.QObject.connect(self.pbReset, QtCore.SIGNAL(_fromUtf8("clicked()")), self.pbResetTestFlow)
        QtCore.QMetaObject.connectSlotsByName(self)
        
    def pbResetTestFlow(self, file='./config/testFlow'):
        with open(file, 'r') as fd:
            rl = fd.readline()
            while rl != '':
                if not rl.startswith('['):
                    rl = fd.readline()
                    continue
                rl = rl.strip().strip('[').strip(']')
                if len(rl.split(self._SP_SIGN)) < 5:
                    print 'config file is broken, please re-generate'
                    return -1
                level_index, childCount, checkable, editable, value = rl.split(self._SP_SIGN)
                checkable = int(checkable.strip())
                editable = editable.strip()
                value = value.strip()
                level_index = level_index.strip().split('-')
                if editable == '1' or checkable >= 0:
                    item = self.trwTestFlow.invisibleRootItem()
                    for i in range(1,len(level_index)):
                        tmp = item.text(0)
                        item = item.child(int(level_index[i]))
                    if editable == '1':
                        item.setText(0, value)
                    if checkable >= 0:
                        item.setCheckState(0, checkable)
                    
                    
                rl = fd.readline()
        return 0
        
    
    def pbSubmitFunc(self):
        vrfBox = QtGui.QMessageBox(QtGui.QMessageBox.NoIcon, "Verify", "Verify Code:")
        vrfBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        vrfBox.setDefaultButton(QtGui.QMessageBox.Cancel)
        
        rst = vrfBox.exec_()
        if rst == QtGui.QMessageBox.Ok:
            print 'OK'
        else:
            print "cancel"
        #if self._VerifyDialog == None:
            #list_run = []
            #self._VerifyDialog = WarningBox('verify', 'Verify Code:', True, list_run)
            #if self._VerifyDialog.exec_():
                #return
            #print list_run
            #self._VerifyDialog = None
        #else:
            #self._VerifyDialog.activateWindow()
    
    def updateTestFlow(self, file='./config/testFlow'):
        with open(file, 'w') as fd:
            fd.write("- level-index $$ childCount$$ checkable$$ editable$$ value -\n")
            self.generateFlow(fd, self.trwTestFlow.invisibleRootItem(), '0')
    
    def generateFlow(self, fd, root, level_index):
        fd.write("[%-12s%s%2d%s%2d%s%2d%s %s]\n"%(level_index, self._SP_SIGN, int(root.childCount()), self._SP_SIGN, 
                                          int(root.checkState(0) if(root.flags()&QtCore.Qt.ItemIsUserCheckable) else -1), self._SP_SIGN, 
                                          int(1 if(root.flags()&QtCore.Qt.ItemIsEditable) else 0), self._SP_SIGN, str(root.text(0))))
        for i in range(root.childCount()):
            self.generateFlow(fd, root.child(i), level_index+'-'+str(i))
    
    def testFlowCheck(self, item=None, index=None):
        def updateParentItem(item):
            try:
                parent = item.parent()
            except:
                return
            
            checkedCount = 0
            checkableCount = 0
            
            for i in range(parent.childCount()):
                childItem = parent.child(i)
                if childItem.flags()&QtCore.Qt.ItemIsUserCheckable:
                    checkableCount += 1
                    if childItem.checkState(0) == 2:
                        checkedCount += 1
            if(checkedCount <= 0):
                if parent.flags() & QtCore.Qt.ItemIsUserCheckable:
                    parent.setCheckState(0, QtCore.Qt.Unchecked)
            elif checkedCount>0 and checkedCount<checkableCount:
                if parent.flags() & QtCore.Qt.ItemIsUserCheckable:
                    parent.setCheckState(0, QtCore.Qt.PartiallyChecked)
            elif checkedCount == checkableCount:
                if parent.flags() & QtCore.Qt.ItemIsUserCheckable:
                    parent.setCheckState(0, QtCore.Qt.Checked)        
        
        if item.checkState(0) == QtCore.Qt.Unchecked:
            checkalbeChildCount = 0
            for i in range(item.childCount()):
                if item.child(i).flags() & QtCore.Qt.ItemIsUserCheckable:
                    item.child(i).setCheckState(0,QtCore.Qt.Unchecked)
                    checkalbeChildCount += 1
            if checkalbeChildCount <= 0:
                updateParentItem(item)
                
        elif item.checkState(0) == QtCore.Qt.Checked:
            checkalbeChildCount = 0
            for i in range(item.childCount()):
                if item.child(i).flags() & QtCore.Qt.ItemIsUserCheckable:
                    item.child(i).setCheckState(0,QtCore.Qt.Checked)
                    checkalbeChildCount += 1
            if checkalbeChildCount <= 0:
                updateParentItem(item)
                
            
def run():       
    app = QtGui.QApplication(sys.argv)
    ui = FactoryToolUI()
    ui.show()
    sys.exit(app.exec_())        
    pass

if __name__ == "__main__":
    run()