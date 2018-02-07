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
#from param_save_load import *

sys.path.append('D:\\VM\\share\\new_factory_tools\\upload_to_server')
from upload_to_server import *	

ui_STOPFLAG=0
testflow={'UART_DOLAD_EN':'1',
          'BAUDRATE':'115200',
          'CHIP_TYPE':'ESP32',
          'SUB_CHIP_TYPE':'ESP32'
}

dutconfig={'COMPORT':'COM4',
          'BAUDRATE':'115200',
          'SLOT':'1',
          'USER_FW_DL_COM':'COM4'
}   


testitem=['FREQ_OFFSET',
      'TX_POWER_BACKOFF',
      'FB_RX_NUM',
      'DUT_RX_NUM',
      'TX_VDD33_DIFF',
      'RX_NOISEFLOOR',
      'TXIQ',
      'TXDC',
      'RXIQ',
      'RXDC',
      'RSSI_DIFF',
      'VDD33',
      'TOUT'
]

item_thres_h_dict={'FREQ_OFFSET':'0x11111111',
                   'TX_POWER_BACKOFF':'0x11111111',
                   'FB_RX_NUM':'98',
                   'DUT_RX_NUM':'98',
                   'TX_VDD33_DIFF':'300',
                   'RX_NOISEFLOOR':'-345',
                   'TXIQ':'0x1111',
                   'TXDC':'124',
                   'RXIQ':'0x1111',
                   'RXDC':'384',
                   'RSSI_DIFF':'10',
                   'VDD33':'4000',
                   'TOUT':'65535'
}                   

item_thres_l_dict={'FREQ_OFFSET':'0x00000000',
                   'TX_POWER_BACKOFF':'0x00000000',
                   'FB_RX_NUM':'48',
                   'DUT_RX_NUM':'48',
                   'TX_VDD33_DIFF':'-100',
                   'RX_NOISEFLOOR':'-405',
                   'TXIQ':'0x0000',
                   'TXDC':'3',
                   'RXIQ':'0x0000',
                   'RXDC':'128',
                   'RSSI_DIFF':'-10',
                   'VDD33':'3000',
                   'TOUT':'10'
} 

