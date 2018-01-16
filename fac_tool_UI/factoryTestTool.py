import sys
from factoryTestToolUI import *

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
    
class FactoryToolUI(Ui_MainWindow, QtGui.QMainWindow):
    def __init__(self, params={}, parent=None):
        super(QtGui.QMainWindow, self).__init__(parent=parent)
        self.setupUi(self)
        self.addMyUI()
        self.setupSignal()
    
    def addMyUI(self):
        pass
    
    def setupSignal(self):
        p = self.trwTestFlow.children()[0]
        QtCore.QObject.connect(self.trwTestFlow, QtCore.SIGNAL(_fromUtf8("itemChanged(QTreeWidgetItem*,int)")), self.testFlowCheck)
        QtCore.QMetaObject.connectSlotsByName(self)
    
    def testFlowCheck(self, item=None, index=None):
        print (item.checkState(index))
        print (item.childCount())
        

def run():       
    app = QtGui.QApplication(sys.argv)
    ui = FactoryToolUI()
    ui.show()
    sys.exit(app.exec_())        
    pass

if __name__ == "__main__":
    run()