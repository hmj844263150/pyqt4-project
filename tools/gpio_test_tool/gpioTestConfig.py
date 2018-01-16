import sys
from gpioTestConfigUI import *

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
    
    
class GpioToolUI(Ui_gpioConfigTool, QtGui.QMainWindow):
    _choose_state = 0
    io_pairs = []
    pair_num = 0
    tmp = None
    def __init__(self, params={}, parent=None):
        super(QtGui.QMainWindow, self).__init__(parent=parent)
        self.setupUi(self)
        self.addMyUI()
        self.setupSignal()
    
    def addMyUI(self):
        self.rbHigh.setChecked(True)
        pass
    
    def setupSignal(self):
        QtCore.QObject.connect(self.pbChoose, QtCore.SIGNAL(_fromUtf8("clicked()")), self.btnEventChoose)
        QtCore.QObject.connect(self.pbDelete, QtCore.SIGNAL(_fromUtf8("clicked()")), self.btnEventDelete)
        QtCore.QObject.connect(self.pbGenerate, QtCore.SIGNAL(_fromUtf8("clicked()")), self.btnEventGenerate)
        for btn in self.buttonGroup.buttons():
            btn.myClicked.connect(self.btnChoose)
            
        self.pbV33.myClicked.connect(self.btnV33GND)
        self.pbGND.myClicked.connect(self.btnV33GND)
            
        QtCore.QMetaObject.connectSlotsByName(self)
    
    def btnEventChoose(self):
        self._choose_state = 1
        self.tbLog.append('choose out io')
        if self.tmp != None:
            self.tmp.setEnabled(True)
            self.tmp.setDown(False)
    
    def btnEventDelete(self):
        if self.pair_num < 1:
            self.tbLog.append('empty now what yuo want')
            return
        pair = self.io_pairs.pop(self.pair_num-1)
        self.tbLog.append('delete %s -> %s'%(pair[0].text(), pair[1].text()))
        self.pair_num -= 1
        pair[0].setEnabled(True)
        pair[0].setDown(False)
        pair[1].setEnabled(True)
        pair[1].setDown(False)
        self.tbResult.clear()
        for pair in self.io_pairs:
            if len(pair) == 3:
                self.tbResult.append('%s -> %s (%s)'%(pair[0].text(), pair[1].text(), pair[2]))
    
    def btnEventGenerate(self):
        GPIO_32_TEST_VAL = [0x00000000,0x00000000,0x00000000]        
        GPIO_32_TEST_TARGET = [0x00000000,0x00000000,0x00000000]
        with open('GPIO_config.txt', 'w') as fd:
            for pair in self.io_pairs:
                if len(pair) == 3:
                    fd.write('%s -> %s (%s)\n'%(pair[0].text(), pair[1].text(), pair[2]))
                    if str(pair[0].text()) != 'V33' and str(pair[0].text()) != 'GND':
                        io_out = int(str(pair[0].text()[2:]), 10)
                    else:
                        io_out = -1
                    io_in = int(str(pair[1].text()[2:]), 10)
                    if pair[2] == 'High':
                        io_hl = 0x03
                    else:
                        io_hl = 0x02
                    if io_out != -1:
                        GPIO_32_TEST_VAL[io_out/16] |= (io_hl << (io_out%16)*2)
                    GPIO_32_TEST_VAL[io_in/16] |= (0x01 << (io_in%16)*2)
                    GPIO_32_TEST_TARGET[io_in/16] |= (io_hl << (io_in%16)*2)
                    
            fd.write("\nGPIO_32_TEST_VAL_0 = 0x%08x\n"%(GPIO_32_TEST_VAL[0]))
            fd.write("GPIO_32_TEST_VAL_1 = 0x%08x\n"%(GPIO_32_TEST_VAL[1]))
            fd.write("GPIO_32_TEST_VAL_2 = 0x%08x\n\n"%(GPIO_32_TEST_VAL[2]))
            fd.write("GPIO_32_TEST_TARGET_0 = 0x%08x\n"%(GPIO_32_TEST_TARGET[0]))
            fd.write("GPIO_32_TEST_TARGET_1 = 0x%08x\n"%(GPIO_32_TEST_TARGET[1]))
            fd.write("GPIO_32_TEST_TARGET_2 = 0x%08x\n"%(GPIO_32_TEST_TARGET[2]))
                    
        
    def btnV33GND(self, btn):
        if self._choose_state == 0:
            self.tbLog.append('please click choose btn first')
        elif self._choose_state == 1:
            self.io_pairs.append([btn])
            self.tbLog.append('%s -> '%(str(btn.text())))
            self._choose_state = 2
        elif self._choose_state == 2:
            self.tbLog.append('v33 and gnd only could be out')
    
    def btnChoose(self, btn):
        print (btn.text())
        if self._choose_state == 0:
            self.tbLog.append('please click choose btn first')
        elif self._choose_state == 1:
            self.tmp = btn
            self.io_pairs.append([btn])
            self.tbLog.append('%s -> '%(str(btn.text())))
            btn.setEnabled(False)
            btn.setDown(True)
            self._choose_state = 2
        elif self._choose_state == 2:
            self.tmp = None
            self.io_pairs[self.pair_num].append(btn)
            if (self.rbHigh.isChecked() == True and self.io_pairs[self.pair_num][0].text()!='GND') or self.io_pairs[self.pair_num][0].text() == 'V33':
                self.io_pairs[self.pair_num].append('High')
            else:
                self.io_pairs[self.pair_num].append('Low')
            self.tbLog.append('%s -> %s'%(self.io_pairs[self.pair_num][0].text(), self.io_pairs[self.pair_num][1].text()))
            self.tbResult.append('%s -> %s (%s)'%(self.io_pairs[self.pair_num][0].text(), self.io_pairs[self.pair_num][1].text(), self.io_pairs[self.pair_num][2]))
            btn.setEnabled(False)
            btn.setDown(True)
            self.pair_num += 1
            self._choose_state = 0
        
def run():       
    app = QtGui.QApplication(sys.argv)
    ui = GpioToolUI()
    ui.show()
    sys.exit(app.exec_())        
    pass

if __name__ == "__main__":
    run()