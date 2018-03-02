# -*- coding: utf-8-*- #
import esptool
import json
import os
import sys
import time
import serial
import serialCmd

import espefuse

defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)
    
DEBUG=0
class esp_fw_check:
    def __init__(self,port,baud,cmdEn,cmd,chiptype,targetStr,delaytime,timeout,fw_print_port,fw_baud):
        self.port=port
        self.baud=baud
        self.cmdEn=cmdEn
        self.cmd=cmd
        self.chiptype=chiptype
        self.targetStr=targetStr   
        self.delaytime=delaytime
        self.timeout=timeout
        self.fw_print_port=fw_print_port
        self.fw_baud=fw_baud
        self._port=serial.Serial(port=self.port, baudrate=self.baud)
        
       # self.esp=esptool.ESPLoader(port=self._port, baud=self.baud)
        self.esp=esptool.ESP8266ROM(port=self._port, baud=self.baud)
       # _slip_reader = esptool.slip_reader(self._port)
            
    def run_esp_firmware(self):
        if(self.chiptype=='ESP8266') or(self.chiptype=='ESP8089'):
            print ('run ESP8266 firmware')
        elif(self.chiptype=='ESP32'):
            print ("run ESP32 firmware")
        elif(self.chiptype=='ESP8285'):
            print ('run ESP8285 firmware')
       # self._port=serial.Serial(port=self.port, baudrate=self.baud)   
        #self.esp=esptool.ESP8266ROM(port=self._port, baud=self.baud)
        #ser = self._port
        #if(self.window.io_change_boot_mode_en == 1):
        if not self.esp._port.isOpen():
            self.esp._port.open()
        self.send_reboot_cmd() # run flash mode
        try:
            self.uart_connect_and_sync()
        except:
            pass
        self.esp.flash_begin(0, 0)
        self.esp.flash_finish(reboot=True)
            #pass
                
            
    def uart_connect_and_sync(self):
        connect_res = 1
        sync_res = 0
        com_port = self._port
        BR=self.baud
        sync_count=0
        while(sync_count<=4):
            
            sync_count+=1
            print("sync_count is : %d "%sync_count)
            time.sleep(0.3)      #delay to run uart_connect() again , if shorter than 0.2, fail to connect again
            
            if(sync_count>1):
                connect_res=self.com_connect(self.port,self.baud)
            
            if connect_res == 1:
                try:
                    #if(self.window.io_change_boot_mode_en == 1):
                    #self.memory_download.ESP_SET_BOOT_MODE(0) # boot mode
                    #time.sleep(1)
                        #pass
                    sync_res =  self.connect()
                except:
                    self.print_dbg("error when start sync again  =================")
                if sync_res == 1:
                    print("sync ok...")
                    break
                else:
                    print('sync error')
                    sync_res = 0
            else:
                sync_res=0
                break
        

        return sync_res    
    
    def com_connect(self, com_port = "COM6", baudrate = 115200):
        print "======\r\nCONNECT BAUD:",baudrate,"\r\n============"
       
        #self.esp = None
        #if self.esp == None:
         #   self.esp = self.rom(port=com_port, baud=self.ESP_ROM_BAUD)
        #else:
         #   self.esp._port.baudrate = baudrate
        if self.esp._port.isOpen():
            self.esp._port.flush()
            self.esp._port.flushInput()
            self.esp._port.close()
            
        if not self.esp._port.isOpen():
            self.esp._port.open()

        self._COM = self.port
        try:
            self.isRunning = True
            self.state = '0x3'
           # self.append_log("set state: ESP_DL_SYNC\n")
            #self.append_log("serial port opened\n")
            #self.append_log("-----------\n")
            #self.append_log("baud:"+str(self.ESP_ROM_BAUD))
            #self.append_log("\nroot baud:"+str(self.ESP_ROM_BAUD))
            #self.append_log("\n-------------\n")
            return True
        except:
            
            self.state = '0x2'
            
            return False    
    
    def connect(self):
        #self.print_dbg('Connecting...')
        #sys.stdout.flush()

        for _ in xrange(4):
            # issue reset-to-bootloader:
            # RTS = either CH_PD or nRESET (both active low = chip in reset)
            # DTR = GPIO0 (active low = boot to flasher)

            # worst-case latency timer should be 255ms (probably <20ms)
            self.esp._port.timeout = 0.2
            for _ in xrange(2):
                try:
                    self.esp._port.flushInput()
                    self.esp._slip_reader = esptool.slip_reader(self.esp._port)
                    self.esp._port.flushOutput()
                    self.esp.sync()
                    self.esp._port.timeout = 5
                    return 1
                except:
                    time.sleep(0.05)
                    sys.stdout.flush()
       # raise err_define.ChipSyncError(self.chip, self.esp_sync_blocking)
        
    
    def ESP_SET_BOOT_MODE(self, mode):
        #return
        if (mode == 0): #set boot mode
            if self._port.isOpen():
                flag = 0
            else:
                self._port.open()
                flag = 1

            self._port.setDTR(False)    #en=0, io=0
            self._port.setRTS(True)
            time.sleep(0.1)
            self._port.setDTR(True)     #en=1, io=0
            self._port.setRTS(False)
            time.sleep(0.05)
            #self.esp._port.setDTR(False)

            #self.esp._port.flushInput()
            #self.esp._port.flush()
            if flag == 1:
                self.esp._port.close()

        elif (mode == 1): #set run mode
            if self._port.isOpen():
                flag = 0
            else:
                self._port.open()
                flag = 1

            self._port.setDTR(False)    #en=0, io=0
            self._port.setRTS(True)
            time.sleep(0.1)
            self._port.setDTR(False)    #en=1, io=1
            self._port.setRTS(False)
            time.sleep(0.05)
            if flag == 1:
                self._port.close()
    def send_reboot_cmd(self):
        """
        Send reboot command to firmware to reboot and get back to rom mode.
        """
        #self.print_dbg("send cmd port: {}".format(self.COM_PORT))
        
        if not self._port.isOpen():
            self._port.open()
       
        self._port.flushInput
        self._port.write("esp_en_reboot\r")
        self._port.write("esp_en_reboot\r")        
            
    def testcheckfirmware(self):
        
        print '======================='
        print 'RUN FIRMWARE'
        print '======================='
        
        self.run_esp_firmware()
        time.sleep(self.delaytime/1000)
        
        print 'check module boot info'
        print 'Target check str is %s'%self.targetStr
        if(self.port==self.fw_print_port):
            res,data = serialCmd.uart_send_command(ser=self._port,cmd_str = "",
                                                                           pattern = self.targetStr,
                                                                           ser_tout = self.timeout,
                                                                           delay = 0,
                                                                           baud= self.fw_baud)   
        else:
            res,data = serialCmd.uart_send_command(ser=serial.Serial(port=self.fw_print_port,baudrate=self.baud),cmd_str = "",
                                                                                       pattern = self.targetStr,
                                                                                       ser_tout = self.timeout,
                                                                                       delay = 0,
                                                                                       baud= self.fw_baud)              
        
        print '**********************************************'
        if(res==True):
            self.fwcheckres=1
            print 'firmware check ok'
        else:
            print 'firmware check error'
            self.fwcheckres=0
        print '**********************************************'
        if(self.cmdEn):
            if(self.port==self.fw_print_port):
                res,data = serialCmd.uart_send_command(ser=self._port,cmd_str = self.cmd,
                                                                           pattern = self.targetStr,
                                                                           ser_tout = self.timeout,
                                                                           delay = 0,
                                                                           baud= self.fw_baud)   
            else:
                res,data = serialCmd.uart_send_command(s=serial.Serial(port=self.fw_print_port,baudrate=self.baud),cmd_str = self.cmd,
                                                      pattern = self.targetStr,
                                                      ser_tout = self.timeout,
                                                      delay = 0,
                                                      baud= self.fw_baud)    
            print 'cmd reslut is %s,%s'%(res,data)
            if(res==True):
                self.fwcheckres=1
                print 'firmware check ok'
            else:
                print 'firmware check error'
                self.fwcheckres=0
        self._port.close()       
        return self.fwcheckres

