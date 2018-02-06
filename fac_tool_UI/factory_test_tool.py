import sys
import os
from factory_test_tool_ui import *
import time
import ConfigParser
import serial
import serial.tools.list_ports 
import threading
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
    #sys.stdout = stdout
    if dut_config['common_conf']['test_from'] == 'FLASH':
        dut_num = dut_config['common_conf']['dut_num']
        baudrate = dut_config['DUT'+dut_num]['rate1']
        port = dut_config['DUT'+dut_num]['port1']
        import random
        i = random.randint(0, 4)
        
        stdout.write('[state]run')
        stdout.write('[mac]18fe34000001')
        stdout.write(port)
        stdout.write(baudrate)
        try:
            ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
            ser.write('esp_set_flash_jump_start 1\r')
            rl = ser.readline()            
        except:
            stdout.write('open serial fail')
            
    elif dut_config['common_conf']['test_from'] == 'RAM':
        pass
    else:
        pass
    
class FactoryToolUI(Ui_MainWindow, QtGui.QMainWindow):
    _SP_SIGN = '$$'
    SIGNAL_PRINT = QtCore.pyqtSignal(QtGui.QTextBrowser, str)
    DUT_NUM = 4
    DUT_PORTS = []
    DUT_RATES = []
    DUT_START_BTNS = []
    DUT_STOP_BTNS = []
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
            self.DUT_STOP_BTNS.append(eval('self.pbStop'+str(i)))
            self.DUT_LOG_BTNS.append(eval('self.maLog'+str(i)))
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
        QtCore.QObject.connect(self.cbTestFrom, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), self.test_from_change)
        QtCore.QObject.connect(self.pbBinPath, QtCore.SIGNAL(_fromUtf8("clicked()")), self.showFileDialog)
        for btn in self.DUT_START_BTNS: btn.clicked.connect(self.single_start)
        for btn in self.DUT_STOP_BTNS: btn.clicked.connect(self.single_stop)
        for cb in self.DUT_PORTS: cb.clicked.connect(self.change_port)
        self.maLog1.triggered.connect(lambda :self.pop_log(1))
        self.maLog2.triggered.connect(lambda :self.pop_log(2))
        self.maLog3.triggered.connect(lambda :self.pop_log(3))
        self.maLog4.triggered.connect(lambda :self.pop_log(4))
        self.cbPortRate1_1.currentIndexChanged.connect(lambda :self.change_baud(self.cbPortRate1_1))
        self.cbPortRate1_2.currentIndexChanged.connect(lambda :self.change_baud(self.cbPortRate1_2))
        self.cbPortRate2_1.currentIndexChanged.connect(lambda :self.change_baud(self.cbPortRate2_1))
        self.cbPortRate2_2.currentIndexChanged.connect(lambda :self.change_baud(self.cbPortRate2_2))
        self.cbPortRate3_1.currentIndexChanged.connect(lambda :self.change_baud(self.cbPortRate3_1))
        self.cbPortRate3_2.currentIndexChanged.connect(lambda :self.change_baud(self.cbPortRate3_2))
        self.cbPortRate4_1.currentIndexChanged.connect(lambda :self.change_baud(self.cbPortRate4_1))
        self.cbPortRate4_2.currentIndexChanged.connect(lambda :self.change_baud(self.cbPortRate4_2))
        
        self.SIGNAL_PRINT.connect(self.print_log)
        self.maCloud.changed.connect(self.change_position)
        
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
            self.dut_config['common_conf']['dut_num'] = str(id)
            t = threading.Thread(target=fac_test, args=[stdout_, self.dut_config, self.test_flow])
            t.start()
        else:
            print('error: get strat btn err')
    
    def single_stop(self, btn):
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
    
    def print_(self, log):
        self.SIGNAL_PRINT.emit(log)
        
    def pop_log(self, index):
        id = index
        print id
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
    
    def change_baud(self, cb):
        if cb.currentText() == 'custom':
            eval('self.lePortRate{}'.format(cb.objectName()[-3:])).setHidden(False)
        else:
            eval('self.lePortRate{}'.format(cb.objectName()[-3:])).setHidden(True)
        
    def cloud_sync(self):
        conf = ConfigParser.ConfigParser()
        conf.read('./config/dutConfig')
        ip = conf.get('common_conf', 'tmp_server_ip')
        port = conf.get('common_conf', 'tmp_server_port')
        url = 'http://{}:{}/hp_register.py?opration=config&user_token={}'.format(ip,port,self.leConfigId.text()) # test_config_002
        import requests
        import json
        def get(url, datas=None):
            response = requests.get(url, params=datas)
            json = response.json()
            return json
        
        rsp = get(url)
        #print rsp
        
        if rsp['production'] == False or rsp['testflow'] == False:
            self.lbSyncState.setText('get cloud config fail')
            return
        self.lbSyncState.setText('get cloud config succ')
        production, testflow = list(rsp['production']), list(rsp['testflow'])
        conf = ConfigParser.ConfigParser()
        try:
            conf.read('./config/dutConfig')
            conf.set('common_conf','position', 'cloud')
            conf.set('common_conf','fw_ver', production[3])
            conf.set('common_conf','po_no', production[4])
            conf.set('common_conf','mpn_no', production[1])
            conf.set('common_conf','fac_sid', production[5])
            conf.set('common_conf','batch_sid', production[6])
            conf.set('common_conf','fac_plan', production[7])
            conf.set('common_conf','cloud_no', production[0])
            conf.set('common_conf','test_from', production[8])
            conf.set('common_conf','auto_start', str(production[11]))
            conf.set('chip_conf','freq', production[9])
            conf.set('chip_conf','efuse_mode', production[10])
            conf.set('chip_conf','chip_type', production[2])
            conf.write(open('./config/dutConfig', 'w'))
        except:
            print 'dut config file error'
        self.dut_reset(file_path='./config/dutConfig')
        item = self.trwTestFlow.invisibleRootItem()
        if testflow[0] == '\x01':
            item.child(0).setCheckState(0, 2)
        else:
            item.child(0).setCheckState(0, 0)
        if testflow[1] == '\x01':
            item.child(1).setCheckState(0, 2)
        else:
            item.child(1).setCheckState(0, 0)
        if testflow[2] == '\x01':
            item.child(2).setCheckState(0, 2)
        else:
            item.child(2).setCheckState(0, 0)
        self.testflow_update()
        
    def dut_reset(self, file_path='./config/dutConfig'):
        conf = ConfigParser.ConfigParser()
        try:
            conf.read(file_path)
            for i in conf.sections():
                self.dut_config[i] = dict(conf.items(i))
                
            index = self.cbChipType.findText(conf.get('chip_conf', 'CHIP_TYPE'))
            if index >= 0:
                self.cbChipType.setCurrentIndex(index)  
                self.leChipType.setHidden(True)
            else:
                self.cbChipType.setCurrentIndex(self.CHIP_TYPE_NUM-1)
                self.leChipType.setText(conf.get('chip_conf', 'CHIP_TYPE'))
                self.leChipType.setHidden(False)
            self.leFWVer.setText(conf.get('common_conf', 'FW_VER'))
            self.lePoNo.setText(conf.get('common_conf', 'PO_NO'))
            self.leMPNNo.setText(conf.get('common_conf', 'MPN_NO'))
            self.leFacId.setText(conf.get('common_conf', 'FAC_SID'))
            self.leBatchId.setText(conf.get('common_conf', 'BATCH_SID'))
            self.leFacPlan.setText(conf.get('common_conf', 'FAC_PlAN'))
            self.leConfigId.setText(conf.get('common_conf', 'CLOUD_NO'))
            self.leBinPath.setText(conf.get('common_conf', 'BIN_PATH'))
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
            
            if conf.get('common_conf', 'position') == 'cloud':
                self.maCloud.setChecked(True)
                self.wgCloudConfig.setEnabled(True)
                self.wgLocalConfig.setEnabled(False)
                self.lbPosition.setText('Cloud')
            else:
                self.maCloud.setChecked(False)
                self.wgCloudConfig.setEnabled(False)
                self.wgLocalConfig.setEnabled(True)
                self.lbPosition.setText('Loacl')                
            
            if conf.get('common_conf', 'test_from') == 'RAM':
                self.cbTestFrom.setCurrentIndex(0)
            else:
                self.cbTestFrom.setCurrentIndex(1)
                
            self.cbFREQ.setCurrentIndex(self.cbFREQ.findText(conf.get('chip_conf', 'freq')))
            self.cbAutoStart.setCurrentIndex(self.cbAutoStart.findText(conf.get('common_conf', 'auto_start')))
            self.cbEfuseMode.setCurrentIndex(self.cbEfuseMode.findText(conf.get('chip_conf', 'efuse_mode')))
                
            self.lbChipType.setText(conf.get('chip_conf', 'chip_type'))
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
        if not conf.has_section('chip_conf'):
            conf.add_section('chip_conf')
            
        conf.set('common_conf', 'POSITION', 'cloud' if self.maCloud.isChecked() else 'local')
        conf.set('common_conf', 'TEST_FROM', self.cbTestFrom.currentText())
        conf.set('chip_conf', 'FREQ', self.cbFREQ.currentText())
        conf.set('chip_conf', 'efuse_mode', self.cbEfuseMode.currentText())
        conf.set('common_conf', 'auto_start', self.cbAutoStart.currentText())
        if self.cbChipType.currentIndex() < self.CHIP_TYPE_NUM - 1:
            conf.set('chip_conf', 'CHIP_TYPE', self.cbChipType.currentText())
        else:
            conf.set('chip_conf', 'CHIP_TYPE', self.leChipType.text())
        conf.set('common_conf', 'FW_VER', self.leFWVer.text())
        conf.set('common_conf', 'PO_NO', self.lePoNo.text())
        conf.set('common_conf', 'MPN_NO', self.leMPNNo.text())
        conf.set('common_conf', 'FAC_SID', self.leFacId.text())
        conf.set('common_conf', 'BATCH_SID', self.leBatchId.text())
        conf.set('common_conf', 'FAC_PlAN', self.leFacPlan.text())
        conf.set('common_conf', 'CLOUD_NO', self.leConfigId.text())
        conf.set('common_conf', 'BIN_PATH', self.leBinPath.text())
        
        for i in xrange(1, self.DUT_NUM+1):
            if not conf.has_section('DUT'+str(i)):
                conf.add_section('DUT'+str(i))
            for j in xrange(1, 3):
                conf.set('DUT'+str(i), 'PORT'+str(j), str(eval('self.cbPort'+str(i)+'_'+str(j)).currentText()))
                if eval('self.cbPortRate'+str(i)+'_'+str(j)).currentIndex() < self.BAUD_NUM-1:
                    conf.set('DUT'+str(i), 'RATE'+str(j), str(eval('self.cbPortRate'+str(i)+'_'+str(j)).currentText()))
                else:
                    conf.set('DUT'+str(i), 'RATE'+str(j), str(eval('self.lePortRate'+str(i)+'_'+str(j)).text()))
        conf.write(open(file_path, 'w'))
        
        self.dut_reset(file_path)
            
        if file_path=='./config/dutConfig':
            msg = QtGui.QMessageBox(QtGui.QMessageBox.NoIcon, '!!!','The DUT config update succ!!    ')
            msg.exec_()    
    
    def state_change(self, dut_num, state, style):
        leState = eval("self.leStatus{}".format(dut_num))
        leState.setText(state)
        leState.setStyleSheet(_fromUtf8(style+"color: rgb(255, 255, 255);"))
        
    def print_log(self, tb, log):
        log=str(log)
        if log.startswith('[state]'):
            if log.lower().find('idle') >= 0:
                state = 'IDLE'
                style = "background-color: rgb(0, 170, 255);\n"
            elif log.lower().find('run') >= 0:
                state = 'RUN'
                style = "background-color: rgb(255, 255, 0);\n"
            elif log.lower().find('pass') >= 0:
                state = 'PASS'
                style = "background-color: rgb(0, 170, 0);\n"
            else:
                state = 'FAIL'
                style = "background-color: rgb(255, 0, 0);\n"
            
            self.state_change(tb.objectName()[-1], state, style)
        elif log.startswith('[mac]'):
            eval("self.lbMAC{}".format(tb.objectName()[-1])).setText(log[5:17])
            
        tb.append(log)
    
    def chip_type_change(self, index):
        if index == self.CHIP_TYPE_NUM - 1:
            self.leChipType.setHidden(False)
        else:
            self.leChipType.setHidden(True)
    
    def test_from_change(self, index):
        self.dut_config['common_conf']['test_from'] = self.cbTestFrom.currentText()
        if self.cbTestFrom.currentText() == 'RAM':
            self.pbBinPath.setEnabled(True)
            self.leBinPath.setEnabled(True)
        else:
            self.pbBinPath.setEnabled(False)
            self.leBinPath.setEnabled(False)            
    
    def change_position(self):
        if self.maCloud.isChecked():
            self.wgLocalConfig.setEnabled(False)
            self.wgCloudConfig.setEnabled(True)
            self.twTestArea.widget(2).setEnabled(False)
            self.lbPosition.setText('Cloud')
            self.tePosition.setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);\n"
                                                    "border-color: rgb(0, 255, 255);"))
        else:
            self.wgLocalConfig.setEnabled(True)
            self.wgCloudConfig.setEnabled(False)
            self.twTestArea.widget(2).setEnabled(True)
            self.lbPosition.setText('Loacl')
            self.tePosition.setStyleSheet(_fromUtf8("background-color: rgb(255, 170, 127);\n"
                                                    "border-color: rgb(0, 255, 255);"))            
    
    def showFileDialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(None, 'Open file', './bin/', filter='firmware(*.bin);;all(*.*)', selectedFilter='firmware(*.bin)')
        self.leBinPath.setText(filename)
        self.dut_config['common_conf']['bin_path'] = filename

def run():
    app = QtGui.QApplication(sys.argv)
    ui = FactoryToolUI()
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()