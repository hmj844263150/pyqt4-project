import json
import sys
import os
import esptool
import ConfigParser
import zlib
import time

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

def efuse_check_82(chip_type, reg0, reg1, reg2, reg3, mode = 1):
    EFUSE_ERR_FLG = 0x1
    EFUSE_WARNING_FLG = 0x2
    efuse_log = ""
    efuse_res = True
    error_flg = 0
    warning_flg = 0

    efuse = reg0 | (reg1<<32) | (reg2<<64) | (reg3<<96)
    
    if chip_type == "ESP8285":
        if ((efuse>>80)&0x1) ^ ((efuse>>4)&0x1):
            pass     # check bit80 or bit4 first. one of them should be 1 and the other should be 0
        else:
            return err_check_efuse, "8285 special efuse check fail" # if check false, it is not ESP8285    
    
    check_err_0 = (efuse>>76)&0xf    #0xa , 0xb
    check_err_1 = (efuse>>124)&0x3   #0x0
    check_err_2 = (efuse>>0)&0x3     #0x0
    check_err_3 = (efuse>>56)&0xf    #0x2
    check_err_4 = (efuse>>76)&0xf    #0x
    
    if not check_err_0 in [0xa,0xb]:
        efuse_log += ("bit[79:76] error")
        error_flg |= EFUSE_ERR_FLG
    if not check_err_1 == 0x0:
        efuse_log += ("bit[125:124] error")
        error_flg |= EFUSE_ERR_FLG
    if not check_err_2 == 0x0:
        efuse_log += ("bit[1:0] error")
        error_flg |= EFUSE_ERR_FLG
    if not check_err_3 == 0x2:
        efuse_log += ("bit[59:56] error")
        error_flg |= EFUSE_ERR_FLG

    if mode == 0:
        if check_err_4 == 0xb:  #48bit mac
            b0 = (reg0>>24)&0xff
            b1 = (reg1&0xff)
            b2 = (reg1>>8)&0xff
            b3 = (reg3&0xff)
            b4 = (reg3>>8)&0xff
            b5 = (reg3>>16)&0xff
            id0 = (reg0>>4)&0xff
            id1 = (reg0>>12)&0xff
            id2 = (reg0>>20)&0xf | (reg1>>12)&0xf0
            id3 = (reg1>>20)&0xf | (reg1>>24)&0xf0
            id4 = (reg2&0xff)
            id5 = (reg2>>8)&0xf  | (reg2>>12)&0xf0
            id6 = (reg2>>20)&0xff
            id7 = (reg2>>28)&0xf |(reg3>>20)&0xf0

            crc_efuse_4bit = ((reg0>>2)&0x03 ) | ((reg3>>28)&0x0c)
            crc_data = [b0,b1,b2,b3,b4,b5,id0,id1,id2,id3,id4,id5,id6,id7]
            crc_calc_4bit = crc.calcrc(crc_data) & 0xf
            efuse_log += ("crc_efuse_4bit: {}\n".format(crc_efuse_4bit))
            efuse_log += ("crc_calc_4bit: {}\n".format(crc_calc_4bit))
            if (not crc_efuse_4bit == crc_calc_4bit):
                efuse_log += ("efuse crc error\n")
                error_flg |= EFUSE_WARNING_FLG
        if error_flg == 0x0:
            efuse_log+="""EFUSE CHECK PASS...\r\n"""
            efuse_log+="""CUSTOMER ID:%02X %02X %02X %02X %02X %02X %02X %02X \r\n"""%(id7,id6,id5,id4,id3,id2,id1,id0)
        else:
            if error_flg & EFUSE_ERR_FLG:
                efuse_log+="""EFUSE VAL ERROR..."""
            if error_flg & EFUSE_WARNING_FLG:
                efuse_log+="""EFUSE CRC ERROR..."""

    elif mode == 1: #normal:
        if((reg3>>24)&0x1) == 1:
            efuse_log+="""EFUSE FOR CUSTOMER:\r\n"""
            if check_err_4 == 0xb:  #48bit mac
                b0 = (efuse>>80)&0xff
                b1 = (efuse>>68)&0xff
                b2 = (efuse>>60)&0xff
                mac_head_flg = (reg0>>6)&0x3
                if(mac_head_flg == 1):
                    b5 = 0x2c   #0x00101100
                    b4 = 0x3a   #0x00111010
                    b3 = 0xe8   #0x11101000
                elif(mac_head_flg == 2):
                    b5 = 0xa4   #0x10100100
                    b4 = 0x7b   #0x01111011
                    b3 = 0x9d   #0x10011101
                elif(mac_head_flg == 3):
                    b5 = 0x18   #0x00011000
                    b4 = 0xfe   #0x11111110
                    b3 = 0x34   #0x00110100
                else:
                    b5 = 0x00
                    b4 = 0x00
                    b3 = 0x00

                crc_efuse_4bit = ((reg0>>2)&0x03 ) | ((reg3>>28)&0x0c)
                crc_data = [b2,b1,b0]
                crc8_result = crc.esp_crc8(crc_data)
                crc8_mac_reg = (reg0>>8)&0xff
                if(crc8_result == crc8_mac_reg):
                    if(DEBUG): print("EFUSE CHECK PASS!")
                    return True
                else:
                    if(DEBUG): print("EFUSE CHECK FAIL!")
                    return False
        else:
            # if bit-120 is zero
            efuse_log += ("====================\n")
            efuse_log += ("EFUSE NORMAL MODE\n")
            efuse_log += ("====================\n")
            efuse_log+="""====================
                               \rEFUSE NORMAL MODE
                               \r====================\r\n"""
            if check_err_4 == 0xb: #48bit mac
                crc_cal_val = (efuse>>96)&0xffffff
                crc_data = [(crc_cal_val&0xff),(crc_cal_val>>8)&0xff,(crc_cal_val>>16)&0xff]
                crc_calc_res = crc.calcrc(crc_data) &0xff
                crc_efuse_val = (efuse>>88)&0xff
                efuse_log += ("=========================\n")
                efuse_log += ("CRC IN MODE 1: \n")
                efuse_log += ("crc_calc_res: {}\n".format(crc_calc_res))
                efuse_log += ("target crc val: {}\n".format(crc_efuse_val))
                efuse_log += ("=========================\n")
                if not crc_calc_res == crc_efuse_val:
                    efuse_log += ("bit[119:96] crc error\n")
                    error_flg |= EFUSE_WARNING_FLG

            if error_flg & EFUSE_ERR_FLG:
                efuse_log+="""EFUSE VAL ERROR...\r\n"""
            if error_flg & EFUSE_WARNING_FLG:
                efuse_log+="""EFUSE CRC ERROR...\r\n"""

            #--------------------------------------------
            #warning items for mode 1:
            #-----------------------
            crc_val = (efuse >> 24) & 0xffffffff
            crc_data =[(crc_val>>0)&0xff,(crc_val>>8)&0xff,(crc_val>>16)&0xff,(crc_val>>24)&0xff]
            crc_calc_res = crc.calcrc(crc_data) &0xff
            crc_efuse_val = (efuse>>16)&0xff
            efuse_log += ("=========================\n")
            efuse_log += ("CRC IN MODE 1:\n")
            efuse_log += ("crc_calc_res: {}\n".format(crc_calc_res))
            efuse_log += ("target crc val: {}\n".format(crc_efuse_val))
            efuse_log += ("=========================\n")
            if not crc_calc_res == crc_efuse_val:
                self.logger.warn("bit[47:24] crc warning\n")
                warning_flg = EFUSE_WARNING_FLG
            check_warn_0 = (efuse >> 126) & 0x3
            check_warn_2 = (efuse >> 80) & 0xff
            check_warn_3 = (efuse >> 60) & 0xffff
            check_warn_4 = (efuse >> 48) & 0xff
            check_warn_5 = (efuse >> 4) & 0xfff
            check_warn_6 = (efuse >> 2) & 0x3
            check_warn_7 = (efuse >> 88) & 0xffffffff

            if not (check_warn_0|check_warn_2|check_warn_3|check_warn_4|check_warn_5|check_warn_6)==0:
                efuse_log += ("efuse warning found...\n")
                warning_flg |= EFUSE_WARNING_FLG

            if check_err_4 == 0xa: #24bit mac
                if not check_warn_7 == 0:
                    efuse_log += ("efuse warning found!!!\n")
                    warning_flg |= EFUSE_WARNING_FLG
            if error_flg == 0x0 and warning_flg==0x0:
                efuse_log+="""EFUSE CHECK PASS..."""
            else:
                if warning_flg & EFUSE_ERR_FLG:
                    efuse_log+="""EFUSE VAL WARNING...\r\n"""
                if warning_flg & EFUSE_WARNING_FLG:
                    efuse_log+="""EFUSE CRC WARNING...\r\n"""

    if error_flg > 0 or warning_flg >0:
        return False, efuse_log
    else:
        return True, efuse_log

