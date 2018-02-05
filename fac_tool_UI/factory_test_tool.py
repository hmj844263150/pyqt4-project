import sys
import os
from factory_test_tool_ui import *
import time
import ConfigParser
import serial
import serial.tools.list_ports 
from my_widget import *
from io import StringIO

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

def fac_test(stdout, dut_config, test_flow):
    sys.stdout = stdout
    print (test_flow['USER_FW_VER_BAUD'])

class WarningBox(QtGui.QDialog):
    def __init__(self,str_title,str_text,input_box_bool,list_bool):##�Լ�дһ��warningbox
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
    SIGNAL_PRINT = QtCore.pyqtSignal(QtGui.QTextBrowser, str)
    DUT_NUM = 4
    DUT_PORTS = []
    DUT_RATES = []
    DUT_START_BTNS = []
    DUT_LOG_BTNS = []
    CHIP_TYPE_NUM = 0
    
    class _Print(StringIO):
        def __init__(self, factory_tool, obj):
            """ x.__init__(...) initializes x; see help(type(x)) for signature """
            self.factory_tool = factory_tool
            self.obj = obj
        
        def write(self, log):
            self.factory_tool.SIGNAL_PRINT.emit(self.obj, log)    
    
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
       
    def _setup_signal(self):
        p = self.trwTestFlow.children()[0]
        QtCore.QObject.connect(self.trwTestFlow, QtCore.SIGNAL(_fromUtf8("itemChanged(QTreeWidgetItem*,int)")), self.testflow_check)
        QtCore.QObject.connect(self.pbTFSubmit, QtCore.SIGNAL(_fromUtf8("clicked()")), self._testflow_submit)
        QtCore.QObject.connect(self.pbTFReset, QtCore.SIGNAL(_fromUtf8("clicked()")), self.testflow_reset)
        QtCore.QObject.connect(self.pbAllStart, QtCore.SIGNAL(_fromUtf8("clicked()")), self.all_start)
        QtCore.QObject.connect(self.pbCloudSync, QtCore.SIGNAL(_fromUtf8("clicked()")), self.cloud_sync)
        QtCore.QObject.connect(self.pbDutReset, QtCore.SIGNAL(_fromUtf8("clicked()")), self.dut_reset)
        QtCore.QObject.connect(self.pbDutSubmit, QtCore.SIGNAL(_fromUtf8("clicked()")), self._dut_submit)
        QtCore.QObject.connect(self.cbChipType, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), self.chip_type_change)
        for btn in self.DUT_START_BTNS: btn.clicked.connect(self.single_start)
        for btn in self.DUT_LOG_BTNS: btn.clicked.connect(self.pop_log)
        for cb in self.DUT_PORTS: cb.clicked.connect(self.change_port)
        #for cb in self.DUT_RATES: QtCore.QObject.connect(cb, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(QComboBox,QString)")), self.change_baud)
        self.SIGNAL_PRINT.connect(self.print_log)
        self.actionCloud.changed.connect(self.change_position)
        
        QtCore.QMetaObject.connectSlotsByName(self)
    
    def _test_init(self):
        self.dut_config = {}
        self.CHIP_TYPE_NUM = self.cbChipType.count()
        self.BAUD_NUM = self.cbPortRate1_1.count()
        self.dut_reset('./config/dutConfig') 
        
        self.test_flow = {}
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
                        self.testflow_update()
                        print ('verify pass')
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
            self.test_flow[str(root.parent().text(0))] = str(root.text(0))
        else:
            self.test_flow[str(root.text(0))] = root.checkState(0)
            
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
        id = int(btn.objectName()[len(btn.objectName())-1])
        if id in (1,2,3,4):
            stdout_ = self._Print(self, eval("self.tbLog"+str(id)))
            fac_test(stdout_, self.dut_config, self.test_flow)
            
        else:
            print('error: get strat btn err')
       
    def print_(self, log):
        self.SIGNAL_PRINT.emit(log)
        
    def pop_log(self, btn):
        id = int(btn.objectName()[len(btn.objectName())-1])
        if id == 1:
            pass
        elif id == 2:
            pass
        elif id == 3:
            pass
        elif id == 4:
            pass
        else:
            print('error: get log btn err')
    
    def change_port(self, cb_port):
        port_list = list(serial.tools.list_ports.comports())
        cb_port.clear()
        for port in port_list:
            print port[0]
            cb_port.addItem(_fromUtf8(port[0]))
        cb_port.showPopup()
    
    # TODO.
    def change_baud(self, cb_baud): 
        pass
        
    def cloud_sync(self):
        pass
    
    def dut_reset(self, file_path='./config/dutConfig'):
        conf = ConfigParser.ConfigParser()
              
        try:
            conf.read(file_path)
            for i in conf.sections():
                self.dut_config[i] = dict(conf.items(i))
                
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
                    eval('self.cbPort'+str(i)+'_'+str(j)).setCurrentIndex(0)
                    index = eval('self.cbPortRate'+str(i)+'_'+str(j)).findText(conf.get('DUT'+str(i), 'RATE'+str(j)))
                    if index >= 0:
                        eval('self.cbPortRate'+str(i)+'_'+str(j)).setCurrentIndex(index)
                        eval('self.lePortRate'+str(i)+'_'+str(j)).setHidden(True)
                    else:
                        eval('self.cbPortRate'+str(i)+'_'+str(j)).setCurrentIndex(self.BAUD_NUM-1)
                        eval('self.lePortRate'+str(i)+'_'+str(j)).setText(conf.get('DUT'+str(i), 'RATE'+str(j)))
                        eval('self.lePortRate'+str(i)+'_'+str(j)).setHidden(False)
            
            if conf.get('common_conf', 'position') == 'local':
                self.actionCloud.setChecked(False)
                self.wgCloudConfig.setEnabled(False)
                self.wgLocalConfig.setEnabled(True)
                self.lbPosition.setText('Loacl')
            else:
                self.actionCloud.setChecked(True)
                self.wgCloudConfig.setEnabled(True)
                self.wgLocalConfig.setEnabled(False)
                self.lbPosition.setText('Cloud')
                
            self.lbChipType.setText(conf.get('common_conf', 'chip_type'))
            self.lbFWVer.setText(self.leFWVer.text())
            self.lbPoNo.setText(self.lePoNo.text())
            self.lbMPNNo.setText(self.leMPNNo.text())
            self.lbFacId.setText(self.leFacId.text())
            self.lbBatchId.setText(self.leBatchId.text())
            self.lbFacPlan.setText(self.leFacPlan.text())
        except:
            print ('load to config file fail')
    
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
    
    def dut_update(self, file_path='./config/dutConfig'):
        conf = ConfigParser.ConfigParser()
        conf.read(file_path)
        if not conf.has_section('common_conf'):
            conf.add_section('common_conf')
            
        conf.set('common_conf', 'POSITION', 'cloud' if self.actionCloud.isChecked() else 'local')
        if self.cbChipType.currentIndex() < self.CHIP_TYPE_NUM - 1:
            conf.set('common_conf', 'CHIP_TYPE', self.cbChipType.currentText())
        else:
            conf.set('common_conf', 'CHIP_TYPE', self.leChipType.text())
        conf.set('common_conf', 'FW_VER', self.leFWVer.text())
        conf.set('common_conf', 'PO_NO', self.lePoNo.text())
        conf.set('common_conf', 'MPN_NO', self.leMPNNo.text())
        conf.set('common_conf', 'FAC_SID', self.leFacId.text())
        conf.set('common_conf', 'BATCH_SID', self.leBatchId.text())
        conf.set('common_conf', 'FAC_PlAN', self.leFacPlan.text())
        conf.set('common_conf', 'CLOUD_NO', self.leConfigId.text())
        
        for i in xrange(1, self.DUT_NUM+1):
            if not conf.has_section('DUT'+str(i)):
                conf.add_section('DUT'+str(i))
            for j in xrange(1, 3):
                conf.set('DUT'+str(i), 'PORT'+str(j), str(eval('self.cbPort'+str(i)+'_'+str(j)).currentText()))
                if eval('self.cbPort'+str(i)+'_'+str(j)).currentIndex() < self.BAUD_NUM:
                    conf.set('DUT'+str(i), 'RATE'+str(j), str(eval('self.cbPortRate'+str(i)+'_'+str(j)).currentText()))
                else:
                    conf.set('DUT'+str(i), 'RATE'+str(j), str(eval('self.lePortRate'+str(i)+'_'+str(j)).text()))
        conf.write(open(file_path, 'w'))
        
        self.dut_reset(file_path)
            
        if file_path=='./config/dutConfig':
            msg = QtGui.QMessageBox(QtGui.QMessageBox.NoIcon, '!!!','The DUT config update succ!!    ')
            msg.exec_()    
    
    def print_log(self, tb, log):
        log=str(log)
        tb.append(log)
    
    def chip_type_change(self, index):
        if index == self.CHIP_TYPE_NUM - 1:
            self.leChipType.setHidden(False)
        else:
            self.leChipType.setHidden(True)
    
    def change_position(self):
        if self.actionCloud.isChecked():
            self.wgLocalConfig.setEnabled(False)
            self.wgCloudConfig.setEnabled(True)
            self.lbPosition.setText('Cloud')
            self.tePosition.setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);\n"
                                                    "border-color: rgb(0, 255, 255);"))
        else:
            self.wgLocalConfig.setEnabled(True)
            self.wgCloudConfig.setEnabled(False)
            self.lbPosition.setText('Loacl')
            self.tePosition.setStyleSheet(_fromUtf8("background-color: rgb(255, 170, 127);\n"
                                                    "border-color: rgb(0, 255, 255);"))            
        

def run():
    app = QtGui.QApplication(sys.argv)
    ui = FactoryToolUI()
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()