def run(port,baud,cmdEn,cmd,chiptype,targetStr,delaytime,timeout,fw_print_port,fw_baud):
    #params =sys.argv[1]
   # params = '{"port":"COM4","baudrate":"115200","cmdEn":"1","cmd":"AT+GMR","chip":"ESP8266","targetStr":"1.3.0.0","delaytime":"1000","timeout":"5000","DEBUG":"1","fw_print_port":"COM4"}'
  #  global DEBUG
   # params=json.loads(params)
   # DEBUG=int(params['DEBUG'])
    
   # params={'port':'COM4','baudrate':'921600','cmdEn':'0','cmd':'AT+GMR','chip':'ESP32','targetStr':'SDK version: v2.1.1','delaytime':'0','timeout':'5000'}
  #  print params
    port=port
    
    baud=baud
    
    
    cmdEn=cmdEn
    
    cmd=cmd
    chiptype=chiptype
    targetStr=targetStr
    
    delaytime=delaytime
    timeout=timeout
    fw_print_port=fw_print_port
    fw_baud=fw_baud
      
    print'Start to check firmware,make sure the comport has been closed'
    f=esp_fw_check(port, baud, cmdEn, cmd, chiptype, targetStr, delaytime, 
                  timeout,fw_print_port,fw_baud)
    
    check_res=f.testcheckfirmware()
    return check_res
if __name__=='__main__':
    run()