def load_ram(esp, args):
    if(esp.CHIP_NAME == 'ESP32'):
        image = esptool.LoadFirmwareImage("esp32", args.filename)
    else:
        image = esptool.LoadFirmwareImage("esp8266", args.filename)

    if(DEBUG): print('RAM boot...')
    for seg in image.segments:
        offset = seg.addr
        data = seg.data
        size = seg.file_offs

        if(DEBUG): print('Downloading %d bytes at %08x...' % (size, offset))
        sys.stdout.flush()
        esp.mem_begin(size, esptool.div_roundup(size, esp.ESP_RAM_BLOCK), esp.ESP_RAM_BLOCK, offset)

        seq = 0
        while len(data) > 0:
            esp.mem_block(data[0:esp.ESP_RAM_BLOCK], seq)
            data = data[esp.ESP_RAM_BLOCK:]
            seq += 1
        if(DEBUG): print('done!')

    if(DEBUG): print('All segments done, executing at %08x' % image.entrypoint)
    try:
        esp.mem_finish(image.entrypoint)
    except:
        #print "error but ignore"
        pass
    

def write_flash(esp, args):
    flash_params = esptool._get_flash_params(esp, args)

    if args.compress is None and not args.no_compress:
        args.compress = not args.no_stub

    # verify file sizes fit in flash
    flash_end = esptool.flash_size_bytes(args.flash_size)
    for address, argfile in args.addr_filename:
        argfile.seek(0,2)  # seek to end
        if address + argfile.tell() > flash_end:
            raise FatalError(("File %s (length %d) at offset %d will not fit in %d bytes of flash. " +
                             "Use --flash-size argument, or change flashing address.")
                             % (argfile.name, argfile.tell(), address, flash_end))
        argfile.seek(0)

    for address, argfile in args.addr_filename:
        if args.no_stub:
            if(DEBUG): print('Erasing flash...')
        image = esptool.pad_to(argfile.read(), 4)
        image = esptool._update_image_flash_params(esp, address, flash_params, image)
        calcmd5 = esptool.hashlib.md5(image).hexdigest()
        uncsize = len(image)
        if args.compress:
            uncimage = image
            image = zlib.compress(uncimage, 9)
            blocks = esp.flash_defl_begin(uncsize, len(image), address)
        else:
            blocks = esp.flash_begin(uncsize, address)
        argfile.seek(0)  # in case we need it again
        seq = 0
        written = 0
        t = time.time()
        while len(image) > 0:
            if(DEBUG): print('\rWriting at 0x%08x... (%d %%)' % (address + seq * esp.FLASH_WRITE_SIZE, 100 * (seq + 1) // blocks))
            sys.stdout.flush()
            block = image[0:esp.FLASH_WRITE_SIZE]
            if args.compress:
                esp.flash_defl_block(block, seq)
            else:
                # Pad the last block
                block = block + b'\xff' * (esp.FLASH_WRITE_SIZE - len(block))
                esp.flash_block(block, seq)
            image = image[esp.FLASH_WRITE_SIZE:]
            seq += 1
            written += len(block)
        t = time.time() - t
        speed_msg = ""
        if args.compress:
            if t > 0.0:
                speed_msg = " (effective %.1f kbit/s)" % (uncsize / t * 8 / 1000)
            if(DEBUG): print('\rWrote %d bytes (%d compressed) at 0x%08x in %.1f seconds%s...' % (uncsize, written, address, t, speed_msg))
        else:
            if t > 0.0:
                speed_msg = " (%.1f kbit/s)" % (written / t * 8 / 1000)
            if(DEBUG): print('\rWrote %d bytes at 0x%08x in %.1f seconds%s...' % (written, address, t, speed_msg))
        try:
            res = esp.flash_md5sum(address, uncsize)
            if res != calcmd5:
                if(DEBUG): print('File  md5: %s' % calcmd5)
                if(DEBUG): print('Flash md5: %s' % res)
                if(DEBUG): print('MD5 of 0xFF is %s' % (hashlib.md5(b'\xFF' * uncsize).hexdigest()))
                raise FatalError("MD5 of file does not match data in flash!")
            else:
                if(DEBUG): print('Hash of data verified.')
        except NotImplementedInROMError:
            pass
    if(DEBUG): print('\nLeaving...')

    if esp.IS_STUB:
        # skip sending flash_finish to ROM loader here,
        # as it causes the loader to exit and run user code
        esp.flash_begin(0, 0)
        if args.compress:
            esp.flash_defl_finish(False)
        else:
            esp.flash_finish(False)

    if args.verify:
        if(DEBUG): print('Verifying just-written flash...')
        if(DEBUG): print('(This option is deprecated, flash contents are now always read back after flashing.)')
        esptool._verify_flash(esp, args)

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
    # operation=0 # 0:read mac, 1:load ram, 2:burn mac, 3:load to flash, 4:efuse check
    def __init__(self, conf):
        self.flash_freq = conf.get("flash_param", "flash_freq")
        self.flash_mode = conf.get("flash_param", "flash_mode")
        self.flash_size = conf.get("flash_param", "flash_size")
        self.addr_filename = list(eval(conf.get("flash_param", "addr_filename")))
        self.filename = self.addr_filename[0][1]
        for i in range(len(self.addr_filename)):
            self.addr_filename[i] = list(self.addr_filename[i])
            self.addr_filename[i][1] = open(self.addr_filename[i][1], 'rb')
        
        self.chip_type = conf.get("dev_param", "chip_type")
        self.port = conf.get("dev_param", "port")
        self.port_baud = int(conf.get("dev_param", "port_baud"))
        self.compress = bool(conf.get("dev_param", "compress").lower()=='true')
        self.no_compress = bool(conf.get("dev_param", "compress").lower()!='true')
        self.no_stub = bool(conf.get("dev_param", "no_stub").lower()=='true') 
        self.verify = bool(conf.get("dev_param", "verify").lower()=='true')
        
    def connect(self):
        initial_baud = 115200 * 2
        if(self.chip_type == 'ESP32'):
            try:
                self.esp = esptool.ESP32ROM(self.port, initial_baud)
            except:
                if(DEBUG): print "ERROR!! The com port is occupied!!"
                return err_conn, "ERROR!! The com port is occupied!!"
        elif(self.chip_type == 'ESP8266'):
            try:
                self.esp = esptool.ESP8266ROM(self.port, initial_baud)
            except:
                if(DEBUG): print "ERROR!! The com port is occupied!!"
                return err_conn, "ERROR!! The com port is occupied!!"
        
        times = 3
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
            
        return no_err, 'sync succ'
    
    def load_to_flash(self):
        try:
            if not self.no_stub:
                self.esp = self.esp.run_stub()
            self.esp.change_baud(921600)        
            #print "load flash ..." 
            write_flash(self.esp, self)
        except:
            if(DEBUG): print ('load bin fail')
            return err_load_flash, 'load to flash fail'
        return no_err, "load to flash success"
    
    def get_mac(self):
        try:
            esp_mac = self.esp.get_mac()
            cus_mac = self.esp.get_cus_mac(2)
            return no_err, (esp_mac, cus_mac)
        except:
            return err_read_mac, 'read mac fail'
        
    def check_efuse(self):
        if self.chip_type in ("ESP8266","ESP8285"):
            try:
                reg0 = self.read_reg(0x3ff00050)
                reg1 = self.read_reg(0x3ff00054)
                reg2 = self.read_reg(0x3ff00058)
                reg3 = self.read_reg(0x3ff0005c)              
            except:
                return err_check_efuse, 'read efuse error'
            return efuse_check(self.chip_type, reg0, reg1, reg2, reg3)
        elif self.chip_type in ("ESP32"):
            return no_err, 'efuse check pass'
        else:
            return no_err, 'efuse check pass'
    
    def load_to_ram(self):
        try:
            load_ram(self.esp, self)
            return no_err, 'load to ram succ'
        except:
            return err_load_ram, "fail to load ram"
    
    def burn_mac_f(self, cus_mac):
        try:
            cus_mac = cus_mac.encode('utf8').lower()
        except:
            return err_burn_mac, "custom mac format error"
        if cus_mac.startswith('0x'):
            cus_mac = cus_mac[2:]
        if len(cus_mac) != 12:
            return err_burn_mac, "custom mac format error"
        ser = self.esp.get_port()
        ser.flushInput()
        ser.flushOutput()
        cmd = "esp_set_mac 0x" + cus_mac[0:4] + ' 0x' + cus_mac[4:12] + '\r'
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
        params = '{\"config\":\"config/setting.ini\", \"operation\":\"0\", \"cus_mac\":\"0x2c3ae808000f\", \"DEBUG\":\"1\"}'
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
            cus_mac = str(params["cus_mac"]).encode('utf8')
        except:
            work_finish(downloader.get_port(), err_params, "read mac ERROR")
        err_msg["err_code"],err_msg["err_info"] = downloader.load_to_ram()
        if err_msg["err_code"] == no_err:
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
operation:
0: read mac
1: load to ram
2: burn mac
3: load to flash 
4: check efuse

P.s , \"DEBUG\":\"1\"

result£º
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
'''