class esp_testThread(QtCore.QThread):
    def __init__(self,_stdout,dutconfig,testflow):
        super(esp_testThread,self).__init__(parent=None)
	#print dutconfig
	#print testflow
        #self.dutconfig['common_conf']['chip_type']
	self.ui_STOPFLAG=0
	self.MAC = '000000000000'
        self.testflow=testflow
        self.dutconfig=dutconfig
        #self.THRESHOLD_DICT=THRESHOLD_DICT
        self._stdout=_stdout
	slot_num =self.dutconfig['common_conf']['dut_num']
	self.loadmode=self.dutconfig['common_conf']['test_from']
	if(self.loadmode=='RAM'):
	    self.loadmode=1
	elif(self.loadmode=='FLASH'):
	    self.loadmode=2
        self.COMPORT=self.dutconfig['DUT'+slot_num]['port1']
        
        self.BAUDRATE=int(self.dutconfig['DUT'+slot_num]['rate1'])
       # self.SLOT=self.dutconfig['SLOT']
        self.chip_type=self.dutconfig['chip_conf']['chip_type']
	self.chip_type='ESP8266'
        self.sub_chip_type=''
	self.autostartEn=0
        self.user_fw_download_port=self.dutconfig['DUT'+slot_num]['port2']
	self.IMGPATH='./image/ESP32_Module_Test_V128_40M_20170117_IC1229_test_init.bin'
        self.logpath=''
        self.logstr=''
	self.esp_logstr=''
	self.set_mac_en=0
	self.fac_='XINKEN'
	self.tool_ver='V0.0.1'
	self.STOPFLAG=0
	
	self.resflag = 1
	
        self.rptstr='TESTITEM'+','+'TESTVALUE'+','+'SPEC_L'+','+'SPEC_H'+','+'RESULT'+'\n'
	if(dutconfig['chip_conf']['chip_type'] == "ESP32"):
	    self.THRESHOLD_DICT=rl.get_threshold_dict('ATE','.//Threshold//full_Threshold_32.xlsx')
	else:
	    self.THRESHOLD_DICT=rl.get_threshold_dict('ATE','../RF_test/Threshold/full_Threshold_8266.xlsx')  
		
        if self.chip_type=='ESP32':
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
	while(not self.ui_STOPFLAG):
	    self.test()
		
        self.l_print(0,'quit test')
	self.ui_print('USER QUIT TEST')
	
    def try_sync(self):
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
	    rl = self.ser.readline()
	    if rl.find('pass flag res:1') >= 0:
		return 1 # into normal mode, and already test pass
	    elif rl.find('pass flag res:0') >= 0:
		return -2 # into normal mode without test pass
	    elif rl.find('jump to run test bin') >= 0:
		return 0 # into test mode
	    print rl
	    
	return -3 # sync timeout 
    
    def test(self):
	self.STOP_FLG=0
        self.flag_read_res=0
	self.txtest=int(self.testflow['TX'])
	self.rxtest=int(self.testflow['RX'])
	self.analogtest=int(self.testflow['ANALOG'])
	self.tester_con_flg=1
	self.skip_uartdownload=0
	self.tx_test_res=0
	self.rx_test_res=0
        self._date = time.strftime('%Y-%m-%d',time.localtime(time.time()))
        self._time = time.strftime('%H:%M:%S',time.localtime(time.time()))
        #self.logpath=self.esp_gen_log()
        self.tx_rx_log = ""   
        dl_result=0
	
	rst = self.try_sync()
	try:
	    self.ser.close()
	except:
	    pass
	if rst < 0:
	    self.ui_print('sync fail, please check module had plug')
	    self.resflag = 0
	    self.ui_print('[state]fail')
	    self.STOPTEST()
	elif rst == 1:
	    self.ui_print('CHIP HAS ALREADY TEST PASS')
	    self.resflag = 1
	    self.STOPTEST()
	    
        dl_result=self.test_download()
	if(self.STOPFLAG):
	    self.ui_print('DOWNLOAD FAIL')
	    self.ui_print('END TEST SEQUENCE')
	    self.STOPTEST()
	   
	if(dl_result): 
	    lg=self.get_serial_print()
	    if lg is '':
		self.l_print(0,'GET SERIAL RECORD NOK')
		self.ui_print('GET SERIAL RECORD NOK')
		self.STOPFLAG=1
		self.resflag=0
		
	    if(self.analogtest):
		self.test_analogtest(lg)
	if(self.STOPFLAG):
	    self.ui_print('RECORD FAIL')
	    self.ui_print('END TEST SEQUENCE')
	    self.STOPTEST()		
	if(dl_result):
	    if(self.txtest):
		self.l_print(0,'start tx test')
		self.test_txtest(lg)
	    if(self.STOPFLAG):
		self.ui_print('TX TEST FAIL')
		self.ui_print('END TEST SEQUENCE')
		
		self.ui_print('[state]fail')
		
		self.STOPTEST()
		
	    if(self.rxtest):
		self.l_print(0,'start rx test')
		self.test_rxtest(lg)
	    if(self.STOPFLAG):
		self.ui_print('RX TEST FAIL')
		self.ui_print('END TEST SEQUENCE')
		self.ui_print('[state]fail')
		self.STOPTEST()
		
		
	    if(self.resflag):
		self.esp_write_flash()	
		
	    if(self.resflag):
		self.reboot()
		
        if(dl_result):
	    if(self.autostartEn):
		time.sleep(3)
	    else:
		self.ui_print('[state]pass')
		time.sleep(1)
		self.STOPTEST()
    '''
    

    RF TEST--------------------------------
    
    
    '''	
	
    def test_txtest(self, lg):
	    """
	    Run tx packet test
	    """
	    #================TXTEST===================================================
	    self.l_print(0,'"TEST ITEM:')
	    
	    if self.tx_test_res == 0:
		self.tx_test_res = 1
		print(0,self.THRESHOLD_DICT.keys())
		if 'fb_rx_num' in self.THRESHOLD_DICT.keys() and self.txtest:
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
			   
			    self.l_print(3,'("FREQ_OFFSET \t%d~%d\n" %(thres_freq[0][0], thres_freq[1][0]))')
			    if tx_data[0]>4:
			    #if True: #debug
				for idx in range(len(freq_data)):
				    if int(freq_data[idx])<thres_freq[0][idx] or int(freq_data[idx])>thres_freq[1][idx]:
					self.tx_test_res=0
					self.l_print(3,"Part failure in FREQ_OFFSET : #%d ,%d !< %d !< %d \n\r"%(idx,thres_freq[0][idx],int(freq_data[idx]),thres_freq[1][idx]))
					#print "freq test failed "
					#tx_log+="Part failure in FREQ_OFFSET : #%d ,%d !< %d !< %d \n\r"%(idx,thres_freq[0][idx],int(freq_data[idx]),thres_freq[1][idx])
					self.fail_list.append("freq_test")
					self.STOPFLAG=1
					self.resflag=0
				#self.append_err_log(tx_log)
				#self.print_dbg( tx_log)
				#tx_log = ''
			    else:
				self.tx_test_res=0
				self.l_print(3,'unavailable signal')
				self.STOPFLAG=1
				self.resflag=0
				
				tx_log = ''
			elif 'txp_result' in log_tmp:
			    dlist = log_tmp.split(':')[1].split(',')[:-1]
			    txp_res = [int(x) for x in dlist]
			    thres_txp_res = self.THRESHOLD_DICT['TXP_RES']
			    idx = 0
			    val = txp_res[idx]
			    #for idx, val in enumerate(txp_res):
			  
			    self.l_print(3,("TXP_RES \t%d~%d\n" %(thres_txp_res[0][0], thres_txp_res[1][0])))
			    if val < thres_txp_res[0][idx] or val > thres_txp_res[1][idx]:
				self.tx_test_res=0
				self.l_print(3,"Part failure in TXP_RES[tx] : #%d ,%d !< %d !< %d \n\r"%(idx, thres_txp_res[0][idx], val, thres_txp_res[1][idx]))
				
				self.fail_list.append("txp_res[tx]")
				self.STOPFLAG=1
				self.resflag=0
			    tx_log = ''
			elif 'fb_rx_num' in log_tmp:
			    dlist = log_tmp.split(':')[1].split(',')[:-1]
			    if len(dlist) > 6:
				dlist = dlist[2:]
			    tx_data = [ int(x) for x in dlist]
		    if(self.tx_test_res==1):
			self.l_print(0,'TX TEST OK')
			self.ui_print('TX TEST OK')
		  
		    
		    elif self.tx_test_res==0:
			#self.fail_flg=1
			#self.retry_num+=1
			self.STOPFLAG=1
			self.resflag=0
			self.l_print(0,'TX TEST FAIL')
			self.ui_print('TX TEST FAIL')
		   
		else:
		    self.ui_print('TX TEST EXCEPTION')
		    self.STOPFLAG=1
		    self.resflag=0
    
    def test_rxtest(self, lg):
	"""
	Run RX packets test
	"""
	#=============================rx test=============================================
	if self.rx_test_res == 0:
	    self.rx_test_res = 1
	    
	    if 'dut_rx_num' in self.THRESHOLD_DICT.keys() and self.rxtest:
		
		self.l_print(0,"RX TEST BEGIN")
		
		rx_log=''
		rssi_log=''
		log_tx_rx = lg[0].split('\n')
		thres_tmp = self.THRESHOLD_DICT['dut_rx_num']
		#self.append_log("dut_rx_num \t%d~%d\n" %(thres_tmp[0][0], thres_tmp[0][1]))
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
			if self.chip_type == "ESP32":
			    print "fb_rssi for ESP32"
			    fb_rssi_v = [ max(fb_rssi_v), ]

			
			self.l_print(0,("fb_rxrssi \t%d~%d\n" %(self.THRESHOLD_DICT['fb_rxrssi'][0][0], self.THRESHOLD_DICT['fb_rxrssi'][1][0])))
			for k in range(len(fb_rssi_v)):
			    if fb_rssi_v[k]>self.THRESHOLD_DICT['fb_rxrssi'][1][k] or fb_rssi_v[k]<self.THRESHOLD_DICT['fb_rxrssi'][0][k] :
				self.rx_test_res = 0
				fb_rssi_flg = 1
				#
				self.l_print(3,"Part failure in FB_RXRSSI[%d] res: %d !< %d !< %d \r\n"%(k,self.THRESHOLD_DICT['fb_rxrssi'][0][k],fb_rssi_v[k],self.THRESHOLD_DICT['fb_rxrssi'][1][k]))
				self.STOPFLAG=1
				self.resflag=0
			if fb_rssi_flg == 1:
			    self.fail_list.append("fb_rxrssi")

			fb_rssi = int(dlist[0])
		    if 'dut_rxrssi' in log_tmp:
			dlist = log_tmp.split(':')[1].split(',')[:-1]
			dut_rssi = int(dlist[0])
			
			dut_rssi_v = [int(x) for x in dlist]
			dut_rssi_flg = 0
			if self.chip_type == "ESP32":
			    print "dut_rssi for ESP32"
			    dut_rssi_v = [ max(dut_rssi_v), ]

			
			self.l_print(3,("dut_rxrssi \t%d~%d\n" %(self.THRESHOLD_DICT['dut_rxrssi'][0][0], self.THRESHOLD_DICT['dut_rxrssi'][1][0])))
			for k in range(len(fb_rssi_v)):
			    if dut_rssi_v[k]>self.THRESHOLD_DICT['dut_rxrssi'][1][k] or dut_rssi_v[k]<self.THRESHOLD_DICT['dut_rxrssi'][0][k] :
				self.rx_test_res = 0
				dut_rssi_flg = 1
				self.STOPFLAG=1
				self.resflag=0
				self.l_print(3,"Part failure in DUT_RXRSSI[%d] res: %d !< %d !< %d \r\n"%(k,self.THRESHOLD_DICT['dut_rxrssi'][0][k],dut_rssi_v[k],self.THRESHOLD_DICT['dut_rxrssi'][1][k]))
				
			if dut_rssi_flg == 1:
			    self.fail_list.append("dut_rxrssi")

			self.l_print(3,("rssi_diff \t%d~%d\n" %(self.THRESHOLD_DICT['rssi_diff'][0][0], self.THRESHOLD_DICT['rssi_diff'][1][0])))
			
			if (dut_rssi-fb_rssi)>self.THRESHOLD_DICT['rssi_diff'][1][0] or (dut_rssi-fb_rssi)<self.THRESHOLD_DICT['rssi_diff'][0][0] :
			    
			    self.rx_test_res = 0
			    self.resflag=0
			    self.STOPFLAG=1
			    self.l_print(3,"Part failure in RSSI res: FB: %d ; DUT: %d, %d !< %d !< %d \r\n"%(fb_rssi,dut_rssi,self.THRESHOLD_DICT['rssi_diff'][0][0],(dut_rssi-fb_rssi),self.THRESHOLD_DICT['rssi_diff'][1][0]))
			    
			    #self.print_dbg( rssi_log)
			    self.fail_list.append("rssi")
			

		    if 'txp_result' in log_tmp:
			dlist = log_tmp.split(':')[1].split(',')[:-1]
			txp_res = [int(x) for x in dlist]
			thres_txp_res = self.THRESHOLD_DICT['TXP_RES']
			self.l_print(3,("TXP_RES \t%d~%d\n" %(thres_txp_res[0][1], thres_txp_res[1][1])))
			
			idx = 1
			val = txp_res[idx]
			#for idx, val in enumerate(txp_res):
			if val < thres_txp_res[0][idx] or val > thres_txp_res[1][idx]:
			    self.rx_test_res=0
			    self.STOPFLAG=1
			    self.resflag=0
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
		elif(self.rx_test_res==0):
		    self.STOPFLAG=1
		    self.resflag=0
		    self.l_print(0,'RX TEST NOK')
		    self.l_print('RX TEST NOK')		    
		
		

	    else:
		self.STOPFLAG=1
		self.resflag=0
		self.l_print(3,'RX TEST EXCEPTION')
		self.ui_print('RX TEST EXCEPTION')
    	    
    def test_analogtest(self,lg):
	if not lg[0]=='':
	    self.l_print(0,lg[0])
	    self.data_process(0)
	    if(self.ana_test_result):
		self.l_print(0,'analog test ok')
		self.ui_print('ANALOG TEST OK')
		#self.ui_print('[state]PASS')
		#self.STOPTEST()
	    else:
		self.l_print(0,'analog test nok')
		self.ui_print('ANALOG TEST NOK')
		self.STOPFLAG=1
		self.resflag=0
		
    def data_process(self,block_num):
	self.l_print(0,"Data Processing...\n")
        
        start=time.clock()
        if True:
            if self.chip_type == "ESP32":
                print "ESP32:"
                values_dictlist=rl.read_log_data(self.logpath,'ESP32',block_num)
                #for key in values_dictlist[0].keys():
                    #if "BT" in key or "WIFI" in key or "TXDC" in key or "RXDC" in key:
                        #print "key:",key
                        #print "val:",values_dictlist[0][key]
                        #print "------------"
            else:
                values_dictlist=rl.read_log_data(self.logpath,'module2515',block_num)

            print "test len : ",len(values_dictlist)
            #print "dut_rxrssi:",values_dictlist[0]['dut_rxrssi']
            #print "fb_rxrssi :",values_dictlist[0]["fb_rxrssi"]
        else:#debug
            ##debug for print
            print("=============================\r\n\r\n")
            print("this is only for log process debug\r\n")
            print("should never be here in a formal version\r\n")
            #values_dictlist=rl.read_log_data('./logs/print/'+"2015-06-07_print/0x0_A132AA_prnt_1_2015-06-07_18_58_05.txt",'module2515')
            print("===============================\r\n\r\n")
        value_tmp = []
        #self.print_dbg(("block num:",block_num))
       # self.print_dbg(("self.retry:",self.retry_num))
        value_tmp.append( values_dictlist[block_num])
        #_res=rl.data_process_dictList_2(values_dictlist,self.THRESHOLD_DICT,self.window.adc_test_en)
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

        #if not os.path.exists(self.window.log_path+'/logs/log/'+self._date+'_log'):
       #     os.makedirs(self.window.log_path+'/logs/log/'+self._date+'_log')
       # self.print_dbg(self.fn.replace('prnt','log').replace('print','log'))
       # spud.record_log_test( _res[1] ,self.window.log_path+'/logs/log', self.fn.replace('prnt','log').replace('print','log'),TOOL_VERSION+"\r\nFACTORY: %s"%self.window.factory_info+"\r\n\n" )
        self.t_dataprocess=time.clock()-start    
	 	
    def get_serial_print(self):
        start=time.clock()
        #self._date = time.strftime('%Y-%m-%d',time.localtime(time.time()))
        #self._time = time.strftime('%H:%M:%S',time.localtime(time.time()))
        self.l_print(0,'record serial print ')
        
	retry = False
        #print "&&&&&&&&&&&&&&&&&&&&&"
        #print "retry: ",retry
        #print "&&&&&&&&&&&&&&&&&&&&&"
        if self.chip_type == "ESP8089":
            lg=spud.get_serial_line_id(self.ser,'MODULE_TEST START!!!','req_suc',retry = retry,chip_type = self.chip_type) #'user code done')
        elif self.chip_type == "ESP32":
            lg=spud.get_serial_line_id(self.ser,'MODULE_TEST START!!!','MODULE_TEST EDN!!!',retry = retry,chip_type = self.chip_type) #'user code done')
        else:
            lg=spud.get_serial_line_id(self.ser,'MODULE_TEST START!!!','MODULE_TEST END!!!',retry = retry,chip_type = self.chip_type) #'user code done')
        #spud.test_get_serial(self.COM_PORT,GET_SER_BR)
        #self.print_dbg("debug:\n-----------------\r\n")
        #self.print_dbg(lg)
        #self.print_dbg("debug end-------------------\r\n")
       # self.print_dbg('Got Serial print...')
       # self.t_getserial=time.clock()-start
        return lg    
        
    def test_download(self):
        """
        Download test firmware to the chip memory
        """
        #===================UART_DOWNLOAD================================
        dl_result = False
        self.st=time.clock()
        start=time.clock()
        if self.loadmode==1:
	    self.l_print(0,'load to ram')
            dl_result=self.uartdownload_gui(self.IMGPATH)
	    self.l_print(3,'dl_result is %d'%dl_result)
	elif self.loadmode==2:
	    self.l_print(0,'load to flash')
	    dl_result=self.flash_uartdownload_gui()
            #self.print_dbg(('test dl_result : ',dl_result))
	    self.l_print(3,'dl_result is %d'%dl_result)
        else:
	    self.l_print(3,'dl_result skiped')
            self.ui_print('dl_result skiped')
            try:
                ser_test = serial.Serial(self.COM_PORT-1,115200,timeout=1.2)
                ser_test.close()
                while ser_test.isOpen()==True:
                    time.sleep(0.1)
                    #self.print_dbg("test discom")
		    self.l_print(3,'test disconnect')
                dl_result = True
            except:
                self.window.STOP_FLG=1
                self.memory_download.stopFlg=1
		self.l_print(3,'open comport error...')
                
                dl_result=False
        self.t_uartdownload=time.clock()-start
        if dl_result:
            self.ui_print('UART DOWNLOAD OK')
        else:
            self.ui_print('UART DOWNLOAD ERROR')
        return dl_result
    
    def flash_uartdownload_gui(self):
	sync_res=0
	com_port=self.COMPORT
	sync_count=0
	connect_status=1
	dl_result=0
	getmac_res=0
	self.memory_download.disconnect()
	try:
            #connect_res = self.memory_download.com_connect(self.COMPORT, BR)
	    self.ser = serial.Serial(port=com_port, baudrate=self.BAUDRATE,timeout=1)
	   # cmd='esp_read_efuse_128bit\r'
	   # self.ser.write(cmd)	    
	    self.l_print(0,'serial open ok')
	    self.ui_print('SER OPEN OK')
        except serial.SerialException:
            #self.STOP_FLG = 1
            self.ui_print('SERIAL PORT EXCEPTION')	
	    self.STOPTEST()
	#temp=ser.read(128)
	
	try:
	    getmac_res=self.memory_download.esp_getmac(self.ser)
	    
	except:
	    self.l_print(3,'get mac error')
	    self.STOP_FLG=1
	    self.resflag=0
	if(getmac_res):   
	    self.MAC=self.memory_download.ESP_MAC.strip('0x').replace('-','').replace(':','')
	    self.l_print(3,"mac sta: %s"%self.memory_download.ESP_MAC) 
	    self.ui_print('[mac]{}'.format(self.MAC))
	    self.logpath=self.esp_gen_log()
	    dl_result=1
	
	return dl_result
	
	#self.fac_testcmd='esp_set_flash_jump_start 1\r' 
	#self.ser.write(self.fac_testcmd)
	#temp=self.ser.readlines()
	#self.ui_print(temp)
	
    def uartdownload_gui(self,image_path="image/init_data.bin"):
        #connect_res = 0
        sync_res = 0
        com_port = self.COMPORT
        BR=self.BAUDRATE
        sync_count=0
        connect_status = 1
        #connect_res = 0
        self.memory_download.disconnect()
        time.sleep(1.5)
	#self.window.former_mac=0
	self.l_print(0,'target bin is %s'%image_path)
        try:
            connect_res = self.memory_download.com_connect(self.COMPORT, BR)
	    self.l_print(0,'conncet result is %d'%connect_res)
        except serial.SerialException:
            self.testflow.STOP_FLG = 1
            return False
                #sync_count += 1
                #time.sleep(0.5)
                #continue
            #if connect_res == 0:
                #sync_count += 1
            #else:
                #break
        #sync_count = 0

        if connect_res == 1:
            self.memory_download.ESP_SET_BOOT_MODE(0)   #try outside io control boot mode
            while(self.ui_STOPFLAG==0 and sync_count<=20):
		self.l_print(4,("test : self.STOP_FLG:%d"%self.STOP_FLG))
                
                sync_count+=1
		self.l_print(4,("sync_count is : %d "%sync_count))
                time.sleep(0.3)      #delay to run uart_connect() again , if shorter than 0.2, fail to connect again
                if self.STOP_FLG==0:
                    
                    try:
                        sync_res = self.memory_download.device_sync()
			self.l_print(2,'sync res is %d'%sync_res)
                        if sync_res:    #should be status 1 or 2
                            self.memory_download.get_mac()
			    self.l_print(1,'esp mac is %s'%self.memory_download.ESP_MAC)
			    self.logpath=self.esp_gen_log()
                            try:
				if self.logpath is not '':
				    self.l_print(0,'log path is %s'%self.logpath)
			    except:
				pass
			    connect_status = 1
			    self.memory_download.esp._port.setDTR(False)
			    try:
				if not self.chip_type == "ESP32" and not self.chip_type == "ESP8089":
				    self.memory_download.set_higher_baud(1152000)
			    except:
				sync_res = 0
                        else:
                            connect_status = 0
                    except:
                        #self.print_dbg("error when start sync again  =================")
                       # wx.CallAfter(self.window.show_result, -2)
                        connect_status = 0
                    if sync_res == 1:
			self.l_print(0,'chip sync ok')
			self.ui_print('CHIP SYNC OK')
                        break
                    else:
                        self.l_print(4,'chip sync Nok,re-sync again')
            else:
                sync_res = 0
		self.ui_print('CHIP SYNC NOK')
                self.STOP_FLG=1
                self.memory_download.stopFlg=1
                
        else:
            
	    self.l_print(4,("Failed to connect COM: %s  \n"%self.COMPORT))
	    self.ui_print('CONNECT COMPORT NOK')
            self.STOP_FLG=1
            self.memory_download.stopFlg=1

        if self.sub_chip_type == 'ESP3D2WD':
            self.memory_download.esp_config_spi_mode()
        if connect_res==1 and sync_res==1:
            #self.window.textCtrl_logWindow.Clear()
            if self.txtest==1 or self.rxtest==1:
                if self.tester_con_flg==1:
                    self.ui_print('CONNECT TESTER OK')
                   
                elif self.tester_con_flg==0:
                    self.ui_print('CONNECT TESTER NOK')
                  #  self.log_test_res(1,0)
                
		
            else:
		self.ui_print('CONNECT TESTER SKIPED') 
            flash_res = self.memory_download.get_flash_id(self.memory_download.esp)
            if flash_res == False:
                self.STOP_FLG = 1
                return False
            if(not self.chip_type == 'ESP8089'):
                if(self.memory_download.flash_device_id != 0):
		    self.l_print(3,'flash detected')
                    #self.log_item("FLASH DETECTED")
                else:
		    self.l_print(3,'error,flash not detected')
                    self.log_item("ERROR! FLASH NOT DETECTED!")
                    return False
            #self.log_item(2)
	    self.ui_print('UART DOWNLOADing...')
            #wx.CallAfter(self.window.show_result, -3)
            if self.set_mac_en == 0 :
	    
               # wx.CallAfter(self.window.show_chip_id, "","")
		pass

            if True:
                if connect_res==1 and sync_res==1:
                    #res=self.memory_download.get_mac()
                    #res = True
                    res = self.memory_download.get_mac()

                    

                    if res == True:
                        self.ESP_MAC_STA = self.memory_download.ESP_MAC_STA
                        if(not self.chip_type == 'ESP8089'):
                            self.flash_manufacturer_id=self.memory_download.flash_manufacturer_id
                            self.flash_dev_id=self.memory_download.flash_device_id
                        if self.set_mac_en==0:
                           # wx.CallAfter(self.window.show_chip_id, self.memory_download.ESP_MAC_AP,self.memory_download.ESP_MAC_STA)
                           # self.print_dbg( "mac ap: %s"%self.memory_download.ESP_MAC_AP)
                           # self.print_dbg( "mac sta: %s"%self.memory_download.ESP_MAC_STA)
			    self.ui_print("mac ap: %s"%self.memory_download.ESP_MAC_AP)
			    self.ui_print("mac sta: %s"%self.memory_download.ESP_MAC_STA)
                    elif res==False:
                        self.l_print(3,"get mac failed...")
                        sync_res=0
                        self.memory_download.disconnect()
                        connect_res=0
                        self.STOP_FLG=1
                        self.memory_download.stopFlg=1
			self.l_print(0,'read reg failed : reset connect_res and sync_res..')
                        #self.print_dbg('read reg failed : reset connect_res and sync_res..')
                        if self.testflow.set_mac_en==1:
                            pass
                        else:
                            #wx.CallAfter(self.window.show_chip_id, "error","error")
			    self.ui_print('GET MAC FAILED')
                    elif res==-1:
                        #self.print_dbg("EFUSE CHECK failed...")
			self.l_print(3,"EFUSE CHECK failed...")
                        sync_res=0
                        self.memory_download.disconnect()
                        connect_res=0
                        self.STOP_FLG=1
                        self.memory_download.stopFlg=1
                       # self.print_dbg('EFUSE CHECK ERROR...')
			self.l_print(0,'EFUSE CHECK ERROR...')
                        if self.testflow.set_mac_en==1:
                            pass
                        else:
			    self.l_print(3,"CHIP EFUSE CHECK ERROR!!! FAIL")
                        #    wx.CallAfter(self.window.show_chip_id, "error","error")
                       # wx.CallAfter(self.window.LogMessage, "CHIP EFUSE CHECK ERROR!!! FAIL\n\n\n")
			self.ui_print("CHIP EFUSE CHECK ERROR!!! FAIL")
                    else:
                      #  self.print_dbg("read reg failed...")
			self.l_print(3,"read reg failed...")
                        sync_res=0
                        self.memory_download.disconnect()
                        connect_res=0
                        self.STOP_FLG=1
                        self.memory_download.stopFlg=1
			self.l_print(3,'read reg failed : reset connect_res and sync_res..')
                       # self.print_dbg('read reg failed : reset connect_res and sync_res..')
                        if self.window.set_mac_en==1:
                            pass
                        else:
                           # wx.CallAfter(self.window.show_chip_id, "error","error")
			    self.ui_print('READ REGISITER ERROR')
        if connect_res==1 and sync_res==1:
            #self.print_dbg(("Start UartDownload...,",image_path))
	    self.l_print(3,("Start UartDownload...,%s"%image_path))

            #time.sleep( self.start_delay*1.0/1000)

            last_time = None
           # print("last time: {}".format(last_time))
           # print("cur time: {}".format(time.time()))
          #  print("start delay: {}".format(self.start_delay))
	    '''
            if self.top_frm.last_time:
                delta = time.time() - last_time
                delta_ms = delta * 1000
                if delta_ms < self.start_delay:
                    self.top_frm.last_time = self.top_frm.last_time + self.start_delay / 1000.0
                    print("update last time: {}".format(self.top_frm.last_time))
                    delay_time = (self.start_delay - delta_ms) / 1000.0
                    print("delay time: {} s".format(delay_time))
                    time.sleep(delay_time)

                else:
                    self.top_frm.last_time = time.time()
            else:
                self.last_time = time.time()

            print("last time: ", self.top_frm.last_time)
	    '''
            dr=self.memory_download.memory_download('D:\\ESP_NEW_TOOL\\new_factory_tools\\RF_test\\image\\ESP32_Module_Test_V128_40M_20170117_IC1229_test_init.bin')
            #self.memory_download.disconnect()
            #self.print_dbg("download disconnect...")
            if dr==True:
                return True
            else:
                self.window.STOP_FLG=1
                self.memory_download.stopFlg=1
                self.memory_download.disconnect()
                self.print_dbg("download disconnect...")
                return False
        else:
            self.print_dbg('Error when connect and sync...try again ')
            return False    
        
    def rpt_append(item,value):
        testitem_str=str_format(testitem[item])
        if(eval(value)>eval(item_thres_h_dict[testitem[item]])) or (eval(value)<eval(item_thres_l_dict[testitem[item]])):
            res='FAIL'
        else:
            res='PASS'
        value_str=value
        spec_l_str=str_format(item_thres_l_dict[testitem[item]])
        spelc_h_str=str_format(item_thres_h_dict[testitem[item]])
        res_str=str_format(res)
        
        tempstr=testitem_str+','+value_str+','+spec_l_str+','+spelc_h_str+','+res_str+'\n'
        
        self.rptstr=self.rptstr+tempstr
        return 0  
     
    def str_format(value):
      
        if(isinstance(value,str)):
            value=value
      
        else:
            value=str(value)
        re_filling=20
        fill_num=re_filling-len(value)
        re_fill_str=' '
        re_fill_str=re_fill_str*fill_num
        re_fill_str=value+re_fill_str
        
        return re_fill_str
    def esp_gen_rpt(self):
        tool_ver=self.tool_ver
        chip_type=self.chip_type
        fac_=self.fac_
        po=self.po
        mac=self.mac
        res=self.TOTAL_TEST_FLAG
        rptstr=self.rptstr
        _path='C:/ESP_REPORT'   
        timestr=time.strftime('%Y-%m-%d-%H-%M',time.localtime(time.time()))
        try:
            if(not os.path.exists(_path)):
                #os.makedirs('C:\\ESP_REPORT\\'+po+'__'+res+mac+timestr)
                os.makedirs(_path)
            os.chdir(_path)
            
            filename=po+'__'+res+mac+timestr+'.csv'
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
                
                with open(esp_logpath,'a') as fn:
                    fn.write(temp_str)
                print(log_str)
            elif(print_type==1):
                temp_str='[para_in]:'+log_str+'\r\n'
               
                with open(esp_logpath,'a') as fn:
                    fn.write(temp_str)
                print(log_str)
            elif(print_type==2):
                temp_str='[para_out]:'+log_str+'\r\n'
                
                with open(esp_logpath,'a') as fn:
                    fn.write(temp_str)
                print(log_str)
            elif(print_type==3):
                temp_str='[debug]:'+log_str+'\r\n'
                with open(esp_logpath,'a') as fn:
                    fn.write(temp_str)
                print(log_str)            
            
        except IOError:
            
            self.esp_logstr=self.esp_logstr+temp_str    
            
    def esp_gen_log(self):
	logpath='..//logs//'
	mac=self.memory_download.ESP_MAC_STA
	tool_ver=self.tool_ver
	chip_type=self.chip_type
	fac_=self.fac_
	timestr=time.strftime('%Y-%m-%d-%H-%M',time.localtime(time.time()))
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
	except:
	    logpath=''
	    return logpath
	return logpath
    
    def ui_print(self,log):
	self._stdout.write(log)
    
    def upload_server(self, rst):
	
	
	no_err      = "0x00" 
	err_params  = "0x01"
	err_conn    = "0x02"
	err_upload  = "0x03"
	err_other   = "0xff"

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
	           "chk_repeat_flg":"False", 
	           "po_type":"0"}

	uploader = Uploader(up_data)
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

	print (err_msg)
	if err_msg['err_code'] == '0x00':
	    self.ui_print('UPLOAD OK')
	else:
	    self.ui_print('[state]upload-f')
    
    def esp_write_flash(self):
	self.l_print(0,'ALL TEST PASS,WRITE PASS FLAG')
	cmdstr=self.time2cmdstr()
	print cmdstr
	try:
	    if(not self.ser.isOpen()):
		self.ser.open()
	    self.ser.write(cmdstr)
	except:
	    self.l_print(3,'write pass info nok')
	    self.ui_print('WRITE PASS INFO NOK')
	    self.STOPFLAG=1
	    self.resflag=0
	temp=self.ser.readline()
	if 'esp_set_fac_info_pass' in temp:
	    self.l_print(3,'write pass info ok')
	    self.ui_print('WRITE PASS INFO OK')
	else:
	    self.l_print(3,'write pass info nok')
	    self.ui_print('WRITE PASS INFO NOK')
	    self.STOPFLAG=1
	    self.resflag=0	    
    
    def reboot(self):
	pass
	#self.ser.write('')
	#if self.dutconfig['chip_conf']['freq'] == '26M':
	    #self.ser.baudrate = 74880
	
    
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
    
    def STOPTEST(self):
	if(self.isRunning()):
	    #print 'stop exe'
	    try:
		self.ser.close()
	    except:
		pass
	    if self.resflag == 0:
		self.upload_server('fail')
	    else:
		self.upload_server('success')
	    time.sleep(3)
	    self.ui_print('[state]finish')
	    self.ui_print('[state]idle')
	    self.terminate()
    
def fac_test(stdout_, dut_config, test_flow):
    if(0):
	stdout_.write('[state]run')
	if(dut_config['chip_conf']['chip_type'] == "ESP32"):
	    THRESHOLD_DICT=rl.get_threshold_dict('ATE','.//Threshold//full_Threshold_32.xlsx')
	else:
	    THRESHOLD_DICT=rl.get_threshold_dict('ATE','D:\\ESP_NEW_TOOL\\new_factory_tools\\RF_test\\Threshold\\full_Threshold_8266.xlsx')    
	
	try:
	    esp_process=esp_testThread(stdout_, dut_config,test_flow, THRESHOLD_DICT)
	    time.sleep(0.5)
	    esp_process.start()
	except:
	    pass 
	    

	    
#if __name__=='__main':
    