import json
import sys
import os
import esptool
import ConfigParser

DEBUG = 0

no_err      = "0x00" 
err_params  = "0x01"
err_dev     = "0x02"
err_conn    = "0x03"
err_load_flash = "0x04"
err_load_ram = "0x05"
err_read_mac = "0x06"
err_burn_mac = "0x07"
err_check_efuse = "0x08"
err_other   = "0xff"

class Downloader(object):
    chip_type = 'ESP32' #para_dict['CHIP_TYPE']
    port = ''
    port_baud = 115200
    compress = True
    no_stub = False
    verify = False
    
    flash_freq = '40m'  #para_dict['FLASH_FREQ']
    flash_mode = 'dio'  #para_dict['FLASH_MODE']
    flash_size = '4MB'  #para_dict['FLASH_SIZE']
    addr_filename = ''  #{(0x0, self.filename)}
    filename = ''    
    # operation=0 # 0:read mac, 1:load ram, 2:burn mac, 3:load to flash
    def __init__(self, conf):
        self.flash_freq = conf.get("flash_param", "flash_freq")
        self.flash_mode = conf.get("flash_param", "flash_mode")
        self.flash_size = conf.get("flash_param", "flash_size")
        self.addr_filename = tuple(eval(conf.get("flash_param", "addr_filename")))
        self.filename = self.addr_filename[0][1]
        
        self.chip_type = conf.get("dev_param", "chip_type")
        self.port = conf.get("dev_param", "port")
        self.port_baud = int(conf.get("dev_param", "port_baud"))
        self.compress = bool(conf.get("dev_param", "compress").lower()=='true')
        self.no_compress = bool(conf.get("dev_param", "compress").lower()!='true')
        self.no_stub = bool(conf.get("dev_param", "no_stub").lower()=='true') 
        self.verify = bool(conf.get("dev_param", "verify").lower()=='true')
        
    def connect(self):
        initial_baud = 115200
        if(self.chip_type == 'ESP32'):
            try:
                self.esp = esptool.ESP32ROM(params.port, initial_baud)
            except:
                if(DEBUG): print "ERROR!! The com port is occupied!!"
                return err_conn, "ERROR!! The com port is occupied!!"
        elif(self.chip_type == 'ESP8266'):
            try:
                self.esp = esptool.ESP8266ROM(self.port, initial_baud)
            except:
                if(DEBUG): print "ERROR!! The com port is occupied!!"
                return err_conn, "ERROR!! The com port is occupied!!"
        
        times = 5
        while True:
            try:
                if times-1>0:
                    self.esp.connect()
                else:
                    return err_conn, "ERROR!! sync to chip fail"
                break
            except:
                times -= 1
                pass
            
        if(DEBUG): print 'sync succ'
        return no_err, 'sync succ'
    
    def load_to_flash(self):
        try:
            if not params.no_stub:
                self.esp = self.esp.run_stub()
            self.esp.change_baud(921600)        
            #print "load flash ..." 
            esptool.write_flash(self.esp, self)
        except:
            if(DEBUG): print ('load bin fail')
            return err_load_flash, 'load bin fail'
    
    def get_mac(self):
        try:
            esp_mac = self.esp.get_mac()
            cus_mac = self.esp.get_cus_mac(2)
            return no_err, (esp_mac, cus_mac)
        except:
            return err_read_mac, 'read mac fail'
        
    def check_efuse(self):
        return True
    
    def load_to_ram(self):
        try:
            esptool.load_ram(self.esp, self)
            return no_err, ''
        except:
            return err_load_ram, "fail to load ram"
    
    def burn_mac_f(self, MAC_address):
        ser = self.esp.get_port()
        ser.flushInput()
        ser.flushOutput()
        cmd = "esp_set_mac 0x" + MAC_address[2:6] + ' 0x' + MAC_address[6:14] + '\r'
        if(DEBUG): print (cmd)
        ser.write(cmd)
    
        s1 = ser.read(64)
        if (s1.find("efuse") < 0) and (s1.find("mac") < 0):
            if(DEBUG): print "RETRY..."
            ser.flushInput()
            ser.flushOutput()    
            ser.write(cmd)
            s1 = ser.read(64)
            if (s1.find("efuse") < 0) and (s1.find("mac") < 0):
                return err_burn_mac, "burn mac fail"
        return no_err, s1
    
    def get_port(self):
        return self.esp.get_port()

def work_finish(ser, err_code, err_info):
    if ser != '':
        try:
            ser.close()
        except:
            pass
    err_msg = {
        "err_code" : err_code,
        "err_info" : err_info
    }
    print (err_msg)
    sys.exit(0)

def main():
    global DEBUG
    err_msg = {
        "err_code" : no_err,
        "err_info" : ''
    }
    try:
        params = sys.argv[1]
        if params.find("DEBUG") >= 0:
            DEBUG = 1
        if(DEBUG): print ("params:", params)
        params = json.loads(params)
        operation = int(params["operation"])
    except:
        work_finish('', err_params, "read params ERROR")
    
    try:
        conf = ConfigParser.ConfigParser()
        conf.read(params["config"])
    except:
        work_finish('', err_params, "read config file ERROR")
    
    downloader = Downloader(conf)
    err_msg["err_code"],err_msg["err_info"] = downloader.connect()
    if err_msg["err_code"] == no_err:
        if(DEBUG): print "sync succ"
    else:
        if(DEBUG): print "sync fail"
    
    if operation == 0:
        err_msg["err_code"],err_msg["err_info"] = downloader.get_mac()
    elif operation == 1:
        err_msg["err_code"],err_msg["err_info"] = downloader.load_to_ram()
    elif operation == 2:
        try:
            cus_mac = params["cus_mac"]
        except:
            work_finish(downloader.get_port(), err_params, "read mac ERROR")
        err_msg["err_code"],err_msg["err_info"] = downloader.burn_mac_f(cus_mac)
    elif operation == 3:
        err_msg["err_code"],err_msg["err_info"] = downloader.load_to_flash()
    elif operation == 4:
        pass
    
    work_finish(downloader.get_port(), err_msg["err_code"], err_msg["err_info"])
    return    

if __name__ == "__main__":
    main()

'''
params:
"{\"config\":\"config/setting.ini\", \"operation\":\"0\"}"

P.s , \"DEBUG\":\"1\"
'''