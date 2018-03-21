from PyQt4 import QtGui,QtCore
import os
import sys
import time
import serial
import esptool
import espefuse
import binascii
import subprocess
import read_xls_to_h
import serial_print_uart_download as spud
import threading
import timer
import read_log_to_csv_noprint as rl
import sqlite3
import serial
import get_phy_init
import serialCmd
import upload_server
import datetime
import visa
import esp_rpt
import espDownloader
import fwcheck_ramdownload
#from param_save_load import *

DEBUG = 0

sys.path.append('../')
import upload_to_server.upload_to_server as upload_to_server


class TestError(RuntimeError):
    """
    Wrapper class for runtime errors that caused any error in test
    """
    def __init__(self, message):
        RuntimeError.__init__(self, message)

    @staticmethod
    def WithResult(message, result):
        """
        Return a fatal error object that appends the hex values of
        'result' as a string formatted argument.
        """
        message += " (result was %s)" % hexify(result)
        return TestError(message)

class esp_testThread(QtCore.QThread):
    SIGNAL_STOP = QtCore.pyqtSignal()
    def serial_operation(func):
        def wrapper(*args, **kwargs):
            try:
                ser = args[0].ser
            except:
                pass
            rst = func(*args, **kwargs)
            try:
                ser.close()
            except:
                pass
            return rst
        return wrapper    
    
    def __init__(self,_stdout,dutconfig,testflow, rfmutex):
        super(esp_testThread,self).__init__(parent=None)
        self.rfmutex = rfmutex
        self.stop_flag = 0
        self.SIGNAL_STOP.connect(self.ui_stop)
        self.param_read=1
        self.logpath=''
        self.esp_logstr=''
        self.set_params(_stdout,dutconfig,testflow)
        self.MAC = '000000000000'
        self.set_mac_en=0    
        self.tool_ver='V0.0.1'

        self.rptstr='TESTITEM'+','+'TESTVALUE'+','+'SPEC_L'+','+'SPEC_H'+','+'RESULT'+'\n'
        if self.chip_type.find("ESP32")>=0:
            self.THRESHOLD_DICT=rl.get_threshold_dict('ATE', self.threshold_path+'full_Threshold_32.xlsx')
        elif self.chip_type.find('ESP8266')>=0 or self.chip_type.find('ESP8285')>=0:
            self.THRESHOLD_DICT=rl.get_threshold_dict('ATE', self.threshold_path+'full_Threshold_8266.xlsx')  

        if self.chip_type.find("ESP32")>=0:
            self.memory_download= espDownloader.ESP32FACTORY(frame=self, port=self.COMPORT, baudrate=self.BAUDRATE,
                                                             name=self.user_fw_download_port,chip=self.chip_type,
                                                             sub_chip=self.sub_chip_type)
        elif self.chip_type == 'ESP8285':
            self.memory_download= espDownloader.ESP8285FACTORY(frame=self, port=self.COM_PORT_STR, baudrate=self.BAUDRATE,
                                                               name=self.user_fw_download_port,chip=self.chip_type)
        elif (self.chip_type == 'ESP8266') or (self.chip_type == 'ESP8089'):
            self.memory_download= espDownloader.ESP8266FACTORY(frame=self, port=self.COMPORT, baudrate=self.BAUDRATE,
                                                               name=self.user_fw_download_port,chip=self.chip_type)        


    def run(self):
        while not self.stop_flag:
            self.ui_print("[state]idle clear")
            try:
                self.main_test()
            except:
                pass
            #if self.autostartEn:
                #self.msleep(10000)
            if self.autostartEn:
                pass
            else:
                break
            
        try:
            self.ser.close()
        except:
            pass
            self.l_print(0,'quit test')
        self.ui_print('USER QUIT TEST')
        self.ui_print('[state]finish btn up')

    def main_test(self):
        self.stop_flag = 0
        self.resflag = 0
        self.tester_con_flg=1
        self.memory_download.stopFlg=0
        self.tx_test_res=0
        self.rx_test_res=0

        self.logpath=''
        self.esp_logstr=''
        err = 0
        def CHECK(err, err_msg, err_code=0x0, fatal_stop=0):
            if err == 0:
                return
            self.resflag = err
            self.stop_flag = fatal_stop
            self.ui_print(err_msg)
            self.STOPTEST(err_code)
            raise TestError(err_msg)

        CHECK(self.check_param(), 'PARAMS READ ERROR', fatal_stop=1)
        err = self.try_sync()
        if err == -1:
            CHECK(err, 'SYNC FAIL', err_code=1, fatal_stop=1)
        else:
            CHECK(err, 'SYNC FAIL', err_code=1, fatal_stop=0)
        self.ui_print('CHIP SYCN OK')
        self.l_print(0,str(self.THRESHOLD_DICT))   
        CHECK(self.check_chip(), 'CHIP CHECK FAIL', fatal_stop=1)

        if self.loadmode == 1:  # need load bin on ram mode 
            CHECK(self.load_to_ram(self.IMGPATH), 'LOAD RAM FAIL')

        self.ui_print('[state]RUN')
        
        err, log=self.rf_test_catch_log()
        CHECK(err, 'GET TEST LOG FAIL')
        if(self.en_analog_test):
            CHECK(self.rf_test_analogtest(log),' ANALOG TEST FAIL\nEND TEST SEQUENCE', err_code=2)
        if(self.en_tx_test):
            CHECK(self.rf_test_txtest(log), 'TX TEST FAIL\nEND TEST SEQUENCE', err_code=2)
        if(self.en_rx_test):
            CHECK(self.rf_test_rxtest(log), 'RX TEST FAIL\nEND TEST SEQUENCE', err_code=2)

        CHECK(self.general_test_gpio(), 'GPIO TEST FAIL\nEND TEST SEQUENCE', err_code=2)        

        if(self.loadmode==2):
            CHECK(self.esp_write_flash(), 'WRITE PASS INFO FAIL\nEND TEST SEQUENCE')
            CHECK(self.reboot(), 'REBOOT FAIL\nEND TEST SEQUENCE')
            self.l_print(0,'read pass flag ok')
            self.ui_print('REBOOT OK')        

        if self.en_user_fw_check:
            CHECK(self.general_test_fwcheck(), 'FIRMWARE CHECK FAIL\nEND TEST SEQUENCE', err_code=3, fatal_stop=1)

        self.ui_print('ALL ITEM PASSED')
        self.STOPTEST()

    ### RF TEST -------------------------------- ###
    def rf_test_txtest(self, lg):
        """
        Run tx packet test
        Returns: err
            0: success
            1: fail
        """
        self.l_print(0,'start tx test')
        self.l_print(0,'"TEST ITEM:')

        if self.tx_test_res == 0:
            self.tx_test_res = 1
            print(0,self.THRESHOLD_DICT.keys())
            if 'fb_rx_num' in self.THRESHOLD_DICT.keys() and self.en_tx_test:
                self.l_print(0,'TX TEST BEGIN')
                tx_log=''
                log_tx_rx = lg[0].split('\n')
                thres_tmp = self.THRESHOLD_DICT['fb_rx_num']
                self.l_print(3,("fb_rx_num \t%r\n" %(thres_tmp)))

                for log_tmp in log_tx_rx[-20:]:
                    if "tx packet test" in log_tmp:
                        self.tx_test_res = 1
                        break

                #self.tx_test_res=0
                tx_data=[]
                for log_tmp in log_tx_rx[-20:]:
                    if 'FREQ_OFFSET' in log_tmp:
                        freq_data = log_tmp.split(',')[1:-1]
                        freq_data = [int(x) for x in freq_data]
                        thres_freq = self.THRESHOLD_DICT['FREQ_OFFSET']

                        if tx_data[0]>4:
                        #if True: #debug
                            for idx in range(len(freq_data)):
                                self.rpt_append('FREQ_OFFSET', freq_data[idx],thres_freq[0][idx],thres_freq[1][idx])
                                self.l_print(3,'FREQ_OFFSET \t%d~%d\n' %(thres_freq[0][idx], thres_freq[1][idx]))
                                if int(freq_data[idx])<thres_freq[0][idx] or int(freq_data[idx])>thres_freq[1][idx]:
                                    self.tx_test_res=0
                                    self.l_print(3,"Part failure in FREQ_OFFSET : #%d ,%d !< %d !< %d \n\r"%(idx,thres_freq[0][idx],int(freq_data[idx]),thres_freq[1][idx]))
                                    #print "freq test failed "
                                    #tx_log+="Part failure in FREQ_OFFSET : #%d ,%d !< %d !< %d \n\r"%(idx,thres_freq[0][idx],int(freq_data[idx]),thres_freq[1][idx])
                                    self.fail_list.append("freq_test")
                            #self.append_err_log(tx_log)
                            #self.print_dbg( tx_log)
                            #tx_log = ''
                        else:
                            self.rpt_append('FREQ_OFFSET','UaS-NA',thres_freq[0][0],thres_freq[1][0])
                            self.tx_test_res=0
                            self.l_print(3,'unavailable signal')			    
                            tx_log = ''

                    elif 'txp_result' in log_tmp:
                        dlist = log_tmp.split(':')[1].split(',')[:-1]
                        txp_res = [int(x) for x in dlist]
                        thres_txp_res = self.THRESHOLD_DICT['TXP_RES']
                        idx	= 0		    #idx=0  means  txp_res for tx index
                        val = txp_res[idx]
                        #for idx, val in enumerate(txp_res):
                        self.l_print(3,"TXP_RES \t%d~%d\n" %(thres_txp_res[0][0], thres_txp_res[1][0]))
                        self.rpt_append('TXP_RES_0', val,thres_txp_res[0][0],thres_txp_res[1][0])
                        if val < thres_txp_res[0][idx] or val > thres_txp_res[1][idx]:
                            self.tx_test_res=0
                            self.l_print(3,"Part failure in TXP_RES[tx] : #%d ,%d !< %d !< %d \n\r"%(idx, thres_txp_res[0][idx], val, thres_txp_res[1][idx]))

                            self.fail_list.append("txp_res[tx]")

                        tx_log = ''
                    elif 'fb_rx_num' in log_tmp:
                        dlist = log_tmp.split(':')[1].split(',')[:-1]
                        if len(dlist) > 6:
                            dlist = dlist[2:]
                        tx_data = [ int(x) for x in dlist]
                if(self.tx_test_res==1):
                    self.l_print(0,'TX TEST OK')
                    self.ui_print('TX TEST OK')
                    return 0	      

                elif self.tx_test_res==0:
                    self.l_print(0,'TX TEST FAIL')
                    self.ui_print('TX TEST FAIL')
                    return 1

            else:
                self.ui_print('TX TEST EXCEPTION')
                return 1

    def rf_test_rxtest(self, lg):
        """
        Run RX packets test
        Returns: err
            0: success
            1: fail
        """
        #=============================rx test=============================================
        self.l_print(0,'start rx test')
        if self.rx_test_res == 0:
            self.rx_test_res = 1

            if 'dut_rx_num' in self.THRESHOLD_DICT.keys() and self.en_rx_test:

                self.l_print(0,"RX TEST BEGIN")

                rx_log=''
                rssi_log=''
                log_tx_rx = lg[0].split('\n')
                thres_tmp = self.THRESHOLD_DICT['dut_rx_num']
                #self.append_log("dut_rx_num \t%d~%d\n" %(thres_tmp[0][0], thres_tmp[0][1]))
                self.l_print(3,("dut_rx_num \t%d~%d\n" %(thres_tmp[0][0], thres_tmp[1][0])))
                for log_tmp in log_tx_rx[-20:]:
                    if "tx packet test" in log_tmp:
                        self.rx_test_res = 1
                        break
                #self.rx_test_res=1
                dut_rssi = -1
                fb_rssi = -1

                for log_tmp in log_tx_rx[-20:]:
                    #self.print_dbg(( "log_tmp :",log_tmp))
                    #self.print_dbg("test : in rssi test")

                    if 'fb_rxrssi' in log_tmp:
                        #print "test log tmp:",log_tmp
                        dlist = log_tmp.split(':')[1].split(',')[:-1]
                        #print "&&&&&&&&&&&&&&&&&&&&&&&&&"
                        #print "test dlist:",dlist
                        #self.print_dbg(("test dlist fb rssi : ",dlist))
                        fb_rssi_v = [int(x) for x in dlist]
                        fb_rssi_flg = 0
                        if self.chip_type.find("ESP32")>=0:
                            print "fb_rssi for ESP32"
                            fb_rssi_v = [ max(fb_rssi_v), ]

                        for k in range(len(fb_rssi_v)):
                            self.l_print(0,("fb_rxrssi \t%d~%d\n" %(self.THRESHOLD_DICT['fb_rxrssi'][0][k], self.THRESHOLD_DICT['fb_rxrssi'][1][k])))
                            self.rpt_append('FB_RXRSSI', fb_rssi_v[k],fb_rssi_v[k]<self.THRESHOLD_DICT['fb_rxrssi'][0][k],fb_rssi_v[k]<self.THRESHOLD_DICT['fb_rxrssi'][1][k])
                            if fb_rssi_v[k]>self.THRESHOLD_DICT['fb_rxrssi'][1][k] or fb_rssi_v[k]<self.THRESHOLD_DICT['fb_rxrssi'][0][k] :
                                self.rx_test_res = 0
                                fb_rssi_flg = 1
                                self.l_print(3,"Part failure in FB_RXRSSI[%d] res: %d !< %d !< %d \r\n"%(k,self.THRESHOLD_DICT['fb_rxrssi'][0][k],fb_rssi_v[k],self.THRESHOLD_DICT['fb_rxrssi'][1][k]))

                        if fb_rssi_flg == 1:
                            self.fail_list.append("fb_rxrssi")

                        fb_rssi = int(dlist[0])
                    if 'dut_rxrssi' in log_tmp:
                        dlist = log_tmp.split(':')[1].split(',')[:-1]
                        dut_rssi = int(dlist[0])

                        dut_rssi_v = [int(x) for x in dlist]
                        dut_rssi_flg = 0
                        if self.chip_type.find("ESP32")>=0:
                            if DEBUG: print "dut_rssi for ESP32"
                            dut_rssi_v = [ max(dut_rssi_v), ]

                        for k in range(len(fb_rssi_v)):
                            self.l_print(3,("dut_rxrssi \t%d~%d\n" %(self.THRESHOLD_DICT['dut_rxrssi'][0][k], self.THRESHOLD_DICT['dut_rxrssi'][1][k])))
                            self.rpt_append('DUT_RXRSSI',dut_rssi_v[k],self.THRESHOLD_DICT['dut_rxrssi'][0][k],self.THRESHOLD_DICT['dut_rxrssi'][1][k])
                            if dut_rssi_v[k]>self.THRESHOLD_DICT['dut_rxrssi'][1][k] or dut_rssi_v[k]<self.THRESHOLD_DICT['dut_rxrssi'][0][k] :
                                self.rx_test_res = 0
                                dut_rssi_flg = 1
                                self.l_print(3,"Part failure in DUT_RXRSSI[%d] res: %d !< %d !< %d \r\n"%(k,self.THRESHOLD_DICT['dut_rxrssi'][0][k],dut_rssi_v[k],self.THRESHOLD_DICT['dut_rxrssi'][1][k]))

                        if dut_rssi_flg == 1:
                            self.fail_list.append("dut_rxrssi")

                        self.l_print(3,("rssi_diff \t%d~%d\n" %(self.THRESHOLD_DICT['rssi_diff'][0][0], self.THRESHOLD_DICT['rssi_diff'][1][0])))

                        if (dut_rssi-fb_rssi)>self.THRESHOLD_DICT['rssi_diff'][1][0] or (dut_rssi-fb_rssi)<self.THRESHOLD_DICT['rssi_diff'][0][0] :
                            self.rx_test_res = 0
                            self.l_print(3,"Part failure in RSSI res: FB: %d ; DUT: %d, %d !< %d !< %d \r\n"%(fb_rssi,dut_rssi,self.THRESHOLD_DICT['rssi_diff'][0][0],(dut_rssi-fb_rssi),self.THRESHOLD_DICT['rssi_diff'][1][0]))
                            #self.print_dbg( rssi_log)
                            self.fail_list.append("rssi")

                    if 'txp_result' in log_tmp:
                        dlist = log_tmp.split(':')[1].split(',')[:-1]
                        txp_res = [int(x) for x in dlist]
                        thres_txp_res = self.THRESHOLD_DICT['TXP_RES']

                        idx = 1    #idx=1 means txp_res in rx 
                        val = txp_res[idx]
                        #for idx, val in enumerate(txp_res):
                        self.l_print(3,"TXP_RES_1 \t%d~%d\n" %(thres_txp_res[0][1], thres_txp_res[1][1]))
                        self.rpt_append('TXP_RES_1', val,thres_txp_res[0][0],thres_txp_res[1][0])			
                        if val < thres_txp_res[0][idx] or val > thres_txp_res[1][idx]:
                            self.rx_test_res=0
                            self.l_print(3,"Part failure in TXP_RES[rx] : #%d ,%d !< %d !< %d \n\r"%(idx, thres_txp_res[0][idx], val, thres_txp_res[1][idx]))
                            self.fail_list.append("txp_res[rx]")

                        rx_log = ''

                    if u'dut_rx_num' in log_tmp:
                        dlist = log_tmp.split(':')[1].split(',')[:-1]
                        if len(dlist) > 6:
                            dlist = dlist[2:]
                        rx_data = [ int(x) for x in dlist]

                if(self.rx_test_res):
                    self.l_print(0,'RX TEST OK')
                    self.ui_print('RX TEST OK')
                    return 0
                elif(self.rx_test_res==0):
                    self.l_print(0,'RX TEST NOK')
                    self.l_print('RX TEST NOK')		    
                    return 1

            else:
                self.l_print(3,'RX TEST EXCEPTION')
                self.ui_print('RX TEST EXCEPTION')
                return 1

    def rf_test_analogtest(self,lg):
        if not lg[0]=='':
            self.l_print(0,lg[0])
            self.data_process(0)
            if(self.ana_test_result):
                self.l_print(0,'analog test ok')
                self.ui_print('ANALOG TEST OK')
                return 0
            else:
                self.l_print(0,'analog test nok')
                self.ui_print('ANALOG TEST NOK')
                return 1

    def data_process(self,block_num):
        self.l_print(0,"Data Processing...\n")

        start=time.clock()
        if True:
            if self.chip_type.find("ESP32")>=0:
                print "ESP32:"
                values_dictlist=rl.read_log_data(self.logpath,'ESP32',block_num)
            else:
                values_dictlist=rl.read_log_data(self.logpath,'module2515',block_num)

            print "test len : ",len(values_dictlist)
        else:#debug
            ##debug for print
            print("=============================\r\n\r\n")
            print("this is only for log process debug\r\n")
            print("should never be here in a formal version\r\n")
            print("===============================\r\n\r\n")
        value_tmp = []
        value_tmp.append( values_dictlist[block_num])
        _res=rl.data_process_dictList_2(value_tmp,self.THRESHOLD_DICT,0)

        if 1:
            if 'single_chip passed' in _res[1] or not "Part failure" in _res[1]:
                #  self.print_dbg("single chip passed...")
                self.ana_test_result=1
                self.fail_list=[]
            else:
                self.ana_test_result=False
                self.fail_list=_res[2]
        else:
            self.ana_test_result=_res[0]
            self.fail_list=_res[2]

        self.t_dataprocess=time.clock()-start    

    def rf_test_catch_log(self):
        '''
        get the module self calibration and test result via uart
        Return: err, logs
            0: get log success
            1: get log fail
        '''
        print self.slot_num, "start wait"
        self.rfmutex.acquire()

        start=time.clock()
        self.l_print(0,'record serial print ')

        try:
            retry = False
            if self.chip_type == "ESP8089":
                log=spud.get_serial_line_id(self.ser,'MODULE_TEST START!!!','req_suc',retry = retry,chip_type = self.chip_type,mode=self.loadmode,wd=self) #'user code done')
            elif self.chip_type.find("ESP32")>=0:
                log=spud.get_serial_line_id(self.ser,'MODULE_TEST START!!!','MODULE_TEST EDN!!!',retry = retry,chip_type = self.chip_type,mode=self.loadmode,wd=self) #'user code done')
            else:
                log=spud.get_serial_line_id(self.ser,'MODULE_TEST START!!!','MODULE_TEST END!!!',retry = retry,chip_type = self.chip_type,mode=self.loadmode,wd=self) #'user code done')
            
            print self.slot_num, "finish RF"
            self.rfmutex.release()
        except:
            print self.slot_num, "finish RF"  
            self.rfmutex.release()            
            self.l_print(3,'get log fail')
            return 1, ''
            
        if '' in log:
            self.l_print(3,'seria print is null')
            return 1, log  

        return 0, log

    def load_to_ram(self, image_path="image/init_data.bin"):
        self.l_print(0,'target bin is %s'%image_path)
        self.ui_print('UART DOWNLOADing...')
        self.l_print(3,("Start UartDownload...,%s"%image_path))
        last_time = None
        dr=self.memory_download.memory_download(image_path)
        if dr:
            return 0
        else:
            self.memory_download.stopFlg=1
            self.memory_download.disconnect()
            self.l_print(0,"download disconnect...")
            return 1

    ### GENERAL TEST -------------------------------- ###
    def general_test_gpio(self):
        if(self.chip_type.find('ESP8266') >= 0):
            if self.en_gpio_8266_test:
                return self.general_test_gpio_8266()
        elif(self.chip_type=='ESP32'):
            if self.en_gpio_32_test:
                return self.general_test_gpio_32()
        return 0

    def general_test_gpio_8266(self):
        i=0
        self.gpio_02_test_pin=self.testflow['GPIO_8266_TEST_PIN']
        self.gpio_02_test_value=self.testflow['GPIO_8266_TEST_VAL']
        self.gpio_02_read_en=int(self.testflow['GPIO_8266_TEST_READ_EN'])
        self.gpio_02_target_testvalue=self.testflow['GPIO_8266_TEST_VAL_TARGET']
        self.l_print(0,'start 02 gpio test')
        self.msleep(200)

        serTestRes = self.ser
        if not serTestRes.isOpen():
            serTestRes.open()
        serTestRes.flush()
        self.l_print(2,'gpio test pin is:%s'%self.gpio_02_test_pin)
        self.l_print(2,'gpio test value is:%s'%self.gpio_02_test_value)
        self.l_print(2,'gpio test read en?%d'%self.gpio_02_read_en)
        self.l_print(2,'gpio test target value is:%s'%self.gpio_02_target_testvalue)

        gpio_cmd = "gpio_test %s %s %s\n\r"%(self.gpio_02_test_pin,self.gpio_02_test_value,self.gpio_02_test_value)
        serTestRes.write(gpio_cmd)
        gpio_log = ''
        while True:
            res_line = serTestRes.readline()
            if "PASS" in res_line:
                self.l_print(3,'read res:%s'%res_line)
                self.l_print(3,'GPIO TEST 1 PASS')

                self.gpio_test_res1 = 1
                break;
            elif "FAIL" in res_line:
                self.l_print(3,'read res:%s'%res_line)
                self.l_print(3,'GPIO TEST 1 FAIL')

                self.gpio_test_res = 0
                break;
            else:
                self.l_print(0,'step1,read gpio test return value exception,count is %d'%i)
                self.gpio_test_res=0
                i+=1

        if self.gpio_02_read_en == 1:
            i=0
            serTestRes.flushInput()
            serTestRes.flushOutput()

            serTestRes.write("gpio_read\n\r")
            res_line = serTestRes.readline()
            if "GPIO_READ" in res_line:
                val_rd = int(res_line.strip("\r\n").split(',')[1],16)
                val_tgt = int(self.gpio_02_target_testvalue,16)

                self.l_print(3,("val_rd: {}".format(hex(val_rd))))
                self.l_print(3,("val_tgt: {}".format(hex(val_tgt))))


                if val_rd&val_tgt == val_tgt:
                    self.gpio_test_res2=1
                    self.l_print(3,("{}".format(res_line)))
                    self.l_print(0,'pass')

                else:
                    self.l_print(0,'fail')
                    self.l_print(3,("\r\ngpio_read1 fail:"+res_line+";target:"+self.gpio_02_target_testvalue+"\r\n"))
                    self.gpio_test_res = 0
            else:
                self.l_print(3,'step2,read gpio value exception')
                self.gpio_test_res=0

        gpio_v = int(self.gpio_02_test_value,16)
        gpio_v = hex(0xffff^gpio_v)
        gpio_cmd = "gpio_test %s %s %s\n\r"%(self.gpio_02_test_pin,gpio_v,self.gpio_02_test_value)
        serTestRes.write(gpio_cmd)

        while True:
            res_line = serTestRes.readline()
            if "PASS" in res_line:
                self.l_print(3,("log:%s"%res_line))
                self.l_print(3,'GPIO TEST 2 PASS')
                self.gpio_test_res3 = 1
                break;
            elif "FAIL" in res_line:
                self.l_print(3,(("log:%s"%res_line)))
                self.l_print(3,'GPIO TEST 2 FAIL')
                self.gpio_test_res = 0
                break;
            else:

                self.gpio_test_res=0
                self.l_print(0,'step3,read gpio return str exception,count is %d'%i)
                i+=1

        if self.gpio_02_read_en == 1:

            serTestRes.flushInput()
            serTestRes.flushOutput()
            serTestRes.write("gpio_read\n\r")
            res_line = serTestRes.readline()
            if "GPIO_READ" in res_line:

                val_rd = int(res_line.strip("\r\n").split(',')[1],16)
                val_tgt = int(self.window.gpio_8266_target_val,16)
                self.l_print(3,("val_rd:%x" %hex(val_rd)))
                self.l_print(3,("val_tgt:%x"%hex(val_tgt)))

                if val_rd&val_tgt == 0:
                    self.gpio_test_res4=1
                    self.l_print(3,'step4 pass')

                else:
                    self.l_print(3,'step4 fail')
                    self.l_print(3,("\r\ngpio_read2 fail:"+res_line+";target:"+self.gpio_02_target_testvalue+"\r\n"))
                    self.gpio_test_res = 0
            else:
                self.l_print(3,'step4,read gpio return value exception')
                self.gpio_test_res=0

        #serTestRes.close()
        if(self.gpio_test_res==0):
            self.l_print(3,'gpio test fail,please check step log for err info')
            return 1
        else:
            try:
                if self.gpio_02_read_en:
                    if(self.gpio_test_res1) and (self.gpio_test_res2) and (self.gpio_test_res3) and (self.gpio_test_res4):
                        self.l_print(0,'general_test_gpio_8266 test pass')
                        self.ui_print('GPIO_02 TEST PASS')
                        self.gpio_test_res=1
                else:
                    self.l_print(3,'gpio02 read en=0')
                    if(self.gpio_test_res1) and (self.gpio_test_res3):
                        self.l_print(0,'general_test_gpio_8266 test pass')
                        self.ui_print('GPIO_02 TEST PASS')
                        self.gpio_test_res=1
                return 0
            except:
                self.l_print(3,'gpio test fail,please check the which step err')
                self.gpio_test_res=0
                return 1
            

    def general_test_gpio_32(self):
        self.l_print(0,'start 32 gpio test')
        self.gpio_32_test_val_0=self.testflow['GPIO_32_TEST_VAL_0']
        self.gpio_32_test_val_1=self.testflow['GPIO_32_TEST_VAL_1']
        self.gpio_32_test_val_2=self.testflow['GPIO_32_TEST_VAL_2']
        gpio_cmd = "ESP_TEST_GPIO %s %s %s\r" %(self.gpio_32_test_val_0, self.gpio_32_test_val_1, self.gpio_32_test_val_2)
        self.l_print(2,(("gpio cmd:%s"%gpio_cmd)))

        test_log = self._test_item('GPIO', gpio_cmd)
        if test_log == []:
            self.gpio_test_res = 0
            self.l_print(0,'general_test_gpio_32 test fail,read value is null')
        for i in test_log:
            if "Input result" in i:
                gpio_index = i.find('0x')
                gpio_result= i[gpio_index:].split(',')
                self.l_print(3,("gpio_result is:%s "%gpio_result))

                if (int(gpio_result[0], 16) == int(self.gpio_32_test_target_0, 16)
                    and int(gpio_result[1], 16) == int(self.gpio_32_test_target_1, 16)
                    and int(gpio_result[2], 16) == int(self.gpio_32_test_target_2, 16)):
                    self.l_print(3,'general_test_gpio_32 test ok')
                    self.gpio_test_res=1
                    self.ui_print('GPIO_32 TEST OK')
                    break
                else:
                    self.l_print(3,'the return value is not equal the target value')
                    self.gpio_test_res=0
                    break
            else:
                self.l_print('line have no keyword  for general_test_gpio_32 test')
                self.gpio_test_res=0

        if(self.gpio_test_res==0):
            self.l_print(3,'general_test_gpio_32 test nok')
            self.ui_print('GPIO_32 TEST NOK')
            return 1

        return 0	    

    def _test_item(self, test_name, test_cmd, break_str = None, timeout = None):
        """
        Common method of sending a serial command and get response
        """
        i=0
        self.send_count=1
        #send command  more times when test adc 
        self.l_print(3,'test item is %s'%test_name)

        self.msleep(50)
        timeout_ori = self.ser.timeout
        if timeout == None:
            self.ser.timeout = 0.8
        else:
            self.ser.timeout = timeout
        ser_temp = self.ser
        ser_temp.baudrate = 115200
        if not ser_temp.isOpen():
            ser_temp.open()
        ser_temp.flush()
        ser_temp.flushInput()
        self.l_print(0,("%s test cmd: %s" %(test_name, test_cmd)))

        while(i<self.send_count):
            ser_temp.write(test_cmd)
            res_line = []
            read_flag=0
            while True:
                temp = ser_temp.readline()
                if temp == '':
                    break
                elif break_str != None:
                    if break_str in temp:
                        res_line.append(temp)
                        self.l_print(3,'%s:%s'%(break_str,temp))
                        read_flag=1
                        break
                    res_line.append(temp)
                    self.l_print(3,'breakstr non-inside,value:%s'%temp)		    
                else:
                    res_line.append(temp)
                    self.l_print(3,'none breakstr,value:%s'%temp)
                    read_flag=1

            if(read_flag==1):
                self.l_print(3,'test sucess')

                break
            i+=1

        return res_line     
    
    def general_test_fwcheck(self):
        if(self.loadmode==1):
            return self.general_test_fwcheck_ram()
        elif(self.loadmode==2):
            return self.general_test_fwcheck_flash()
        return 1
        
    def general_test_fwcheck_flash(self):
        self.l_print(0,'start firmware check')
        self.l_print(2,'firmware check port is %s'%self.user_fw_download_port)
        self.l_print(2,'firmware check baudrate is %d'%self.user_fw_download_baud)
        try:
            self.ser.close()
        except:
            pass
        try:
            self.fwser=serial.Serial(port=self.user_fw_download_port, baudrate=self.user_fw_download_baud, 
                                     timeout=1)
        except:
            self.ui_print('OPEN FIRMWARE CHECK PORT ERROR')
            return 1

        if(self.fw_cmdEn==0):
            self.l_print(0,'fw check with no cmd')
            res,data=self._read_fw(ser=self.fwser,cmd_str='',pattern=self.fw_targetstr,ser_tout=self.user_fw_download_timeout,
                                   delay=self.user_fw_download_delay,baud=self.user_fw_download_baud)

        elif(self.fw_cmdEn):
            for param in self.cmd_group:
                temp_list=[]
                temp_list=param.split(',')
                cmd=temp_list[0]
                targetstr=temp_list[1]
                tout=temp_list[2]
                self.l_print(0,'fw check with cmden=1')
                res,data=self._read_fw(ser=self.fwser, cmd_str=cmd, pattern=targetstr,ser_tout=tout,
                                       delay=0.5,baud=self.user_fw_download_baud)
                self.l_print(3,'re-send cmd')
                try:
                    res,data=self._read_fw(ser=self.fwser, cmd_str=cmd, pattern=targetstr,ser_tout=tout,
                                           delay=0.5,baud=self.user_fw_download_baud)
                except:
                    self.ui_print("FW COM FAIL")
                    return 1                    
                if not res==True:
                    self.l_print(3,'%s cmd check firmware error'%cmd)
                    break
        try:
            self.fwser.close()
        except:
            self.l_print(0,'close fw check port error1')
        if res==True:
            self.l_print(0,'firmware check ok')
            self.ui_print('FIRMWARE CHECK OK')
            return 0
        else:
            self.l_print(0,'firmware check nok')
            return 1

    def general_test_fwcheck_ram(self):
        try:
            if(self.ser.isOpen()):
                self.ser.close()
        except:
            self.l_print(0,'close port error for firmware check__loadmode=2')
            return 1

        if(self.fw_cmdEn==0):
            self.l_print(0,'fw check with no cmd')
            try:
                check_res=fwcheck_ramdownload.run(self.COMPORT,self.BAUDRATE,self.fw_cmdEn,'',self.chip_type,self.fw_targetstr,
                                              self.user_fw_download_delay,self.user_fw_download_timeout,self.user_fw_download_port,self.user_fw_download_baud)
            except:
                self.ui_print("FW COM FAIL")
                return 1
        elif(self.fw_cmdEn):
            for param in self.cmd_group:
                temp_list=[]
                temp_list=param.split(',')
                cmd=temp_list[0]
                targetstr=temp_list[1]
                tout=temp_list[2]
                self.l_print(0,'fw check with cmden=1')
                try:
                    check_res=fwcheck_ramdownload.run(self.COMPORT, self.BAUDRATE, self.fw_cmdEn,cmd, self.chip_type, 
                                                  targetstr, 
                                                  0.5, 
                                                  tout, 
                                                  self.user_fw_download_port,self.user_fw_download_baud)
                except:
                    self.ui_print("FW COM FAIL")
                    return 1                
                if not check_res:
                    self.l_print(3,'%s cmd check firmware error'%cmd)
                    break
        if check_res:
            self.ui_print('FIRMWARE CHECK OK')
            return 0
        else:
            self.ui_print('FIRMWARE CHECK ERROR')
            return 1


    def _read_fw(self,ser,cmd_str,pattern,ser_tout = 1,delay = 1, baud = None):
        if not ser.isOpen():

            ser.open()
        if not baud == None:
            print "set new baud: ", baud
            ser.baudrate = baud

        ser.timeout = 0.5

        start_time = time.time()

        if not cmd_str == '':
            ser.write(cmd_str+"\r\n")
        if pattern == None:
            return (True,None)
        while True:
            line = ser.read(1024)
            self.l_print(3,'firmware check read line:%s'%line)
            if pattern.upper() in line.upper():
                #ser.close()
                return (True,line)  
            elif line == '':
                ser.close()
                return (False,None)
            else:
                pass
            if delay>0:
                self.msleep(int(1000*delay))
            if time.time() - start_time >= ser_tout:
                self.l_print(3,'read firmware version timeout')
                return (False, None)
        pass

    ### COMMON TEST -------------------------------- ###
    @serial_operation
    def try_sync(self):
        self.ui_print('[state]SYNC')
        if(self.loadmode==1):	# ram test mode
            rst = self.try_sync_ram()
        elif self.loadmode == 2:    # flash test mode 
            rst = self.try_sync_flash()
        else:
            rst = -1
        return rst

    def try_sync_flash(self, ser):
        '''
        try synchronous the chip with flash jump mode via uart, the program need deal with follow 4 case, within most 5 seconds
        case 1: (chip already power on and running in test mode, serial baudrate in 115200) 
        case 2: (chip already power on but runing in normal mode)
        case 3: (chip from power off to power on)
        case 4: (chip not power on, or other error)

        Returns:
            0: sycn success
            1: into normal mode, and already test pass
            -2: into normal mode without test pass
            -3: sync timeout
            -4: error cause read from serial
        '''
        try:
            self.ser = serial.Serial(port=self.COMPORT, baudrate=self.BAUDRATE, timeout=0.1)
        except:
            self.ui_print('open serial fail')
            return -1 # open serial fail
        cmd='esp_read_efuse_128bit\r'
        self.ser.write(cmd)
        rst = self.ser.readline()
        if rst.find('esp_read_efuse_128bit:') >= 0:
            return 0

        timeout = 5
        if self.dutconfig['chip_conf']['freq'] == '26M':
            self.ser.baudrate = 74880
        t = time.time()
        while time.time()-t < timeout:
            try:
                rl = self.ser.readline()
            except:
                return -4 # error cause read from serial
            if rl.find('pass flag res:1') >= 0:
                return 2 # into normal mode, and already test pass
            elif rl.find('pass flag res:0') >= 0:
                return -2 # into normal mode without test pass
            elif rl.find('jump to run test bin') >= 0:
                return 0 # into test mode
            if len(rl)>1: 
                if DEBUG: print rl

        return -3 # sync timeout 

    def try_sync_ram(self):
        '''
        try sycn the chip by slip cmd within 20 times
        '''
        sync_res = 0
        sync_count=0
        connect_status = 1
        self.memory_download.disconnect()
        try:
            connect_res = self.memory_download.com_connect(self.COMPORT, self.BAUDRATE)
            self.ser=self.memory_download.esp._port
            self.l_print(0,'conncet result is %d'%connect_res)
        except serial.SerialException:
            return -1

        if connect_res:
            self.memory_download.ESP_SET_BOOT_MODE(0)   #try outside io control boot mode
            while(sync_count<=20):

                sync_count+=1
                self.l_print(3,("sync_count is : %d "%sync_count))
                self.ui_print("sync_count is : %d "%sync_count)
                self.msleep(300)      #delay to run uart_connect() again , if shorter than 0.2, fail to connect again

                try:
                    sync_res = self.memory_download.device_sync()
                    self.l_print(2,'sync res is %d'%sync_res)
                    if sync_res > 0:    #should be status 1 or 2
                        connect_status = 1
                        self.memory_download.esp._port.setDTR(False)
                        try:
                            if not (self.chip_type.find("ESP32")>=0) and not self.chip_type == "ESP8089":
                                self.memory_download.set_higher_baud(1152000)
                        except:
                            sync_res = 0
                    else:
                        connect_status = 0
                except:
                    connect_status = 0

                if sync_res == 1:
                    self.l_print(0,'chip sync ok')
                    return 0
                else:
                    self.l_print(3,'chip sync Nok,re-sync again')
            else:
                sync_res = 0
                return 1

    def check_chip(self):
        if self.loadmode == 2:
            return self.check_chip_flash()
        elif self.loadmode == 1:
            return self.check_chip_ram()

    def check_chip_flash(self):
        '''
        try check chip's mac and efuse
        '''
        getmac_res=0
        self.memory_download.disconnect()
        try:
            self.ser = serial.Serial(port=self.COMPORT, baudrate=self.BAUDRATE,timeout=0.5)
            self.l_print(0,'serial open ok')
            self.ui_print('SER OPEN OK')
        except serial.SerialException:
            self.ui_print('SERIAL PORT EXCEPTION')
            return 1

        try:
            getmac_res=self.memory_download.esp_getmac(self.ser)
        except:
            self.l_print(3,'get mac error')
            return 1

        if getmac_res:   
            self.l_print(1,self.memory_download.ESP_MAC)
            self.MAC=self.memory_download.ESP_MAC.replace('0x','').replace('-','').replace(':','')
            self.l_print(3,"mac sta: %s"%self.memory_download.ESP_MAC) 
            self.ui_print('[mac]{}'.format(self.MAC))
            self.logpath=self.esp_gen_log()
            if(self.logpath is not ''):
                return 0
            else:
                self.ui_print('GEN LOG PRINT NOK')
                return 1
        return 1

    def check_chip_ram(self):
        if self.sub_chip_type == 'ESP32D2WD':
            self.memory_download.esp_config_spi_mode()
        if self.en_tx_test>0 or self.en_rx_test > 0:
            if self.tester_con_flg==1: 
                self.ui_print('CONNECT TESTER OK')
            elif self.tester_con_flg==0: 
                self.ui_print('CONNECT TESTER NOK')
        else:
            self.ui_print('CONNECT TESTER SKIPED')

        flash_res = self.memory_download.get_flash_id(self.memory_download.esp)
        if flash_res == False:
            return 1
        if(not self.chip_type == 'ESP8089'):
            if(self.memory_download.flash_device_id != 0):
                self.l_print(3,'flash detected')
            else:
                self.l_print(3,'error,flash not detected')
                self.log_item("ERROR! FLASH NOT DETECTED!")
                return 1

        if self.set_mac_en == 0 :
            pass

        try:
            res = self.memory_download.get_mac()
        except:
            return 1
        if res == True:
            self.MAC=self.memory_download.ESP_MAC.replace('0x','').replace('-','').replace(':','')
            self.l_print(3,"mac sta: %s"%self.memory_download.ESP_MAC) 
            self.ui_print('[mac]{}'.format(self.MAC))

            if(not self.chip_type == 'ESP8089'):
                self.flash_manufacturer_id=self.memory_download.flash_manufacturer_id
                self.flash_dev_id=self.memory_download.flash_device_id
            if self.set_mac_en==0:
                self.l_print("mac ap: %s"%self.memory_download.ESP_MAC_AP)
        elif res==False:
            self.l_print(3,"get mac failed...")
            sync_res=0
            self.memory_download.disconnect()
            connect_res=0
            self.memory_download.stopFlg=1
            self.l_print(0,'read reg failed : reset connect_res and sync_res..')
            if self.testflow.set_mac_en==1:
                pass
            else:
                self.ui_print('GET MAC FAILED')
        elif res==-1:
            self.l_print(3,"EFUSE CHECK failed...")
            sync_res=0
            self.memory_download.disconnect()
            connect_res=0
            self.memory_download.stopFlg=1

            self.l_print(0,'EFUSE CHECK ERROR...')
            if self.testflow.set_mac_en==1:
                pass
            else:
                self.l_print(3,"CHIP EFUSE CHECK ERROR!!! FAIL")
            self.ui_print("CHIP EFUSE CHECK ERROR!!! FAIL")

        else:
            self.l_print(3,"read reg failed...")
            self.memory_download.disconnect()
            self.memory_download.stopFlg=1
            self.l_print(3,'read reg failed : reset connect_res and sync_res..')
            if self.window.set_mac_en==1:
                pass
            else:
                self.ui_print('READ REGISITER ERROR')

        self.logpath=self.esp_gen_log()
        try:
            if self.logpath is not '':
                self.l_print(0,'log path is %s'%self.logpath)
        except:
            self.ui_print('GENERAL LOG FAIL')
            return 1

        return 0

    ### OTHER FUNCTIONS -------------------------------- ###
    def rpt_append(self,item,value,thres_l=-1000,thres_h=1000):
        testitem_str=item
        #if(eval(value)>eval(item_thres_h_dict[testitem[item]])) or (eval(value)<eval(item_thres_l_dict[testitem[item]])):
        if(value>thres_l) and (value<thres_h):
            res='PASS'
        else:
            res='FAIL'
        value_str=str(value)
        spec_l_str=str(thres_l)
        spelc_h_str=str(thres_h)
        res_str=res

        tempstr=testitem_str+','+value_str+','+spec_l_str+','+spelc_h_str+','+res_str+'\n'

        self.rptstr=self.rptstr+tempstr
        return 0  

    
    def esp_gen_rpt(self):
        tool_ver=self.tool_ver
        chip_type=self.chip_type
        fac_=self.fac_
        po=self.po
        mac=self.MAC
        res=self.resflag
        if(res==1):
            res='PASS'
        else:
            res='FAIL'
        rptstr=self.rptstr
        _path='C:/ESP_REPORT/'   
        timestr=time.strftime('%Y%m%d%H-%M-%S',time.localtime(time.time()))
        try:
            if(not os.path.exists(_path)):
                os.makedirs(_path)


            filename=_path+po+'__'+res+mac+'_'+timestr+'.csv'
            title_str='********************-----ESP MODULE TEST REPORT-----********************'+'\r\n'
            ver_str='TEST TOOL VERSION:'+tool_ver+'\r\n'
            chip_str='CHIP TYPE:'+chip_type+'\r\n'
            fac_str='FACTORY:'+fac_+'\r\n'
            title=title_str+ver_str+chip_str+fac_str
            rptstr=title+rptstr
            with open(filename,'a') as fn:
                fn.write(rptstr)
        except:
            print 'esp report creat error'    

            """
            esp print type definition:
            type 0 means normal print
            type 1 means parameter input
            type 2 means parameter output,eg,test value in reg..
            type 3 means debug print,eg,some import information for debug read

            """             
    def l_print(self,print_type=0,log_str=''):
        sys.stdout=sys.stdout
        esp_logpath=self.logpath
        try:
            if(print_type==0):
                temp_str=log_str+'\r\n'
                print(log_str)
                with open(esp_logpath,'a') as fn:
                    fn.write(temp_str)

            elif(print_type==1):
                temp_str='[para_in]:'+log_str+'\r\n'
                print(log_str)
                with open(esp_logpath,'a') as fn:
                    fn.write(temp_str)

            elif(print_type==2):
                temp_str='[para_out]:'+log_str+'\r\n'
                print(log_str)
                with open(esp_logpath,'a') as fn:
                    fn.write(temp_str)

            elif(print_type==3):
                temp_str='[debug]:'+log_str+'\r\n'
                print(log_str) 
                with open(esp_logpath,'a') as fn:
                    fn.write(temp_str)
        except IOError:
            self.esp_logstr=self.esp_logstr+temp_str    

    def esp_gen_log(self):
        logpath='..//logs//'
        mac=self.MAC
        tool_ver=self.tool_ver
        chip_type=self.chip_type
        fac_=self.fac_
        timestr=time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))
        filename=mac+timestr+'.txt'
        logpath=logpath+filename
        title_str='********************-----ESP MODULE TEST LOG-----********************'+'\r\n'
        ver_str='TEST TOOL VERSION:'+tool_ver+'\r\n'
        chip_str='CHIP TYPE:'+chip_type+'\r\n'
        fac_str='FACTORY:'+fac_+'\r\n'
        title=title_str+ver_str+chip_str+fac_str  
        try:
            with open(logpath,'a') as fn:
                fn.write(title)
                fn.write(self.esp_logstr)
        except:
            logpath=''
            return logpath
        return logpath

    def ui_print(self,log):
        if log.endswith('OK'):
            v_l=log.split(' ')
            temp_str=log[:len(v_l[-1])*-1]
            re_filling=22
            fill_num=re_filling-len(temp_str)
            re_fill_str=' '
            re_fill_str=re_fill_str*fill_num
            log=temp_str+re_fill_str+v_l[-1]
            
        self._stdout.write(log)

    def upload_server(self, rst, err_code):
        no_err      = "0x00" 
        err_params  = "0x01"
        err_conn    = "0x02"
        err_upload  = "0x03"
        err_other   = "0xff"
        
        repeat_check = 'True' if self.dutconfig['common_conf']['repeat_check']=='1' else 'False'
        po_type = self.dutconfig['common_conf']['po_type']
        
        err_msg = {
            "err_code" : no_err,
            "err_info" : ''
        }
        up_data = {"server_ip":"120.76.204.21", 
                   "server_port":"6666", 
                   "device_type":str(self.dutconfig['chip_conf']['chip_type']), 
                   "fw_ver":str(self.dutconfig['common_conf']['fw_ver']), 
                   "esp_mac":str(self.MAC), 
                   "cus_mac":"", 
                   "flash_id":"", 
                   "test_result":rst, 
                   "factory_sid":str(self.dutconfig['common_conf']['fac_sid']), 
                   "batch_sid":str(self.dutconfig['common_conf']['batch_sid']), 
                   "efuse":"", 
                   "chk_repeat_flg":repeat_check, 
                   "po_type":po_type}

        uploader = upload_to_server.Uploader(up_data)
        try:
            t_err, rsp = uploader.client()
            if t_err != 0:
                err_msg["err_code"] = err_conn
                err_msg["err_info"] = "tcp conn error"
            elif rsp["status"] == 500:
                err_msg["err_code"] = err_upload
                err_msg["err_info"] = rsp["message"]
            elif rsp["status"] == 200:
                err_msg["err_code"] = no_err
                err_msg["err_info"] = "send to server success"
            else:
                err_msg["err_code"] = err_other
                err_msg["err_info"] = "unknow error"
        except:
            err_msg["err_code"] = err_conn
            err_msg["err_info"] = "tcp conn error"
            self.l_print(3,'upload result:\n'+err_msg['err_code']+':'+err_msg["err_info"]+'\n')
            return 1

        print (err_msg)
        if err_msg['err_code'] == '0x00':
            index= str(rsp['batch_index'])
            total= str(rsp['batch_cnt'])
            self.ui_print('[upload]'+index+'/'+total)
            self.ui_print('UPLOAD OK')
            self.l_print(3,'upload result:\n'+err_msg['err_code']+':'+err_msg["err_info"]+'\n')
            return 0
        else:
            print err_msg["err_info"]
            self.l_print(3,'upload result:\n'+err_msg['err_code']+':'+err_msg["err_info"]+'\n')
            return 1

    def esp_write_flash(self):
        self.l_print(0,'ALL TEST PASS,WRITE PASS FLAG')
        cmdstr=self.time2cmdstr()
        print cmdstr
        try:
            self.ser.flushInput()
            self.ser.flushOutput()
            self.msleep(100)
            self.ser.write(cmdstr)
        except:
            self.l_print(3,'write pass info nok1')
            self.ui_print('WRITE PASS INFO NOK1')
            return 1

        temp=self.ser.readline()
        print temp
        if 'esp_set_fac_info_pass' in temp:
            self.l_print(3,'write pass info ok2')
            self.ui_print('WRITE PASS INFO OK2')
            return 0

        elif 'start ok' in temp:
            self.l_print(3,'write pass info ok4')
            self.ui_print('WRITE PASS INFO OK4')
            return 0
        else:
            self.l_print(3,'write pass info nok3')
            self.ui_print('WRITE PASS INFO NOK3')
            return 1

    def reboot(self):
        try:
            if self.ser.isOpen():
                self.ser.close()
                self.msleep(100)
        except:
            self.l_print(0,'close port exception')
        self.ser=serial.Serial(port=self.COMPORT, baudrate=self.BAUDRATE, timeout=3)	

        cmd='esp_en_reboot\r'
        self.l_print(0,'write reboot cmd')	    
        self.ser.write(cmd)
        self.ser.write(cmd)
        #if self.dutconfig['chip_conf']['freq'] == '26M':
        #    self.ser.baudrate = 74880	    
        rst = self.ser.readline()

        print '1'+rst
        if rst.find('pass flag res:1') >= 0:
            return 0

        timeout = 10
        t = time.time()
        while time.time()-t < timeout:
            rl = self.ser.readline()
            print '2'+rl
            if rl.find('pass flag res:1') >= 0:

                return 0 
            elif rl.find('pass flag res:0') >= 0:

                return -1 
            elif rl.find('jump to run test bin') >= 0:

                return -2 
            print rl

        return -3 

    def time2cmdstr(self):
        timestr=time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
        facstr='11'
        cmdstr=''
        temp=facstr+'-'+timestr
        for i in temp:
            if i=='-':
                i='0x2d'
            else:
                i='0x3'+i

            cmdstr+=i+' '
        cmdstr=cmdstr+'\r'
        cmdstr='esp_set_flash_test_pass_info'+' '+cmdstr
        return cmdstr        
 
    @serial_operation
    def STOPTEST(self, err_code=0x0):        
        if err_code == -1 and self.resflag==1: # not even sync
            return
            
        if self.resflag == 1:
            self.esp_gen_rpt()
            if self.position == 'cloud':
                if self.upload_server('fail', err_code) != 0:
                    self.ui_print('[state]fail_record'+',0x04')
                    self.ui_print('[state]upload-f')
                    self.stop_flag = 1
                else:
                    self.ui_print('[state]fail_record'+','+str(err_code))
            else:
                self.ui_print('[state]fail_record'+','+str(err_code))
        elif self.resflag == 0:
            self.l_print(0,'all item test passed')
            self.esp_gen_rpt()
            if self.position == 'cloud':
                if self.upload_server('success', err_code) != 0:
                    self.ui_print('[state]fail_record'+',0x04')
                    self.ui_print('[state]upload-f')
                    self.stop_flag = 1
                else:
                    self.ui_print('[state]pass_record')
            else:
                self.ui_print('[state]pass_record')
        elif self.resflag==2:
            self.l_print(0,'already passed module')
            self.ui_print('[state]passed')         

        if self.resflag in (0,2):
            if self.autostartEn:
                self.msleep(5000)
        else:
            while not self.stop_flag:
                try:
                    getmac_res=self.memory_download.esp_getmac(self.ser)
                except:
                    break
                if getmac_res:
                    temp_mac=self.memory_download.ESP_MAC.replace('0x','').replace('-','').replace(':','')
                    if temp_mac != self.MAC:
                        break
                else:
                    break
                self.msleep(300)

    def stopthread(self):
        self.ui_print('[state]finish btn up')
        self.ui_print('[state]idle')
        
        try:
            self.ser.close()
        except:
            pass
        self.terminate()

    def ui_stop(self):
        self.stop_flag = 1
        self.stopthread()

    def set_params(self,stdout_='',dutconfig='',testflow=''):
        try:
            self.send_cmd=[]
            self.fwstr_withcmd=[]
            self.fwtmo_withcmd=[]
            self.cmd_group=[]
            self.testflow=testflow
            self.dutconfig=dutconfig
            self._stdout=stdout_
            self.slot_num =self.dutconfig['common_conf']['dut_num']
            self.COMPORT=self.dutconfig['DUT'+self.slot_num]['port1']	
            self.BAUDRATE=int(self.dutconfig['DUT'+self.slot_num]['rate1'])
            self.sub_chip_type=self.dutconfig['chip_conf']['chip_type'].replace('-','')
            self.autostartEn=int(self.dutconfig['common_conf']['auto_start'])
            self.loadmode=self.dutconfig['common_conf']['test_from']
            self.efusemode=int(self.dutconfig['chip_conf']['efuse_mode'])
            self.user_fw_download_port=self.dutconfig['DUT'+self.slot_num]['port2']
            self.user_fw_download_baud=int(self.dutconfig['DUT'+self.slot_num]['rate2'])
            self.user_fw_download_delay=int(self.testflow['USER_FW_VER_DELAY(s)'])
            self.user_fw_download_timeout=int(self.testflow['USER_FW_VER_TIMEOUT(s)'])
            self.IMGPATH=self.dutconfig['common_conf']['bin_path']
            self.fac_=self.dutconfig['common_conf']['fac_sid']
            self.po=self.dutconfig['common_conf']['po_no']
            self.position=self.dutconfig['common_conf']['position']
            self.en_user_fw_check=int(self.testflow['USER_FW_CHECK'])
            self.fw_targetstr=self.testflow['USER_FW_VER_STR']
            self.fw_cmd_combin=self.testflow['USER_TEST_CMD<cmd,rsp,tmo>']
            self.threshold_path = self.dutconfig['common_conf']['threshold_path']
        except:
            self.l_print(1,'read param error')
            self.param_read=0	        #check it before start test
            
        if self.sub_chip_type.find('ESP8266') >= 0:
            self.chip_type = 'ESP8266'
        elif self.sub_chip_type.find('ESP8285') >= 0:
            self.chip_type = 'ESP8285'
        elif self.sub_chip_type.find('ESP32') >= 0:
            self.chip_type = 'ESP32'
        
        try:
            cmd_list=self.fw_cmd_combin.replace('<',';').replace('>',';').strip(';').split(';;;')
            for cmd in cmd_list:
                t_l=cmd.replace('"',',').split(',')
                t_str=t_l[0]+','+t_l[2]+','+t_l[4]
                self.cmd_group.append(t_str)
        except:
            self.l_print(3,'read fw check cmd and fw target str error,if fw no need cmd write,ignore it')
        if self.fw_targetstr.upper()=='ESPCMD_EN':
            self.fw_cmdEn=1
        else:
            self.fw_cmdEn=0
        if(self.loadmode=='RAM'):
            self.loadmode=1
        elif(self.loadmode=='FLASH'):
            self.loadmode=2	

        self.en_tx_test=1 if int(self.testflow['TX'])>0 else 0
        self.en_rx_test=1 if int(self.testflow['RX'])>0 else 0
        self.en_analog_test=1 if int(self.testflow['ANALOG'])>0 else 0
        self.en_gpio_8266_test=1 if int(self.testflow['GPIO_8266_TEST'])>0 else 0
        self.en_gpio_32_test=1 if int(self.testflow['GPIO_32_TEST'])>0 else 0

    def check_param(self):
        #check image avaiable
        if(self.loadmode==1):
            if not os.path.exists(self.IMGPATH):
                self.l_print(1,'IAMGE un-avaiable')
                return 1

        return 0


if __name__=='__main':
    pass