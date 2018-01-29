import sys
import os
from factory_test_tool_ui import *
import time
import ConfigParser
from my_widget import *

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
    DUT_NUM = 4
    TEST_FLOW = {}
    DUT_PORTS = []
    DUT_RATES = []
    DUT_START_BTNS = []
    DUT_LOG_BTNS = []
    CHIP_TYPE_NUM = 0
    def __init__(self, params={}, parent=None):
        super(QtGui.QMainWindow, self).__init__(parent=parent)
        self.setupUi(self)  # general by pyqt designer
        self._ui_init()       # add my control and init some ui settings
        self._setup_signal()  # add signal for need
        self._test_init()     # initial the settings for production test
        
    def _ui_init(self):
        for i in xrange(1,self.DUT_NUM+1):
            self.DUT_START_BTNS.append(eval('self.pbStart'+str(i)))
            self.DUT_LOG_BTNS.append(eval('self.pbLog'+str(i)))
            for j in xrange(1,3):
                self.DUT_PORTS.append(eval('self.cbPort'+str(i)+'_'+str(j)))
                self.DUT_RATES.append(eval('self.cbPortRate'+str(i)+'_'+str(j)))
                eval('self.lePortRate'+str(i)+'_'+str(j)).setHidden(True)
        self.CHIP_TYPE_NUM = self.cbChipType.maxCount()
        self.BAUD_NUM = self.cbPortRate1_1.maxCount()
        self.dut_reset('./config/dutConfig')

    def _setup_signal(self):
        p = self.trwTestFlow.children()[0]
        QtCore.QObject.connect(self.trwTestFlow, QtCore.SIGNAL(_fromUtf8("itemChanged(QTreeWidgetItem*,int)")), self.testflow_check)
        QtCore.QObject.connect(self.pbTFSubmit, QtCore.SIGNAL(_fromUtf8("clicked()")), self._testflow_submit)
        QtCore.QObject.connect(self.pbTFReset, QtCore.SIGNAL(_fromUtf8("clicked()")), self.testflow_reset)
        QtCore.QObject.connect(self.pbAllStart, QtCore.SIGNAL(_fromUtf8("clicked()")), self.all_start)
        QtCore.QObject.connect(self.pbCloudSync, QtCore.SIGNAL(_fromUtf8("clicked()")), self.cloud_sync)
        QtCore.QObject.connect(self.pbDutReset, QtCore.SIGNAL(_fromUtf8("clicked()")), self.dut_reset)
        QtCore.QObject.connect(self.pbDutSubmit, QtCore.SIGNAL(_fromUtf8("clicked()")), self._dut_submit)        
        for btn in self.DUT_START_BTNS: btn.clicked.connect(self.single_start)
        for btn in self.DUT_LOG_BTNS: btn.clicked.connect(self.pop_log)
        for cb in self.DUT_PORTS: cb.clicked.connect(self.change_port)
        for cb in self.DUT_RATES: cb.clicked.connect(self.change_baud)
        
        QtCore.QMetaObject.connectSlotsByName(self)
    
    def _test_init(self):
        self._testflow_init()
        self._threshold_init()
        
    def _threshold_init(self):
        import openpyxl
        wb = openpyxl.load_workbook('config/ESP8266_Threshold_20180110_hmj.xlsx')
        sheet = wb.get_sheet_by_name(wb.sheetnames[0])
        
        for i in xrange(1, sheet.max_row+1):
            self.twThreshold.setRowCount(sheet.max_row)
            for j in xrange(1, sheet.max_column+1):
                twi = QtGui.QTableWidgetItem()
                #twi.setFlags(QtCore.)
                if sheet[str(chr(64+j))+str(i)].value != None:
                    twi.setText(str(sheet[str(chr(64+j))+str(i)].value))
                    self.twThreshold.setItem(i-1, j-1, twi)
        
    def _testflow_init(self):
        self.testflow_update('./config/tmp_testFlow')
        try:
            if self.testflow_reset('./config/testFlow') != 0:
                print ('Test Flow file was broken, load with default config')
                self.testflow_reset('./config/tmp_testFlow')
        except:
            print ('Test Flow file was broken, load with default config')
            self.testflow_reset('./config/tmp_testFlow')
        os.remove('./config/tmp_testFlow')
        
    
    def testflow_reset(self, file_path='./config/testFlow'):
        with open(file_path, 'r') as fd:
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
                    for i in xrange(1,len(level_index)):
                        tmp = item.text(0)
                        item = item.child(int(level_index[i]))
                    if editable == '1':
                        item.setText(0, value)
                    if checkable >= 0:
                        item.setCheckState(0, checkable)
                    
                rl = fd.readline()
        return 0
        
    
    def _testflow_submit(self):
        first_flag = True
        while(1):
            tmp_time = time.strftime('%Y-%m-%d-%H',time.localtime(time.time()))
            y,m,d,h = map(lambda x:int(x), tmp_time.split('-'))
            print (tmp_time, (y+(m+d+h))%10000)
            
            if first_flag:
                verify,rst = QtGui.QInputDialog().getText(self, "Verify Box", "Verify:",
                                                          QtGui.QLineEdit().Normal, '')
            else:
                verify,rst = QtGui.QInputDialog().getText(self, "Verify Box", "Verify: (fail, retry!!)",
                                                          QtGui.QLineEdit().Normal, '')
            first_flag = False
            if rst:       
                try:
                    if int(verify) == (y+(m+d+h))%10000:
                        print ('verify pass')
                        self.testflow_update()
                        break
                    else:
                        print ('verify fail')
                except:
                    print ('please input 4 bytes Number')
            else:
                break
    
    def testflow_update(self, file_path='./config/testFlow'):
        with open(file_path, 'w') as fd:
            fd.write("- level-index $$ childCount$$ checkable$$ editable$$ value -\n")
            self._testflow_general(fd, self.trwTestFlow.invisibleRootItem(), '0')
        QtGui.QTreeWidgetItem
        if file_path=='./config/testFlow':
            msg = QtGui.QMessageBox(QtGui.QMessageBox.NoIcon, '!!!','The Test Flow update succ!!    ')
            msg.exec_()
    
    def _testflow_general(self, fd, root, level_index):
        if(root.flags()&QtCore.Qt.ItemIsEditable):            
            self.TEST_FLOW[str(root.parent().text(0))] = str(root.text(0))
        else:
            self.TEST_FLOW[str(root.text(0))] = root.checkState(0)
            
        fd.write("[%-12s%s%2d%s%2d%s%2d%s %s]\n"%(level_index, self._SP_SIGN, int(root.childCount()), self._SP_SIGN, 
                                          int(root.checkState(0) if(root.flags()&QtCore.Qt.ItemIsUserCheckable) else -1), self._SP_SIGN, 
                                          int(1 if(root.flags()&QtCore.Qt.ItemIsEditable) else 0), self._SP_SIGN, str(root.text(0))))
        for i in xrange(root.childCount()):
            self._testflow_general(fd, root.child(i), level_index+'-'+str(i))
    
    def testflow_check(self, item=None, index=None):
        def updateParentItem(item):
            try:
                parent = item.parent()
            except:
                return
            
            checkedCount = 0
            checkableCount = 0
            
            for i in xrange(parent.childCount()):
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
            for i in xrange(item.childCount()):
                if item.child(i).flags() & QtCore.Qt.ItemIsUserCheckable:
                    item.child(i).setCheckState(0,QtCore.Qt.Unchecked)
                    checkalbeChildCount += 1
            if checkalbeChildCount <= 0:
                updateParentItem(item)
                
        elif item.checkState(0) == QtCore.Qt.Checked:
            checkalbeChildCount = 0
            for i in xrange(item.childCount()):
                if item.child(i).flags() & QtCore.Qt.ItemIsUserCheckable:
                    item.child(i).setCheckState(0,QtCore.Qt.Checked)
                    checkalbeChildCount += 1
            if checkalbeChildCount <= 0:
                updateParentItem(item)
                
    
    def all_start(self):
        pass
    
    def single_start(self, btn):
        print btn.objectName()
        pass
    
    def pop_log(self, btn):
        print btn.objectName()
        pass
    
    def change_port(self, cb_port):
        print cb_port.currentIndex()
        cb_port.showPopup()
        
    def change_baud(self, cb_baud):
        print cb_baud.currentIndex()
        cb_baud.showPopup()
        
    def cloud_sync(self):
        pass
    
    def dut_reset(self, file_path='./config/dutConfig'):
        conf = ConfigParser.ConfigParser()
        #try:
        conf.read(file_path)
        index = self.cbChipType.findText(conf.get('common_conf', 'CHIP_TYPE'))
        if index >= 0:
            self.cbChipType.setCurrentIndex(index)  
            self.leChipType.setHidden(True)
        else:
            self.cbChipType.setCurrentIndex(self.CHIP_TYPE_NUM-1)
            self.leChipType.setText(conf.get('common_conf', 'CHIP_TYPE'))
            self.leChipType.setHidden(False)
        self.leFWVer.setText(conf.get('common_conf', 'FW_VER'))
        self.lePoNo.setText(conf.get('common_conf', 'PO_NO'))
        self.leMPNNo.setText(conf.get('common_conf', 'MPN_NO'))
        self.leFacId.setText(conf.get('common_conf', 'FAC_SID'))
        self.leBatchId.setText(conf.get('common_conf', 'BATCH_SID'))
        self.leFacPlan.setText(conf.get('common_conf', 'FAC_PlAN'))
        self.leConfigId.setText(conf.get('common_conf', 'CLOUD_NO'))
        for i in xrange(1, self.DUT_NUM+1):
            for j in xrange(1, 3):
                eval('self.cbPort'+str(i)+'_'+str(j)).setItemText(0, conf.get('DUT'+str(i), 'PORT'+str(j)))
                index = eval('self.cbPortRate'+str(i)+'_'+str(j)).findText(conf.get('DUT'+str(i), 'RATE'+str(j)))
                if index >= 0:
                    eval('self.cbPortRate'+str(i)+'_'+str(j)).setCurrentIndex(index)
                    eval('self.lePortRate'+str(i)+'_'+str(j)).setHidden(True)
                else:
                    eval('self.cbPortRate'+str(i)+'_'+str(j)).setCurrentIndex(self.BAUD_NUM-1)
                    eval('self.lePortRate'+str(i)+'_'+str(j)).setText(conf.get('DUT'+str(i), 'RATE'+str(j)))
                    eval('self.lePortRate'+str(i)+'_'+str(j)).setHidden(False)           
                               
        #except:
            #print ('load to config file fail')
        self.dut_conf = conf
        
    
    def _dut_submit(self):
        first_flag = True
        while(1):
            tmp_time = time.strftime('%Y-%m-%d-%H',time.localtime(time.time()))
            y,m,d,h = map(lambda x:int(x), tmp_time.split('-'))
            print (tmp_time, (y+(m+d+h))%10000)
            
            if first_flag:
                verify,rst = QtGui.QInputDialog().getText(self, "Verify Box", "Verify:",
                                                          QtGui.QLineEdit().Normal, '')
            else:
                verify,rst = QtGui.QInputDialog().getText(self, "Verify Box", "Verify: (fail, retry!!)",
                                                          QtGui.QLineEdit().Normal, '')
            first_flag = False
            if rst:       
                try:
                    if int(verify) == (y+(m+d+h))%10000:
                        print ('verify pass')
                        self.dut_update()
                        break
                    else:
                        print ('verify fail')
                except:
                    print ('please input 4 bytes Number')
            else:
                break
            
    def dut_update(self, file='./config/dutConfig'):
        with open(file, 'w') as fd:
            fd.write('[common_conf]\n')
            if self.cbChipType.currentIndex() < self.CHIP_TYPE_NUM - 1:
                fd.write('CHIP_TYPE = {}\n'.format(self.cbChipType.currentText()))
            else:
                fd.write('CHIP_TYPE = {}\n'.format(self.leChipType.text()))
            fd.write('FW_VER = {}\n'.format(self.leFWVer.text()))
            fd.write('PO_NO = {}\n'.format(self.lePoNo.text()))
            fd.write('MPN_NO = {}\n'.format(self.leMPNNo.text()))
            fd.write('FAC_SID = {}\n'.format(self.leFacId.text()))
            fd.write('BATCH_SID = {}\n'.format(self.leBatchId.text()))
            fd.write('FAC_PlAN = {}\n'.format(self.leFacPlan.text()))
            fd.write('CLOUD_NO = {}\n'.format(self.leConfigId.text()))
            
            for i in xrange(1, self.DUT_NUM+1):
                fd.write('\n[DUT{}]\n'.format(str(i)))
                for j in xrange(1, 3):
                    fd.write('PORT{} = {}\n'.format(str(j), str(eval('self.cbPort'+str(i)+'_'+str(j)).currentText())))
                    if eval('self.cbPort'+str(i)+'_'+str(j)).currentIndex() < self.BAUD_NUM - 1:
                        fd.write('RATE{} = {}\n'.format(str(j), str(eval('self.cbPortRate'+str(i)+'_'+str(j)).currentText())))
                    else:
                        fd.write('RATE{} = {}\n'.format(str(j), str(eval('self.lePortRate'+str(i)+'_'+str(j)).text())))            
                
    
def run():       
    app = QtGui.QApplication(sys.argv)
    ui = FactoryToolUI()
    ui.show()
    sys.exit(app.exec_())        
    pass

if __name__ == "__main__":
    run()