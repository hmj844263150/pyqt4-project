#!/usr/bin/env python
#
# ESP8266 & ESP32 ROM Bootloader Utility
# Copyright (C) 2014-2016 Fredrik Ahlberg, Angus Gratton, Espressif Systems (Shanghai) PTE LTD, other contributors as noted.
# https://github.com/espressif/esptool
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA 02110-1301 USA.


import sys
sys.path.append("./esptool")
import espefuse as espefuse
import esptool as esptool
import logging
import myLogger
import zlib
import sys
reload(sys)
sys.setdefaultencoding('gbk')
code_type = sys.getfilesystemencoding()

import sys
import struct
import serial
import math
import time
import shutil
import os
import json
import hashlib
#import argparse

import param_save_load
import crc
import err_define
import secure_burn
import wx


from abc import ABCMeta, abstractmethod
from value_dict import *

class Downloader(object):
    __metaclass__ = ABCMeta
    ESP_RAM_BLOCK = 0x1800
    def __init__(self, frame, port = "COM6", baudrate = 115200, name = '', chip = "ESP8266", sub_chip = '', num = 1):
        self.logger = myLogger.logger_init("ESP8266Loader_{name}[{num}]".format(name = name, num = num), chip, name)
        self.chip = chip
        self.sub_chip = sub_chip
        self.num = num
        self.parent = frame
        self.stopFlg=False
        self._port = None
        self._COM = port
        self.name = name
        self.ESP_ROM_BAUD = 115200
        self.isRunning =  False
        self.stopFlg = False
        self.state = self.ESP_DL_IDLE
        self.process_num = 0
        self.MAC = [0 for x in range(6)]
        self.frame = frame
        self.esp = None
        self.rom = esptool.ESP8266ROM
        self.ESP_UART0_BASE_REG = CHIP_REG_DICT["ESP_UART0_BASE_REG_%s"%self.chip]
        self.ESP_UART0_CLKDIV = self.ESP_UART0_BASE_REG + CHIP_REG_DICT["ESP_UART0_CLKDIV_OFFSET_%s"%self.chip]
        self.ESP_UART0_CLKDIV_CNT = CHIP_REG_DICT["ESP_UART0_CLKDIV_CNT_%s"%self.chip]
        self.ESP_UART0_CLKDIV_S = CHIP_REG_DICT["ESP_UART0_CLKDIV_S_%s"%self.chip]
        self.ESP_CMD_ADDR = CHIP_REG_DICT["ESP_CMD_ADDR_%s"%self.chip]
        self.ESP_CMD_RDID = CHIP_REG_DICT["ESP_CMD_RDID_%s"%self.chip]
        self.ESP_DATA_ADDR = CHIP_REG_DICT["ESP_DATA_ADDR_%s"%self.chip]

    def append_log(self,log):
        self.logger.debug("{log}".format(log = log))

    def esp_disp_secure_warning(self):
        return False

    """reset some status used"""
    def reset(self):
        self.isRunning =  False
        self.stopFlg = False
        self.state = self.ESP_DL_IDLE
        self.append_log("set state: ESP_DL_IDLE\n")
        self.process_num = 0

    """close com port"""
    def disconnect(self):
        if self.esp and self.esp._port and self.esp._port.isOpen():
            self.esp._port.close()
            self.append_log("com closed\n")
            self.isRunning = False
        else:
            self.append_log("already closed\n")

    """open RS232 port"""
    def com_connect(self, com_port = "COM6", baudrate = 115200):
        print "======\r\nCONNECT BAUD:",baudrate,"\r\n============"
        self.append_log(" CONNECT BAUD: %d\n"%baudrate)
        self.esp = None
        if self.esp == None:
            self.esp = self.rom(port=com_port, baud=self.ESP_ROM_BAUD)
        else:
            self.esp._port.baudrate = baudrate
        if self.esp._port.isOpen():
            self.esp._port.flush()
            self.esp._port.flushInput()
            self.esp._port.close()
            self.append_log("com port closed")
        if not self.esp._port.isOpen():
            self.esp._port.open()

        self._COM = com_port
        try:
            self.isRunning = True
            self.state = self.ESP_DL_SYNC
            self.append_log("set state: ESP_DL_SYNC\n")
            self.append_log("serial port opened\n")
            self.append_log("-----------\n")
            self.append_log("baud:"+str(self.ESP_ROM_BAUD))
            self.append_log("\nroot baud:"+str(self.ESP_ROM_BAUD))
            self.append_log("\n-------------\n")
            return True
        except:
            self.append_log("serial port open error\n")
            self.append_log("COM:"+str(self._COM) + "\n")
            self.append_log("PORT:"+str(com_port) + "\n")
            self.append_log("SERIAL PORT OPEN ERROR\n")
            self.state = self.ESP_DL_CONNECT_ERROR
            self.append_log("set state: ESP_DL_CONNECT_ERROR\n")
            return False

    def command_chg_baud(self, op=None, data=b"", chk=0, rd_baud = 115200, wait_response=True):
        if op is not None:
            pkt = struct.pack(b'<BBHI', 0x00, op, len(data), chk) + data
            self.esp.write(pkt)
        self.esp._port.flush()
        time.sleep(0.01)
        self.append_log("set rd_baud:%s\n"%str(rd_baud))
        self.esp._port.baudrate = rd_baud
        self.esp._port.flushInput()
        if not wait_response:
            return

        # tries to get a response until that response has the
        # same operation as the request or a retries limit has
        # exceeded. This is needed for some esp8266s that
        # reply with more sync responses than expected.
        for retry in range(100):
            p = self.esp.read()
            if len(p) < 8:
                continue
            (resp, op_ret, len_ret, val) = struct.unpack('<BBHI', p[:8])
            if resp != 1:
                continue
            data = p[8:]
            if op is None or op_ret == op:
                return val, data
        raise esptool.FatalError("Response doesn't match request")

    """ Write to memory address in target """
    def write_reg_chg_baud(self, addr, value, mask, delay_us=0,rd_baud = 115200):
        print "rd_baud:",rd_baud
        if self.command_chg_baud(self.esp.ESP_WRITE_REG,
                                 struct.pack('<IIII', addr, value, mask, delay_us+10000),rd_baud = rd_baud)[1] != "\0\0":
            raise esptool.FatalError('Failed to write target memory')

    #def ESP_SET_GPIO_MODE(self, mode):
        #if (mode == 0): #set boot mode
            #ser = serial.Serial('com11', 115200)
            #ser.setRTS(True)   #IO0=0
            #ser.setDTR(False)   #EN=0
            #time.sleep(0.2)
            #ser.setDTR(True)    #EN=1
            #ser.setRTS(False)    #IO0=1
            #time.sleep(0.2)
            #ser.setDTR(False)
            #ser.close()


    def ESP_SET_BOOT_MODE(self, mode):
        #return
        if (mode == 0): #set boot mode
            if self.esp._port.isOpen():
                flag = 0
            else:
                self.esp._port.open()
                flag = 1

            self.esp._port.setDTR(False)    #en=0, io=0
            self.esp._port.setRTS(True)
            time.sleep(0.1)
            self.esp._port.setDTR(True)     #en=1, io=0
            self.esp._port.setRTS(False)
            time.sleep(0.05)
            #self.esp._port.setDTR(False)

            #self.esp._port.flushInput()
            #self.esp._port.flush()
            if flag == 1:
                self.esp._port.close()

        elif (mode == 1): #set run mode
            if self.esp._port.isOpen():
                flag = 0
            else:
                self.esp._port.open()
                flag = 1

            self.esp._port.setDTR(False)    #en=0, io=0
            self.esp._port.setRTS(True)
            time.sleep(0.1)
            self.esp._port.setDTR(False)    #en=1, io=1
            self.esp._port.setRTS(False)
            time.sleep(0.05)
            if flag == 1:
                self.esp._port.close()

    """ Try connecting repeatedly until successful, or giving up """
    def device_connect(self, mode='default_reset'):
        """ Try connecting repeatedly until successful, or giving up """
        sys.stdout.flush()
        self.append_log("connecting...\n")
        last_error = None
        try:
            for _ in range(10):
                last_error = self.esp._connect_attempt(mode=mode, esp32r0_delay=False)
                if last_error is None:
                    return
                if self.stopFlg:
                    break
                last_error = self.esp._connect_attempt(mode=mode, esp32r0_delay=True)
                if last_error is None:
                    return
                if self.stopFlg:
                    break
        finally:
            pass
        raise esptool.FatalError('Failed to connect to %s: %s' % (self.chip, last_error))

    """ Try connecting repeatedly until successful, or giving up """
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
                    return
                except:
                    time.sleep(0.05)
                    sys.stdout.flush()
        raise err_define.ChipSyncError(self.chip, self.esp_sync_blocking)

    """synchronize baudrate"""
    def device_sync(self, mode="no_reset"):
        self.append_log("CALL DEVICE SYNC\n")
        if self.esp._port.isOpen()==False:
            self.append_log("Error : com not open")
            return False
        else:
            self.connect() #debug
            self.append_log("chip sync ok\n")
            #self.state = self.ESP_DL_SYNC
            return True

    def esp_flash_spi_param_set(self):
        if self.stopFlg:
            return
        try:
            self.append_log("SET FLASH PARAMS\n")
            result = self.esp.command(self.esp.ESP_SPI_SET_PARAMS,
                                  struct.pack('<IIIIII', 0, (128/8)*1024*1024, 64*1024,4*1024,256,0xffff))[1]
            if result != "\0\0":
                self.append_log("FAIL TO CONFIG FLASH\n")
                raise err_define.ChipFlashParamError(self.chip, self.esp_flash_spi_param_set)
        except:
            raise err_define.ChipFlashParamError(self.chip, self.esp_flash_spi_param_set)

    def esp_write_flash(self, esp, param):
        try:
            if self.stopFlg:
                return
            param.addr_filename = [((addr), open(filepath, 'rb')) for (filepath, addr) in self.dl_list]
            self.state = self.ESP_DL_DOWNLOADING
            self.write_flash(esp, param)
            self.state = self.ESP_DL_FINISH
            for _, file_handle in param.addr_filename:
                file_handle.close()
                del(file_handle)
        except:
            raise err_define.ChipFlashDownloadError(self.chip, self.esp_write_flash)

    def write_flash(self, loader, args):
        # set args.compress based on default behaviour:
        # -> if either --compress or --no-compress is set, honour that
        # -> otherwise, set --compress unless --no-stub is set
        if args.compress is None and not args.no_compress:
            args.compress = not args.no_stub
        self.total_len = 0
        if args.flash_size != "keep":
            # verify file sizes fit in flash
            flash_end = esptool.flash_size_bytes(args.flash_size)
        for address, argfile in args.addr_filename:
            argfile.seek(0,2)  # seek to end
            self.total_len += argfile.tell()
            if args.flash_size != "keep" and address + argfile.tell() > flash_end:
                raise esptool.FatalError(("File %s (length %d) at offset %d will not fit in %d bytes of flash. " +
                                 "Use --flash-size argument, or change flashing address.")
                                 % (argfile.name, argfile.tell(), address, flash_end))
            argfile.seek(0)

        for address, argfile in args.addr_filename:
            if args.no_stub:
                self.append_log('Erasing flash...')
            image = esptool.pad_to(argfile.read(), 4)
            image = esptool._update_image_flash_params(loader, address, args, image)
            calcmd5 = hashlib.md5(image).hexdigest()
            uncsize = len(image)
            if args.compress:
                uncimage = image
                image = zlib.compress(uncimage, 9)
                ratio = uncsize / len(image)
                blocks = loader.flash_defl_begin(uncsize, len(image), address)
            else:
                ratio = 1.0
                blocks = loader.flash_begin(uncsize, address)
            argfile.seek(0)  # in case we need it again
            seq = 0
            written = 0
            t = time.time()
            loader._port.timeout = min(esptool.DEFAULT_TIMEOUT * ratio,
                                    esptool.CHIP_ERASE_TIMEOUT * 2)
            while len(image) > 0:
                if self.stopFlg:
                    return
                self.logger.info('\rWriting at 0x%08x... (%d %%)' % (address + seq * loader.FLASH_WRITE_SIZE, 100 * (seq + 1) // blocks))
                sys.stdout.flush()
                block = image[0:loader.FLASH_WRITE_SIZE]
                if args.compress:
                    loader.flash_defl_block(block, seq)
                else:
                    # Pad the last block
                    block = block + b'\xff' * (loader.FLASH_WRITE_SIZE - len(block))
                    loader.flash_block(block, seq)
                image = image[loader.FLASH_WRITE_SIZE:]
                seq += 1
                written += len(block)
                self.process_num += len(block)
            t = time.time() - t
            speed_msg = ""
            if args.compress:
                if t > 0.0:
                    speed_msg = " (effective %.1f kbit/s)" % (uncsize / t * 8 / 1000)
                self.append_log('\rWrote %d bytes (%d compressed) at 0x%08x in %.1f seconds%s...' % (uncsize, written, address, t, speed_msg))
            else:
                if t > 0.0:
                    speed_msg = " (%.1f kbit/s)" % (written / t * 8 / 1000)
                self.append_log('\rWrote %d bytes at 0x%08x in %.1f seconds%s...' % (written, address, t, speed_msg))
            try:
                tout_ori = self.esp._port.timeout
                self.esp._port.timeout = 30
                res = loader.flash_md5sum(address, uncsize)
                self.esp._port.timeout = tout_ori
                if res != calcmd5:
                    self.append_log('File  md5: %s' % calcmd5)
                    self.append_log('Flash md5: %s' % res)
                    self.append_log('MD5 of 0xFF is %s' % (hashlib.md5(b'\xFF' * uncsize).hexdigest()))
                    raise esptool.FatalError("MD5 of file does not match data in flash!")
                else:
                    self.append_log('Hash of data verified.')
            except esptool.NotImplementedInROMError:
                pass
            loader._port.timeout = esptool.DEFAULT_TIMEOUT
        self.append_log('\nLeaving...')

    def esp_com_detect_blocking(self, initial_baud):
        while self.stopFlg == False:
            try:
                ret = self.com_connect(self._COM, initial_baud)
            except OSError:
                time.sleep(0.8)
                ret = False
            if ret:
                break

    def esp_sync_blocking(self, mode = "no_reset"):
        self.append_log("===============")
        self.append_log("BAUD : {}".format(self.ESP_ROM_BAUD))
        self.append_log("===============")
        while self.stopFlg == False:
            try:
                if self.device_sync(mode):
                    return True
            except IOError:
                self.logger.error("IOError: the serial port should probably be removed")
                raise err_define.ChipSyncError(self.chip, self.esp_sync_blocking)
            except esptool.FatalError, e:
                self.logger.error("Chip sync error: {}".format(e))
                raise err_define.ChipSyncError(self.chip, self.esp_sync_blocking)

    def flash_erase_test(self,com,baudrate,_dl_list,stub_mode = False,factory = False):
        try:
            self.flash_erase_func(com,baudrate,_dl_list,stub_mode,factory)
        except err_define.ChipSyncError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_SYNC_ERROR
        except err_define.ChipStubError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipHspiError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipEfuseCheckError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipFlashIDError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipFlashParamError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipFlashDownloadError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ReadMacRegError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ConfiguredSPICmdError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        finally:
            if self.isRunning:
                self.disconnect()
                pass
            if self.stopFlg:
                self.state = self.ESP_DL_STOP
                self.append_log("set state: ESP_DL_STOP\n")
            self.frame.running = False

    def flash_download_test(self,com,baudrate,_dl_list,stub_mode = False,factory = False):
        try:
            self.flash_download_func(com,baudrate,_dl_list,stub_mode,factory)
        except err_define.ChipSyncError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_SYNC_ERROR
        except err_define.ChipStubError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipHspiError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipEfuseCheckError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipFlashIDError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipFlashParamError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipFlashDownloadError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ChipEfuseDisRomConsoleError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ReadMacRegError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.ConfiguredSPICmdError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.BurnSecureBootKeyError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        except err_define.BurnFlashEncryptKeyError, e:
            self.logger.error(e)
            self.state = self.ESP_DL_DOWNLOAD_ERROR
        finally:
            if self.isRunning:
                self.disconnect()
            if self.stopFlg:
                self.state = self.ESP_DL_STOP
                self.append_log("set state: ESP_DL_STOP\n")
            if self.frame:
                self.frame.running = False

    def esp_clr_protect(self, stub):
        new_status   = param_save_load.conf_get_value("DOWNLOAD",     "new_status",   0x0,  int, self.chip, self.name)
        num_bytes    = param_save_load.conf_get_value("DOWNLOAD",      "num_bytes",   0x0,  int, self.chip, self.name)
        non_volatile = param_save_load.conf_get_value("DOWNLOAD",   "non_volatile", False, bool, self.chip, self.name)
        self.logger.debug("clear protect bits: val:{new_status};bnum:{num};nonvolatile:{nonvol};".format(new_status = new_status, num = num_bytes, nonvol=non_volatile))
        status = stub.read_status(3)
        self.logger.info("status[before]: {status}".format(status = hex(status)))
        if num_bytes > 0:
            stub.write_status(new_status=new_status, num_bytes=num_bytes, set_non_volatile=non_volatile)
            status = stub.read_status(3)
            self.logger.info("status[after]: {status}".format(status = hex(status)))

    def esp_flash_erase_and_clr_protect(self, loader):
        erase_en = param_save_load.conf_get_value("DOWNLOAD", "erase_flash_en", True, bool, self.chip, self.name)
        self.logger.debug("erase flash: erase_en:{en}".format(en=erase_en))
        self.esp_clr_protect(loader)
        loader.erase_flash()

    def esp_stub_and_set_baud(self, param, initial_baud):
        try:
            if not param.no_stub:
                stub = self.esp.run_stub()
            else:
                stub = self
            if self.fast_baud > initial_baud:
                if param.no_stub:
                    self.set_higher_baud(self.fast_baud)
                else:
                    try:
                        stub.change_baud(self.fast_baud)
                    except esptool.NotImplementedInROMError:
                        print("WARNING: ROM doesn't support changing baud rate. Keeping initial baud rate %d" % initial_baud)
            return stub
        except:
            raise err_define.ChipStubError(self.chip, self.esp_stub_and_set_baud)

    def esp_switch_hspi_mode(self):
        try:
            if "hspi" in self.name.lower() and self.stopFlg == False:
                self.hspi_init()
        except:
            raise err_define.ChipHspiError(self.chip, self.esp_switch_hspi_mode)

    def esp_check_mac_and_efuse(self):
        try:
            if self.stopFlg==False:
                ret = self.get_mac()
                print("ret: ", ret)
                if ret == False:
                    raise err_define.ChipEfuseCheckError(self.chip, self.esp_check_mac_and_efuse)
                self.append_log("get mac res: %d\n"%ret)
        except:
            raise err_define.ChipEfuseCheckError(self.chip, self.esp_check_mac_and_efuse)

    def esp_config_spi_mode(self):
        pass

    def flash_erase_func(self, port, baudrate, _dl_list, stub_mode = False, factory = False):
        self.ESP_MAC = ""
        self._COM=port
        self.fast_baud = baudrate
        self.total_len = 0
        self.process_num = 0
        self.dl_list = []+_dl_list

        param = MyParam(self.chip, self.name)
        initial_baud = min(self.ESP_ROM_BAUD, baudrate)
        ret = True
        if self.isRunning==True:
            self.disconnect()

        self.esp_com_detect_blocking(initial_baud)
        self.esp_sync_blocking(mode = param.before)
        esp = self.esp_stub_and_set_baud(param, initial_baud)
        self.esp_switch_hspi_mode()
        self.esp_config_spi_mode()
        if not factory:
            self.esp_check_mac_and_efuse()
            self.get_crystal()
            self.get_flash_id(esp)
        self.esp_flash_spi_param_set()
        self.state = self.ESP_DL_ERASE
        self.esp_flash_erase_and_clr_protect(esp)
        self.state = self.ESP_DL_FINISH

    def flash_download_func(self, com, baudrate, _dl_list, stub_mode = False, factory = False):
        self.ESP_MAC = ""
        self._COM=com
        self.fast_baud = baudrate
        self.total_len = 0
        self.process_num = 0
        self.dl_list = []+_dl_list

        param = MyParam(self.chip, self.name)
        initial_baud = min(self.ESP_ROM_BAUD, baudrate)
        ret = True
        if self.isRunning==True:
            self.disconnect()

        self.esp_com_detect_blocking(initial_baud)
        self.esp_sync_blocking(mode = param.before)
        self.esp_disable_rom_console()

        esp = self.esp_stub_and_set_baud(param, initial_baud)
        self.esp_switch_hspi_mode()
        self.esp_config_spi_mode()
        if not factory:
            self.esp_check_mac_and_efuse()
            self.get_crystal()
            self.get_flash_id(esp)

        self.esp_flash_spi_param_set()
        self.esp_write_flash(esp, param)

    """stop downloading"""
    def stop_download(self):
        self.stopFlg=True
        self.append_log("set STOP FLG: {}".format(self.stopFlg))

    def print_dbg(self,data):
        print("[%s][%s][sta%d]"%(self.chip, self.name, self.num) + str(data))

    #@stub_and_esp32_function_only
    def change_baud(self, baud):
        print("Changing baud rate to %d" % baud)
        self.esp.command(self.esp.ESP_CHANGE_BAUDRATE, struct.pack('<II', baud, 0))
        print("Changed.")
        self.esp._set_port_baudrate(baud)
        time.sleep(0.05)  # get rid of crap sent during baud rate change
        self.esp.flush_input()

    def memory_download(self,filename = ''):
        image = esptool.LoadFirmwareImage(self.chip.lower(), filename)
        self.print_dbg('RAM boot...{}'.format(filename))
        if not self.frame.sub_chip_type == "ESP8689":
            #self.esp.change_baud(460800)
            self.set_higher_baud(460800)
        try:
            for seg in image.segments:
                offset = seg.addr
                data = seg.data
                size = seg.file_offs
                self.print_dbg('Downloading %d bytes at %08x...' % (size, offset))
                self.esp.mem_begin(size, math.ceil(size / float(self.ESP_RAM_BLOCK)), self.ESP_RAM_BLOCK, offset)
                seq = 0
                total_seq = math.ceil(size / float(self.ESP_RAM_BLOCK))
                len_sector = len(data)
                while len(data) > 0:
                    self.esp.mem_block(data[0:self.ESP_RAM_BLOCK], seq)
                    data = data[self.ESP_RAM_BLOCK:]
                    seq += 1
                    try:
                        self.append_log("\r[esptool][sta_%d]:"%self.sta_num+" %07d / %07d"%(min(seq*self.ESP_RAM_BLOCK,len_sector),len_sector)),
                    except:
                        self.append_log("\r[%s][%s]: %07d / %07d"%(self.chip,self.name,min(seq*self.ESP_RAM_BLOCK,len_sector),len_sector)),

                    if self.stopFlg:
                        break
                self.append_log('done!')
                if self.stopFlg:
                    break
                else:
                    pass
        except:
            self.append_log("uart download error...,quit")
            return False

        self.append_log('All segments done, executing at %08x' % image.entrypoint)
        if self.stopFlg == 1:
            self.append_log("ram download stop")
        else:
            self.append_log("ram download finished")
            try:
                self.esp.mem_finish(image.entrypoint)
            except:
                self.append_log("exception in mem_finishe, but just ignore...")
            return True

    """write mac addr into a given addr of flash"""
    def id_bind(self,mac0,mac1,mac2,mac3,mac4,mac5,addr):
        pass

    @abstractmethod
    def hspi_init(self):
        raise err_define.NotImplementedFuncError(chip = self.chip, func = self.hspi_init)

    @abstractmethod
    def get_flash_id(self, esp = None):
        pass

    """get chip crystal"""
    @abstractmethod
    def get_crystal(self):
        pass

    @abstractmethod
    def efuse_check(self,reg0,reg1,reg2,reg3,mode=1):
        pass

    """read mac addr"""
    @abstractmethod
    def get_mac(self):
        pass

    @abstractmethod
    def set_mac(self,bit_flg):
        pass

    @abstractmethod
    def set_higher_baud(self, h_baud):
        raise err_define.NotImplementedFuncError(chip = self.chip, func = self.set_higher_baud)


class ESP8266Downloader(Downloader):
    #download state
    ESP_DL_OK = 0x0
    ESP_DL_IDLE = 0x1
    ESP_DL_CONNECT_ERROR = 0x2
    ESP_DL_SYNC = 0x3
    ESP_DL_SYNC_ERROR = 0x4
    ESP_DL_ERASE = 0x5
    ESP_DL_ERASE_ERROR = 0x6
    ESP_DL_DOWNLOADING = 0x7
    ESP_DL_DOWNLOAD_ERROR = 0x8
    ESP_DL_FAIL = 0x9
    ESP_DL_FINISH = 0xA
    ESP_DL_STOP = 0xB
    ESP_DL_EFUSE_ERROR = 0xC
    ESP_ROM_CLK_FREQ = 26000000*2

    def __init__(self, frame, port="COM6", baudrate=115200, name='',
                chip="ESP8266", sub_chip='', num=1, crystal='26m'):
        self.EFUSE_ERR_FLG = 0x1
        self.EFUSE_WARNING_FLG = 0x2
        self.chip = chip
        self.name = name
        self.CUSTOM_ID = ""
        self.efuse_mode = param_save_load.conf_get_value(section = "EFUSE CHECK", option = "efuse_mode", default = 1, value_type = int, chip = self.chip, name = self.name)
        self.efuse_err_halt = param_save_load.conf_get_value(section = "EFUSE CHECK", option = "efuse_err_halt", default = 1, value_type = int, chip = self.chip, name = self.name)

        self.flash_manufacturer_id=-1
        self.flash_device_id=-1
        self.crystal_freq = -1
        super(ESP8266Downloader, self).__init__(frame=frame, port=port, baudrate=baudrate, name=name, chip=chip, sub_chip=sub_chip, num=num)

    def hspi_init(self):
        self.write_reg(addr = 0x60000804, value = 0x20, mask = 0x130, delay_us=10)
        self.write_reg(addr = 0x60000808, value = 0x20, mask = 0x130, delay_us=10)
        self.write_reg(addr = 0x6000080c, value = 0x20, mask = 0x130, delay_us=10)
        self.write_reg(addr = 0x60000810, value = 0x20, mask = 0x130, delay_us=10)
        self.write_reg(addr = 0x3ff00028, value = 0x2, mask = 0x2, delay_us=10)
        self.write_reg(addr = 0x60000800, value = 0x0, mask = 0x300, delay_us=10)

    def get_flash_id(self, esp = None):
        #try:
            #if self.stopFlg:
                #return True
            #if esp and not esp.IS_STUB:
                #self.flash_spi_attach_req(0,0)
                #esp.flash_begin(0,0)
            #flash_id = esp.flash_id()
            #self.append_log("get flash id : 0x%08x"%flash_id)
            #self.flash_manufacturer_id = flash_id&0xff
            #self.flash_device_id = ((flash_id>>16)&0xff | (flash_id &( 0xff<<8)))
            #self.append_log("manufacturer_id: 0x%x\r\n"%self.flash_manufacturer_id)
            #self.append_log("device_id: 0x%x\r\n"%self.flash_device_id)
            #return True
        #except:
            #raise err_define.ChipFlashIDError(self.chip, self.get_flash_id)
        try:
        #if True:
            if self.sub_chip == "ESP32D2WD" or self.sub_chip.find('ESP32-PICO') >=0:
                self.esp_config_spi_mode()
            elif self.chip == "ESP32":
                self.flash_spi_attach_req(ucIsHspi=0,ucIsLegacy=0)
            esp.flash_begin(0,0)
            esp.write_reg(self.ESP_DATA_ADDR, 0 , 0 , 0 )
            time.sleep(0.01)
            esp.write_reg(self.ESP_CMD_ADDR , self.ESP_CMD_RDID , self.ESP_CMD_RDID , 0 )
            time.sleep(0.01)
            flash_id = esp.read_reg(self.ESP_DATA_ADDR)
            print "get flash id : 0x%08x"%flash_id
            self.flash_manufacturer_id = flash_id&0xff
            self.flash_device_id = ((flash_id>>16)&0xff | (flash_id &( 0xff<<8)))
            print " manufacturer_id: 0x%x\r\n"%self.flash_manufacturer_id
            print " device_id: 0x%x\r\n"%self.flash_device_id
            return True
        except:
            print "get flash id error"
            self.state = self.ESP_DL_DOWNLOAD_ERROR
            self.flash_manufacturer_id = 0
            self.flash_device_id = 0
            return False


    def get_crystal(self):
        """run before stub"""
        try:
            if self.stopFlg:
                return
            uart_reg = self.esp.read_reg(self.ESP_UART0_CLKDIV)
            uart_reg = (uart_reg >> self.ESP_UART0_CLKDIV_S) & self.ESP_UART0_CLKDIV_CNT
            self.crystal_freq = self.esp._port.baudrate * uart_reg / 2
            return True
        except:
            self.logger.error("Read crystal")
            self.crystal_freq = 0
            return True

    def efuse_specific_check(self, efuse):
        return True

    def efuse_check(self, reg0, reg1, reg2, reg3, mode = 1):
        EFUSE_ERR_FLG = 0x1
        EFUSE_WARNING_FLG = 0x2
        self.efuse_log = ""
        self.efuse_res = True
        error_flg = 0
        warning_flg = 0

        efuse = reg0 | (reg1<<32) | (reg2<<64) | (reg3<<96)
        self.efuse = efuse
        #==========================
        #error check:
        #------------
        check_err_0 = (efuse>>76)&0xf    #0xa , 0xb
        check_err_1 = (efuse>>124)&0x3   #0x0
        check_err_2 = (efuse>>0)&0x3     #0x0
        check_err_3 = (efuse>>56)&0xf    #0x2
        check_err_4 = (efuse>>76)&0xf    #0xb
        self.append_log("check_err_0: %02x"%check_err_0)
        self.append_log("check_err_1: %02x"%check_err_1)
        self.append_log("check_err_2: %02x"%check_err_2)
        self.append_log("check_err_3: %02x"%check_err_3)
        self.append_log("check_err_4: %02x"%check_err_4)
        self.efuse_log+="""======================
    \rEFUSE LOG:
    \r---------------
    \rREG0:%08X
    \rREG1:%08X
    \rREG2:%08x
    \rREG3:%08X
    \r----------------
    \r"""%(reg0,reg1,reg2,reg3)
        if mode == 1: # normal
            if not check_err_0 in [0xa,0xb]:
                self.append_log("bit[79:76] error")
                error_flg |= EFUSE_ERR_FLG
        if not check_err_1 == 0x0:
            self.append_log("bit[125:124] error")
            error_flg |= EFUSE_ERR_FLG
        if not check_err_2 == 0x0:
            self.append_log("bit[1:0] error")
            error_flg |= EFUSE_ERR_FLG
        if not check_err_3 == 0x2:
            self.append_log("bit[59:56] error")
            error_flg |= EFUSE_ERR_FLG

        b0 = (reg0>>24)&0xff
        b1 = (reg1&0xff)
        b2 = (reg1>>8)&0xff
        b3 = (reg3&0xff)
        b4 = (reg3>>8)&0xff
        b5 = (reg3>>16)&0xff
        self.MAC = [b5, b4, b3, b2, b1, b0]

        if mode == 0: # for xiaomi
            self.efuse_log+="""EFUSE FOR CUSTOMER(XM):\r\n"""
            id0 = (reg0>>4)&0xff
            id1 = (reg0>>12)&0xff
            id2 = (reg0>>20)&0xf | (reg1>>12)&0xf0
            id3 = (reg1>>20)&0xf | (reg1>>24)&0xf0
            id4 = (reg2&0xff)
            id5 = (reg2>>8)&0xf  | (reg2>>12)&0xf0
            id6 = (reg2>>20)&0xff
            id7 = (reg2>>28)&0xf |(reg3>>20)&0xf0
            self.ID0,self.ID1,self.ID2,self.ID3,self.ID4,self.ID5,self.ID6,self.ID7 = [id7,id6,id5,id4,id3,id2,id1,id0]
            self.CUSTOM_ID = "%02X%02X%02X%02X%02X%02X%02X%02X"%(id7,id6,id5,id4,id3,id2,id1,id0)

            if (efuse>>78)&0x1 == 0:  # old xiaomi efuse
                crc_efuse_4bit = ((reg0>>2)&0x03 ) | ((reg3>>28)&0x0c)
                crc_data = [b0,b1,b2,b3,b4,b5,id0,id1,id2,id3,id4,id5,id6,id7]
                #print "crc_data is", crc_data
                crc_calc_4bit = crc.calcrc(crc_data) & 0xf
                #print "==============================="
                #print "crc_efuse_4bit:",crc_efuse_4bit
                #print "crc_calc_4bit:",crc_calc_4bit
                #print "==============================="
                if (not crc_efuse_4bit == crc_calc_4bit):
                    print("efuse crc error")
                    error_flg |= 0x2
            else:  # new xiaomi efuse
                zero_num = 112
                self.print_dbg("efuse %x" %efuse)
                crc_mid = (efuse>>96) & 0xfffffff # in case the system is 32 bit
                zero_num = crc.calc_0_num(crc_mid, zero_num)

                crc_mid = (efuse>>80) & 0xffff # in case the system is 32 bit
                zero_num = crc.calc_0_num(crc_mid, zero_num)

                crc_mid = (efuse>>60) & 0xffff # in case the system is 32 bit
                zero_num = crc.calc_0_num(crc_mid, zero_num)

                crc_mid = (efuse>>32) & 0xffffff # in case the system is 32 bit
                zero_num = crc.calc_0_num(crc_mid, zero_num)

                crc_mid = (efuse>>4) & 0xfffffff # in case the system is 32 bit
                zero_num = crc.calc_0_num(crc_mid, zero_num)

                zero_num = zero_num & (0x7f)
                crc_efuse_7bit = ((reg0>>2)&0x03 ) | ((reg3>>28)&0x0c) | ((reg2>>8)&0x30) | ((reg2>>9)&0x40)
                #             bit[1:0] zero[1:0]  bit[127:126] zero[3:2]  bit[77:76] zero[5:4]  bit79 zero[6]
                #print "crc_read_4bit:",crc_read_4bit
                if(not crc_efuse_7bit == zero_num):
                    print("EFUSE CRC FAIL")
                    error_flg |= 0x2

            if error_flg == 0x0:
                self.efuse_log+="""EFUSE CHECK PASS...\r\n"""
                #self.efuse_log+="""XMID:%02X %02X %02X %02X %02X %02X %02X %02X \r\n"""%(id7,id6,id5,id4,id3,id2,id1,id0)

            else:
                if error_flg&0x1 == 1:
                    self.efuse_log+="""EFUSE VAL ERROR..."""
                if error_flg&0x2 == 0x2:
                    self.efuse_log+="""EFUSE CRC ERROR..."""


        elif mode == 1: # normal:
            if((reg3>>24)&0x1) == 1:
                self.efuse_log+="""EFUSE WITH CUSTOM MAC:\r\n"""
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

                    self.MAC = [b5, b4, b3, b2, b1, b0]
                    crc_efuse_4bit = ((reg0>>2)&0x03 ) | ((reg3>>28)&0x0c)
                    crc_data = [b2,b1,b0]
                    crc8_result = crc.esp_crc8(crc_data)
                    crc8_mac_reg = (reg0>>8)&0xff
                    if(crc8_result == crc8_mac_reg):
                        print("EFUSE CHECK PASS!")
                        return True
                    else:
                        print("EFUSE CHECK FAIL!")
                        return False

            else:
                # if bit-120 is zero
                self.append_log("====================\n")
                self.append_log("EFUSE NORMAL MODE\n")
                self.append_log("====================\n")
                self.efuse_log+="""====================
                                   \rEFUSE NORMAL MODE
                                   \r====================\r\n"""
                if check_err_4 == 0xb: #48bit mac
                    crc_cal_val = (efuse>>96)&0xffffff
                    crc_data = [(crc_cal_val&0xff),(crc_cal_val>>8)&0xff,(crc_cal_val>>16)&0xff]
                    crc_calc_res = crc.calcrc(crc_data) &0xff
                    crc_efuse_val = (efuse>>88)&0xff
                    self.append_log("=========================\n")
                    self.append_log("CRC IN MODE 1: \n")
                    self.append_log("crc_calc_res: {}\n".format(crc_calc_res))
                    self.append_log("target crc val: {}\n".format(crc_efuse_val))
                    self.append_log("=========================\n")
                    if not crc_calc_res == crc_efuse_val:
                        self.append_log("bit[119:96] crc error\n")
                        error_flg |= self.EFUSE_WARNING_FLG

                if error_flg & self.EFUSE_ERR_FLG:
                    self.efuse_log+="""EFUSE VAL ERROR...\r\n"""
                if error_flg & self.EFUSE_WARNING_FLG:
                    self.efuse_log+="""EFUSE CRC ERROR...\r\n"""

                #--------------------------------------------
                #warning items for mode 1:
                #-----------------------
                crc_val = (efuse >> 24) & 0xffffffff
                crc_data =[(crc_val>>0)&0xff,(crc_val>>8)&0xff,(crc_val>>16)&0xff,(crc_val>>24)&0xff]
                crc_calc_res = crc.calcrc(crc_data) &0xff
                crc_efuse_val = (efuse>>16)&0xff
                self.append_log("=========================\n")
                self.append_log("CRC IN MODE 1:\n")
                self.append_log("crc_calc_res: {}\n".format(crc_calc_res))
                self.append_log("target crc val: {}\n".format(crc_efuse_val))
                self.append_log("=========================\n")
                if not crc_calc_res == crc_efuse_val:
                    self.logger.warn("bit[47:24] crc warning\n")
                    warning_flg = self.EFUSE_WARNING_FLG
                check_warn_0 = (efuse >> 126) & 0x3
                check_warn_2 = (efuse >> 80) & 0xff
                check_warn_3 = (efuse >> 60) & 0xffff
                check_warn_4 = (efuse >> 48) & 0xff
                check_warn_5 = (efuse >> 4) & 0xfff
                check_warn_6 = (efuse >> 2) & 0x3
                check_warn_7 = (efuse >> 88) & 0xffffffff

                if not (check_warn_0|check_warn_2|check_warn_3|check_warn_4|check_warn_5|check_warn_6)==0:
                    self.append_log("efuse warning found...\n")
                    warning_flg |= self.EFUSE_WARNING_FLG

                if check_err_4 == 0xa: #24bit mac
                    if not check_warn_7 == 0:
                        self.append_log("efuse warning found!!!\n")
                        warning_flg |= self.EFUSE_WARNING_FLG
                if error_flg == 0x0 and warning_flg==0x0:
                    self.efuse_log+="""EFUSE CHECK PASS..."""
                else:
                    if warning_flg & self.EFUSE_ERR_FLG:
                        self.efuse_log+="""EFUSE VAL WARNING...\r\n"""
                    if warning_flg & self.EFUSE_WARNING_FLG:
                        self.efuse_log+="""EFUSE CRC WARNING...\r\n"""

        self.append_log("==================\n")
        self.append_log("EFUSE LOG:\n")
        self.append_log(self.efuse_log)

        if error_flg > 0 or warning_flg >0:
            return False
        else:
            return self.efuse_specific_check(efuse)
        
    def esp_getmac(self,ser):
        if not ser.isOpen():
            ser.open()
            
        retry_times=3
        cal_crc=False
        cmd='esp_read_efuse_128bit\r'
        ser.write(cmd)
        #self.esp._port.write(cmd)
        
        try:
            temp=ser.read(128)
            if temp is not '':
                temp_list=temp.split(':')[-1]
                reg_list=temp_list.split(',')
                reg0=int(reg_list[0],16)
                reg1=int(reg_list[1],16)
                reg2=int(reg_list[2],16)
                reg3=int(reg_list[3],16)
            else:
                return False
        except:
            print "read reg error"
            self.append_log("read reg error\n")
            self.state = self.ESP_DL_DOWNLOAD_ERROR   
            return False
        
        efuse_check_res = self.efuse_check(reg0, reg1, reg2, reg3, self.efuse_mode)#normal mode
    
        if efuse_check_res == False and self.efuse_err_halt == 1:
            self.state = self.ESP_DL_EFUSE_ERROR
            self.append_log("set state: ESP_DL_EFUSE_ERROR\n")
            return False
            #====================================
            #efuse_reg     = (reg3 << 96) | (reg2 << 64) | (reg1 << 32) | reg0
        efuse_flg     = (self.efuse >> 79) & 0x1
        chip_flg      = (self.efuse >> 77) & 0x7
        bit_flg       = (self.efuse >> 76) & 0x1
        self.BIT_FLG  = bit_flg
        self.CHIP_FLG = chip_flg
        self.MAC_FLG = 0
        return self.set_mac(self.BIT_FLG)    
        
    def get_mac(self):
        retry_times = 3
        cal_crc = False
        try:
            reg0 = self.esp.read_reg(0x3ff00050)
            reg1 = self.esp.read_reg(0x3ff00054)
            reg2 = self.esp.read_reg(0x3ff00058)
            reg3 = self.esp.read_reg(0x3ff0005c)
            self.append_log("0x3ff00050: %08x\n"%reg0)
            self.append_log("0x3ff00054: %08x\n"%reg1)
            self.append_log("0x3ff00058: %08x\n"%reg2)
            self.append_log("0x3ff0005c: %08x\n"%reg3)
        except:
            print "read reg error"
            self.append_log("read reg error\n")
            self.state = self.ESP_DL_DOWNLOAD_ERROR
            raise err_define.ReadMacRegError(chip = self.chip, func = self.get_mac)

        #print "EFUSE MODE :",self.efuse_mode
        efuse_check_res = self.efuse_check(reg0, reg1, reg2, reg3, self.efuse_mode)#normal mode

        if efuse_check_res == False and self.efuse_err_halt == 1:
            self.state = self.ESP_DL_EFUSE_ERROR
            self.append_log("set state: ESP_DL_EFUSE_ERROR\n")
            return -1
        #====================================
        #efuse_reg     = (reg3 << 96) | (reg2 << 64) | (reg1 << 32) | reg0
        efuse_flg     = (self.efuse >> 79) & 0x1
        chip_flg      = (self.efuse >> 77) & 0x7
        bit_flg       = (self.efuse >> 76) & 0x1
        self.BIT_FLG  = bit_flg
        self.CHIP_FLG = chip_flg
        self.MAC_FLG = 0
        return self.set_mac(self.BIT_FLG)

    def set_mac(self, bit_flg):
        if bit_flg == 0:
            if self.MAC_FLG ==0:
                mac_ap = ("1A-FE-34-%02x-%02x-%02x"%(self.MAC[3],self.MAC[4],self.MAC[5])).upper()
                mac_sta = ("18-FE-34-%02x-%02x-%02x"%(self.MAC[3],self.MAC[4],self.MAC[5])).upper()
                self.append_log("AP: {}\n".format(mac_ap))
                self.append_log("STA: {}\n".format(mac_sta))
            elif self.MAC_FLG == 1:
                mac_ap = ("AC-D0-74-%02x-%02x-%02x"%(self.MAC[3],self.MAC[4],self.MAC[5])).upper()
                mac_sta = ("AC-D0-74-%02x-%02x-%02x"%(self.MAC[3],self.MAC[4],self.MAC[5])).upper()
                self.append_log("AP: {}\n".format(mac_ap))
                self.append_log("STA: {}\n".format(mac_sta))
            else:
                self.logger.error("mac read error...\n")
                self.logger.error("mac_flg: {}".format(self.MAC_FLG))
                return False
        else:
            print "48bit mac"
            mac_sta = ("%02X-%02X-%02X-%02X-%02X-%02X"%(self.MAC[0],self.MAC[1],self.MAC[2],self.MAC[3],self.MAC[4],self.MAC[5])).upper()
            mac_0_tmp = self.MAC[0] & 0x7
            if mac_0_tmp == 0:
                mac_0_tmp = 0x2
            elif mac_0_tmp==2:
                mac_0_tmp = 0x6
            elif mac_0_tmp == 4:
                mac_0_tmp = 0x6
            elif mac_0_tmp==6:
                mac_0_tmp=0x2
            mac_ap ="%02X-%02X-%02X-%02X-%02X-%02X"%((self.MAC[0]&0xf8)|mac_0_tmp,self.MAC[1],self.MAC[2],self.MAC[3],self.MAC[4],self.MAC[5])
        self.append_log('MAC AP : %s\n'%mac_ap)
        self.append_log('MAC STA: %s\n'%mac_sta)
        self.ESP_MAC_AP = mac_ap
        self.ESP_MAC_STA = mac_sta
        self.ESP_MAC = mac_sta
        return True

    def set_higher_baud(self, h_baud):
        baud_prev = self.esp._port.baudrate
        val = self.esp.read_reg(0x60000014)
        baud = h_baud
        val = self.esp.read_reg(0x60000014)
        self.logger.debug("chip baud div: {}\n".format(val))
        self.logger.debug("chip baud: {}\n".format(26000000 * 2 / val))
        self.logger.debug("set div!!!: {}\n".format(26000000 * 2 / baud))
        self.write_reg_chg_baud(addr=0x60000014, value = 26000000*2/baud, mask=0xfffffff,delay_us=10000,rd_baud = (26000000*2)/(26000000*2/baud))#baud)
        self.esp._port.baudrate = baud
        self.esp._port.flushInput()
        self.esp._port.flush()
        self.esp._port.close()
        self.esp._port.open()
        return True

    def esp_check_mac_and_efuse(self):
        try:
            if self.stopFlg:
                return
            ret = self.get_mac()
            self.append_log("get mac res: %d\n"%ret)
            if ret == False and self.efuse_err_halt:
                raise err_define.ChipEfuseCheckError(self.chip, self.esp_check_mac_and_efuse)
            else:
                ret = True
        except:
            raise err_define.ChipEfuseCheckError(self.chip, self.esp_check_mac_and_efuse)

    def esp_disable_rom_console(self):
        return True

class ESP8285Downloader(ESP8266Downloader):
    def __init__(self, frame, port="COM6", baudrate=115200, name='',
                chip="ESP8266", sub_chip='', num=1,crystal='26m'):
        super(ESP8285Downloader, self).__init__(frame=frame, port=port, baudrate=baudrate, name=name, chip=chip, sub_chip=sub_chip, num=num)
        self.chip = chip
        self.name = name
        self.efuse_mode = param_save_load.conf_get_value(section = "EFUSE CHECK", option = "efuse_mode", default = 1, value_type = int, chip = self.chip, name = self.name)
        self.efuse_err_halt = param_save_load.conf_get_value(section = "EFUSE CHECK", option = "efuse_err_halt", default = 1, value_type = int, chip = self.chip, name = self.name)

    # efuse check for ESP8285
    # There is one bit in EFUSE that shows whether the chip is ESP8266 or ESP8285. it is bit80 or bit4
    def efuse_check(self, reg0, reg1, reg2, reg3, mode = 1):
        self.efuse_log = ""
        self.efuse_res = True
        error_flg = 0
        warning_flg = 0

        efuse = reg0 | (reg1<<32) | (reg2<<64) | (reg3<<96)
        self.efuse = efuse
        if ((efuse>>80)&0x1) ^ ((efuse>>4)&0x1):
            pass     # check bit80 or bit4 first. one of them should be 1 and the other should be 0
        else:
            return False # if check false, it is not ESP8285

        # the following are almost the same to ESP8266
        #==========================
        #error check:
        #------------
        check_err_0 = (efuse>>76)&0xf    #0xa , 0xb
        check_err_1 = (efuse>>124)&0x3   #0x0
        check_err_2 = (efuse>>0)&0x3     #0x0
        check_err_3 = (efuse>>56)&0xf    #0x2
        check_err_4 = (efuse>>76)&0xf    #0xb
        self.append_log("check_err_0: %02x"%check_err_0)
        self.append_log("check_err_1: %02x"%check_err_1)
        self.append_log("check_err_2: %02x"%check_err_2)
        self.append_log("check_err_3: %02x"%check_err_3)
        self.append_log("check_err_4: %02x"%check_err_4)
        self.efuse_log+="""======================
    \rEFUSE LOG:
    \r---------------
    \rREG0:%08X
    \rREG1:%08X
    \rREG2:%08x
    \rREG3:%08X
    \r----------------
    \r"""%(reg0,reg1,reg2,reg3)
        if not check_err_0 in [0xa,0xb]:
            self.append_log("bit[79:76] error")
            error_flg |= EFUSE_ERR_FLG
        if not check_err_1 == 0x0:
            self.append_log("bit[125:124] error")
            error_flg |= EFUSE_ERR_FLG
        if not check_err_2 == 0x0:
            self.append_log("bit[1:0] error")
            error_flg |= EFUSE_ERR_FLG
        if not check_err_3 == 0x2:
            self.append_log("bit[59:56] error")
            error_flg |= EFUSE_ERR_FLG

        b0 = (reg0>>24)&0xff
        b1 = (reg1&0xff)
        b2 = (reg1>>8)&0xff
        b3 = (reg3&0xff)
        b4 = (reg3>>8)&0xff
        b5 = (reg3>>16)&0xff
        self.MAC = [b5, b4, b3, b2, b1, b0]
        #print "efuse is %32x" %efuse
        if mode == 0:
            self.efuse_log+="""EFUSE FOR CUSTOMER:\r\n"""
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
                self.append_log("===============================\n")
                self.append_log("crc_efuse_4bit: {}\n".format(crc_efuse_4bit))
                self.append("crc_calc_4bit: {}\n".format(crc_calc_4bit))
                self.append_log("===============================\n")
                if (not crc_efuse_4bit == crc_calc_4bit):
                    self.append_log("efuse crc error\n")
                    error_flg |= self.EFUSE_WARNING_FLG
            if error_flg == 0x0:
                self.efuse_log+="""EFUSE CHECK PASS...\r\n"""
                self.efuse_log+="""CUSTOMER ID:%02X %02X %02X %02X %02X %02X %02X %02X \r\n"""%(id7,id6,id5,id4,id3,id2,id1,id0)
            else:
                if error_flg & self.EFUSE_ERR_FLG:
                    self.efuse_log+="""EFUSE VAL ERROR..."""
                if error_flg & self.EFUSE_WARNING_FLG:
                    self.efuse_log+="""EFUSE CRC ERROR..."""

        elif mode == 1: #normal:
            if((reg3>>24)&0x1) == 1:
                self.efuse_log+="""EFUSE FOR CUSTOMER:\r\n"""
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
                        print("EFUSE CHECK PASS!")
                        return True
                    else:
                        print("EFUSE CHECK FAIL!")
                        return False

            else:
                # if bit-120 is zero
                self.append_log("====================\n")
                self.append_log("EFUSE NORMAL MODE\n")
                self.append_log("====================\n")
                self.efuse_log+="""====================
                                   \rEFUSE NORMAL MODE
                                   \r====================\r\n"""
                if check_err_4 == 0xb: #48bit mac
                    crc_cal_val = (efuse>>96)&0xffffff
                    crc_data = [(crc_cal_val&0xff),(crc_cal_val>>8)&0xff,(crc_cal_val>>16)&0xff]
                    crc_calc_res = crc.calcrc(crc_data) &0xff
                    crc_efuse_val = (efuse>>88)&0xff
                    self.append_log("=========================\n")
                    self.append_log("CRC IN MODE 1: \n")
                    self.append_log("crc_calc_res: {}\n".format(crc_calc_res))
                    self.append_log("target crc val: {}\n".format(crc_efuse_val))
                    self.append_log("=========================\n")
                    if not crc_calc_res == crc_efuse_val:
                        self.append_log("bit[119:96] crc error\n")
                        error_flg |= self.EFUSE_WARNING_FLG

                if error_flg & self.EFUSE_ERR_FLG:
                    self.efuse_log+="""EFUSE VAL ERROR...\r\n"""
                if error_flg & self.EFUSE_WARNING_FLG:
                    self.efuse_log+="""EFUSE CRC ERROR...\r\n"""

                #--------------------------------------------
                #warning items for mode 1:
                #-----------------------
                crc_val = (efuse >> 24) & 0xffffffff
                crc_data =[(crc_val>>0)&0xff,(crc_val>>8)&0xff,(crc_val>>16)&0xff,(crc_val>>24)&0xff]
                crc_calc_res = crc.calcrc(crc_data) &0xff
                crc_efuse_val = (efuse>>16)&0xff
                self.append_log("=========================\n")
                self.append_log("CRC IN MODE 1:\n")
                self.append_log("crc_calc_res: {}\n".format(crc_calc_res))
                self.append_log("target crc val: {}".format(crc_efuse_val))
                self.append_log("=========================\n")
                if not crc_calc_res == crc_efuse_val:
                    self.logger.warn("bit[47:24] crc warning\n")
                    warning_flg = self.EFUSE_WARNING_FLG
                check_warn_0 = (efuse >> 126) & 0x3
                check_warn_2 = (efuse >> 80) & 0xfe     # already checked bit80, no need to check again
                check_warn_3 = (efuse >> 60) & 0xffff
                check_warn_4 = (efuse >> 48) & 0xff
                check_warn_5 = (efuse >> 4) & 0xffe     # already checked bit4, no need to check again
                check_warn_6 = (efuse >> 2) & 0x3
                check_warn_7 = (efuse >> 88) & 0xffffffff

                if not (check_warn_0|check_warn_2|check_warn_3|check_warn_4|check_warn_5|check_warn_6)==0:
                    self.append_log("efuse warning found...\n")
                    warning_flg |= self.EFUSE_WARNING_FLG

                if check_err_4 == 0xa: #24bit mac
                    if not check_warn_7 == 0:
                        self.append_log("efuse warning found!!!\n")
                        warning_flg |= self.EFUSE_WARNING_FLG
                if error_flg == 0x0 and warning_flg==0x0:
                    self.efuse_log+="""EFUSE CHECK PASS..."""
                else:
                    if warning_flg & self.EFUSE_ERR_FLG:
                        self.efuse_log+="""EFUSE VAL WARNING...\r\n"""
                    if warning_flg & self.EFUSE_WARNING_FLG:
                        self.efuse_log+="""EFUSE CRC WARNING...\r\n"""

        self.append_log("==================\n")
        self.append_log("EFUSE LOG:\n")
        self.append_log(self.efuse_log)

        if error_flg > 0 or warning_flg >0:
            return False
        else:
            return self.efuse_specific_check(efuse)


    def efuse_specific_check(self, efuse):
        if (efuse >> 80) & 0x1 or (efuse >> 4) & 0x1:
            return True
        else:
            self.logger.error("ESP8285 CHIP FLG ERROR\n")
            return False

class ESP32Downloader(ESP8266Downloader):
    def __init__(self, frame, port = "COM6", baudrate = 115200, name = '',
                 chip = "ESP32", sub_chip='', num = 1):
        super(ESP8266Downloader, self).__init__(frame=frame, port=port, baudrate=baudrate, name=name, chip=chip, sub_chip=sub_chip, num=num)
        self.rom = esptool.ESP32ROM
        self.chip = chip
        self.name = name

        self.debug_mode = param_save_load.conf_get_value(section = "DEBUG MODE", option = "debug_enable", default = True, value_type = bool, chip = self.chip, name = "security")
        self.debug_pem_path = param_save_load.conf_get_value(section = "DEBUG MODE", option = "debug_pem_path", default = "", value_type = str, chip = self.chip, name = "security")

        self.secure_boot_en = param_save_load.conf_get_value(section = "SECURE BOOT", option = "secure_boot_en", default = False, value_type = bool, chip = self.chip, name = "security")
        self.burn_secure_boot_key = param_save_load.conf_get_value(section = "SECURE BOOT", option = "burn_secure_boot_key", default = False, value_type = bool, chip = self.chip, name = "security")
        self.secure_boot_force_write = param_save_load.conf_get_value(section = "SECURE BOOT", option = "secure_boot_force_write", default = False, value_type = bool, chip = self.chip, name = "security")
        self.secure_boot_rw_protect = param_save_load.conf_get_value(section = "SECURE BOOT", option = "secure_boot_rw_protect", default = False, value_type = bool, chip = self.chip, name = "security")

        self.flash_encryption_en = param_save_load.conf_get_value(section = "FLASH ENCRYPTION", option = "flash_encryption_en", default = False, value_type = bool, chip = self.chip, name = "security")
        self.burn_flash_encryption_key = param_save_load.conf_get_value(section = "FLASH ENCRYPTION", option = "burn_flash_encryption_key", default = False, value_type = bool, chip = self.chip, name = "security")
        self.flash_encrypt_force_write = param_save_load.conf_get_value(section = "FLASH ENCRYPTION", option = "flash_encrypt_force_write", default = False, value_type = bool, chip = self.chip, name = "security")
        self.flash_encrypt_rw_protect = param_save_load.conf_get_value(section = "FLASH ENCRYPTION", option = "flash_encrypt_rw_protect", default = False, value_type = bool, chip = self.chip, name = "security")

        self.aes_en = param_save_load.conf_get_value(section = "AES KEY", option = "aes_key_en", default = False, value_type = bool, chip = self.chip, name = "security")
        self.burn_aes_key = param_save_load.conf_get_value(section = "AES KEY", option = "burn_aes_key", default = False, value_type = bool, chip = self.chip, name = "security")

        self.jtag_disable       = param_save_load.conf_get_value(section = "DISABLE FUNC", option = "jtag_disable", default = False, value_type = bool, chip = self.chip, name = "security")
        self.dl_encrypt_disable = param_save_load.conf_get_value(section = "DISABLE FUNC", option = "dl_encrypt_disable", default = False, value_type = bool, chip = self.chip, name = "security")
        self.dl_decrypt_disable = param_save_load.conf_get_value(section = "DISABLE FUNC", option = "dl_decrypt_disable", default = False, value_type = bool, chip = self.chip, name = "security")
        self.dl_cache_disable   = param_save_load.conf_get_value(section = "DISABLE FUNC", option = "dl_cache_disable", default = False, value_type = bool, chip = self.chip, name = "security")

        self.efuse_mode = param_save_load.conf_get_value(section = "EFUSE CHECK", option = "efuse_mode", default = 1, value_type = int, chip = self.chip, name = self.name)
        self.efuse_err_halt = param_save_load.conf_get_value(section = "EFUSE CHECK", option = "efuse_err_halt", default = 1, value_type = int, chip = self.chip, name = self.name)

    def esp_disp_secure_warning(self):
        if ((self.secure_boot_en and self.burn_secure_boot_key)
            or (self.flash_encryption_en and self.burn_flash_encryption_key)
            ) and self.num == 1:
            warning = """Some of secure boot and flash encryption function are enabled, efuse will be burned, Please make sure this is what you want!!!\n"""

            warning += "\nsecurity debug mode      : {}\n".format(self.debug_mode)
            if self.debug_mode:
                warning += "secure debug pem       : {}\n".format(self.debug_pem_path)
            warning += "\nsecure boot en         : {}\n".format(self.secure_boot_en)
            warning += "secure boot burn key   : {}\n".format(self.burn_secure_boot_key)
            warning += "secure boot force write: {}\n".format(self.secure_boot_force_write)
            warning += "secure boot rw disable : {}\n\n".format(self.secure_boot_rw_protect)

            warning += "flash encryption en         : {}\n".format(self.flash_encryption_en)
            warning += "flash encryption burn key   : {}\n".format(self.burn_flash_encryption_key)
            warning += "flash encryption force write: {}\n".format(self.flash_encrypt_force_write)
            warning += "flash encryption rw protect : {}\n\n".format(self.flash_encrypt_rw_protect)

            warning += "disable dl decrypt : {}\n".format(self.dl_decrypt_disable)
            warning += "disable dl encrypt : {}\n".format(self.dl_encrypt_disable)
            warning += "disable dl cache   : {}\n".format(self.dl_cache_disable)
            warning += "disable JTAG       : {}\n\n".format(self.jtag_disable)

            retCode = wx.MessageBox(warning, "ESP32 SECURITY FEATURES ENABLE",
                                    wx.OK | wx.ICON_WARNING)
            return True

    def esp_disable_rom_console(self):
        self.logger.info("Disabling the rom console...")
        try:
            if self.stopFlg:
                return
            class BurnEfuseParam(object):
                def __init__(self, efuse_name, new_value):
                    self.efuse_name = efuse_name
                    self.new_value = new_value
                    self.do_not_confirm = True
            efuse_args = BurnEfuseParam(efuse_name = "CONSOLE_DEBUG_DISABLE", new_value = 1)
            efuses = [ espefuse.EfuseField.from_tuple(self.esp, efuse) for efuse in espefuse.EFUSES ]
            espefuse.burn_efuse(self.esp, efuses, efuse_args)
        except:
            raise err_define.ChipEfuseDisRomConsoleError(chip = self.chip, func = self.esp_disable_rom_console)


    def hspi_init(self):
        print"=========================="
        print "ESP32 - SET HSPI MATRIX"
        print "========================="
        self.write_reg(0x60008474,0xfc,0xffffffff)#hold spi sig output
        #hspi gpio init
        val=self.read_reg(addr=0X60009030)
        self.write_reg(addr=0X60009030, value=((2<<12)|val), mask=0XFFFFFFFF)
        val=self.read_reg(addr=0X60009034)
        self.write_reg(addr=0X60009034, value=((2<<12)|val), mask=0XFFFFFFFF)
        val=self.read_reg(addr=0X60009038)
        self.write_reg(addr=0X60009038, value=((2<<12)|val), mask=0XFFFFFFFF)
        val=self.read_reg(addr=0X6000903c)
        self.write_reg(addr=0X6000903c, value=((2<<12)|val), mask=0XFFFFFFFF)
        val=self.read_reg(addr=0X60009040)
        self.write_reg(addr=0X60009040, value=((0x1<<8)|(2<<12)|val), mask=0XFFFFFFFF)
        val=self.read_reg(addr=0X60009048)
        self.write_reg(addr=0X60009048, value=((0x1<<8)|(2<<12)|val), mask=0XFFFFFFFF)
        #gpio enable
        val=self.read_reg(addr=0X60004020)
        self.write_reg(addr=0X60004020, value=(0xf014|val), mask=0XFFFFFFFF)
        #gpio out enable
        self.write_reg(addr=0X600041a4, value=((5<<24)|(0<<16)|(2<<8)|(1<<0)), mask=0XFFFFFFFF)
        self.write_reg(addr=0X6000419c, value=(3<<0), mask=0XFFFFFFFF)
        self.write_reg(addr=0X60004198, value=(4<<16), mask=0XFFFFFFFF)
        #gpio input enable
        self.write_reg(addr=0X600041c0, value=0x3f, mask=0XFFFFFFFF)
        self.write_reg(addr=0X60004130, value=((2<<24)|(4<<18)|(13<<12)|(12<<6)|(14<<0)), mask=0XFFFFFFFF)
        self.write_reg(addr=0X60004134, value=(15<<0), mask=0XFFFFFFFF)

    def efuse_check(self, reg0, reg1, reg2, reg3, reg4, reg5, reg6, mode=1):
        efuse = reg0 | (reg1<<32) | (reg2<<64) | (reg3<<96) | (reg4<<128) | (reg5<<160) | (reg6<<192)
        self.efuse = efuse
        
        flg_res = 0

        flg_32pad = (reg3>>2) & 0x1
        flg_ECO   = (reg3>>15)& 0x1
        flg_vers  = (reg3>>9) & 0x7
        flg_disable_app_cpu = (reg3) & 0x1

        if not self.sub_chip == '':
            if flg_32pad == 1:
                if self.sub_chip.find('ESP8689') < 0:
                    print "CHIP SELECT ERROR"
                    return False
            #elif flg_ECO == 1:
                #if not self.sub_chip == 'ESP32D0WDQ6E':
                    #print 'CHIP SELECT ERROR'
                    #return False
            elif flg_vers == 0:
                if self.sub_chip.find('ESP32D0WDQ6') < 0:
                    print 'CHIP SELECT ERROR'
                    return False
            elif flg_vers == 1:
                if self.sub_chip.find('ESP32D0WD') < 0:
                    print 'CHIP SELECT ERROR'
                    return False
            elif flg_vers == 2:
                if self.sub_chip.find('ESP32D2WD') < 0:
                    print 'CHIP SELECT ERROR'
                    return False
            elif flg_vers == 3:
                if self.sub_chip.find('ESP32D2WDXM') < 0:
                    print 'CHIP SELECT ERROR'
                    return False
            elif flg_vers == 4:
                if self.sub_chip.find('ESP32-PICO-D2') < 0:
                    print 'CHIP SELECT ERROR'
                    return False
            elif flg_vers == 5:
                if self.sub_chip.find('ESP32-PICO-D4') < 0:
                    print 'CHIP SELECT ERROR'
                    return False
            elif flg_vers == 6:
                if self.sub_chip.find('ESP32-PICO-D4XM') < 0:
                    print 'CHIP SELECT ERROR'
                    return False
                
            if flg_disable_app_cpu == 1:
                if self.sub_chip.find('ESP32S0WD') <0 :
                    print 'CHIP SELECT ERROR'
                    return False                    

        if not self.sub_chip == '':
            if self.sub_chip.endswith('E'):
                if flg_ECO == 1:
                    print "CHIP SELECT ERROR"
                    return False
                    # could be an error and return false


        read_mac=((reg2&0xffff)<<32)|reg1
        self.MAC = [(read_mac>>40)&0xff, (read_mac>>32)&0xff, (read_mac>>24)&0xff,
                    (read_mac>>16)&0xff, (read_mac>>8)&0xff,  (read_mac>>0)&0xff ]
        mac_tmp = self.MAC
        #mac_tmp.reverse()
        crc_cal = crc.calcrc(mac_tmp)
        crc_read = (reg2>>16)&0xff
        self.append_log("crc_cal: {}\n".format(crc_cal))
        self.append_log("crc_read: {}\n".format(crc_read))
        if crc_read == crc_cal :
            self.append_log("ESP32 MAC CRC OK\n")
            self.efuse_log = "ESP32 MAC CRC OK\n"
        else:
            self.append_log("ESP32 MAC CRC FAIL\n")
            self.efuse_log = "ESP32 MAC CRC FAIL, EFUSE ERROR!\n"
            flg_res = 1
            
        byte = []
        for i in xrange(28):
            byte.append(efuse >> (i*8) & 0xff )
        
        self.append_log("ESP32 bit check result:\n")
        if (byte[12]>>2 & 0x3) != 0:
            self.append_log("bit error:B12[2-3]\n")
            self.efuse_log = "bit error:B12[2-3]\n"            
            flg_res = 1
        if (byte[17]>>5 & 0x7) != 0:
            self.append_log("bit error:B17[5-7]\n")
            self.efuse_log = "bit error:B17[5-7]\n"            
            flg_res = 1
        if (byte[18]>>0 & 0x1) != 0:
            self.append_log("bit error:B18[0]]\n")
            self.efuse_log = "bit error:B18[0]\n"            
            flg_res = 1
        if (byte[24]>>3 & 0x1) != 0:
            self.append_log("bit error:B24[3]\n")
            self.efuse_log = "bit error:B24[3]\n"            
            flg_res = 1
            
        if flg_res:
            self.append_log("ESP32 EFUSE CHECK ERROR!!!\n")
            self.efuse_log = "ESP32 EFUSE CHECK ERROR!!!\n"
            return False
        
        self.append_log("ESP32 EFUSE CHECK OK\n")
        self.efuse_log = "ESP32 EFUSE CHECK OK\n"        
        return True

    def get_mac(self):
        EFUSE_BLK0_RDATA0=0x6001a000
        EFUSE_BLK0_RDATA1=0x6001a004
        EFUSE_BLK0_RDATA2=0x6001a008
        EFUSE_BLK0_RDATA3=0x6001a00C
        EFUSE_BLK0_RDATA4=0x6001a010
        EFUSE_BLK0_RDATA5=0x6001a014
        EFUSE_BLK0_RDATA6=0x6001a018#

        try:
            reg_b0_0 = self.esp.read_reg(EFUSE_BLK0_RDATA0)
            reg_b0_1 = self.esp.read_reg(EFUSE_BLK0_RDATA1)
            reg_b0_2 = self.esp.read_reg(EFUSE_BLK0_RDATA2)
            reg_b0_3 = self.esp.read_reg(EFUSE_BLK0_RDATA3)
            reg_b0_4 = self.esp.read_reg(EFUSE_BLK0_RDATA4)
            reg_b0_5 = self.esp.read_reg(EFUSE_BLK0_RDATA5)
            reg_b0_6 = self.esp.read_reg(EFUSE_BLK0_RDATA6)
        except:
            print "read reg error"
            self.append_log("read reg error\n")
            self.state = self.ESP_DL_DOWNLOAD_ERROR
            raise err_define.ReadMacRegError(chip=self.chip, func=self.get_mac)

        efuse_check_res = self.efuse_check(reg_b0_0, reg_b0_1, reg_b0_2, reg_b0_3, reg_b0_4, reg_b0_5, reg_b0_6, self.efuse_mode)

        if efuse_check_res == False and self.efuse_err_halt == 1:
            self.state = self.ESP_DL_EFUSE_ERROR
            self.append_log("set state: ESP_DL_EFUSE_ERROR\n")
            return False

        self.ESP_MAC_AP = "%02X%02X%02X%02X%02X%02X"%(self.MAC[0],self.MAC[1],self.MAC[2],self.MAC[3],self.MAC[4],self.MAC[5]+1)
        self.ESP_MAC_STA = "%02X%02X%02X%02X%02X%02X"%(self.MAC[0],self.MAC[1],self.MAC[2],self.MAC[3],self.MAC[4],self.MAC[5])
        self.ESP_MAC = self.ESP_MAC_STA
        self.ESP_MAC_BT = "%02X%02X%02X%02X%02X%02X"%(self.MAC[0],self.MAC[1],self.MAC[2],self.MAC[3],self.MAC[4],self.MAC[5]+2)
        self.ESP_MAC_ETNET = "%02X%02X%02X%02X%02X%02X"%(self.MAC[0],self.MAC[1],self.MAC[2],self.MAC[3],self.MAC[4],self.MAC[5]+3)
        return True

    def set_higher_baud(self,h_baud):
        self.change_baud(h_baud)
        return True

    def get_crystal(self):
        if self.stopFlg:
            return
        try:
            uart_reg = self.esp.read_reg(self.ESP_UART0_CLKDIV)
            uart_reg = (uart_reg>>self.ESP_UART0_CLKDIV_S) & self.ESP_UART0_CLKDIV_CNT
            self.crystal_freq = self.esp._port.baudrate * uart_reg
            return True
        except:
            print "error: read crystal"
            self.crystal_freq = 0
            return True

    def esp_burn_security_key(self, esp):
        secure_key = None
        flash_key = None
        aes_key = None
        if self.secure_boot_en and self.burn_secure_boot_key:
            secure_key = self.boot_key_path
        if self.flash_encryption_en and self.flash_key_path and self.burn_flash_encryption_key:
            flash_key = self.flash_key_path
        if self.aes_en:
            pass

        secure_burn.burn_security_key(esp = esp, downloader = self, secure_boot_key = secure_key,
                                      flash_encrypt_key = flash_key, aes_key = aes_key, logger = self.logger,
                                      secure_boot_force_write=self.secure_boot_force_write, secure_boot_no_protect= not self.secure_boot_rw_protect,
                                      flash_encrypt_force_write=self.flash_encrypt_force_write, flash_encrypt_no_protect= not self.flash_encrypt_rw_protect)
        if self.secure_boot_en or self.flash_encryption_en:
            secure_burn.efuse_disable_functions(esp = esp, logger = self.logger, jtag_disable = self.jtag_disable,
                                               dl_encrypt_disable = self.dl_encrypt_disable,
                                               dl_decrypt_disable = self.dl_decrypt_disable,
                                               dl_cache_disable = self.dl_cache_disable)

    def esp_gen_secure_key(self):
        if self.secure_boot_en or self.flash_encryption_en:
            secure_path = "./secure"
            if not os.path.isdir(secure_path):
                os.makedirs(secure_path)

            secure_boot_key = "secure_boot_key.bin"
            flash_encrypt_key = "flash_encrypt_key.bin"

            self.flash_crypt_conf = 0xf
            self.flash_key_path = os.path.join(secure_path, flash_encrypt_key)
            self.boot_key_path = os.path.join(secure_path, secure_boot_key)
            if self.debug_mode:
                debug_pem_file = self.debug_pem_path
                self.flash_pem_path = debug_pem_file
                self.boot_pem_path = debug_pem_file
            else:
                debug_pem_file = None
                self.boot_pem_path  = os.path.join(path_str, "secure_boot_key.pem")
                self.flash_pem_path = os.path.join(path_str, "flash_encrypt_key.pem")

            secure_burn.gen_security_key(boot_key_file = self.boot_key_path,
                                         flash_key_file = self.flash_key_path,
                                         boot_pem = self.boot_pem_path,
                                         flash_pem = self.flash_pem_path,
                                         debug_mode = self.debug_mode
                                         )

            for i,(filepath, addr) in enumerate(self.dl_list):
                if addr == 0x1000 and "bootloader" in filepath and self.secure_boot_en:
                    output = os.path.splitext(filepath)[0] + "-digest-0x0000.bin"
                    secure_burn.gen_secure_boot_digest(iv=None, image = filepath,
                                                      keyfile = self.boot_key_path,
                                                      output = output)
                    filepath = output
                    addr = 0x0
                    self.dl_list[i] = (filepath, addr)
                if self.flash_encryption_en:
                    output = os.path.splitext(filepath)[0] + "-encrypt.bin"
                    secure_burn.gen_encrypted_flash_image(output = output, plaintext = filepath, address = addr, keyfile = self.flash_key_path, flash_crypt_conf = self.flash_crypt_conf)
                    filepath = output
                    self.dl_list[i] = (filepath, addr)

    def esp_write_flash(self, esp, param):
        try:
            self.esp_gen_secure_key()
        except IOError, e:
            self.logger.error("generate secure key error: {}".format(e))
            raise err_define.BurnSecureBootKeyError(chip = self.chip, func = self.esp_write_flash)

        if self.stopFlg:
            return
        try:
            param.addr_filename = [((addr), open(filepath, 'rb')) for (filepath, addr) in self.dl_list]
            self.state = self.ESP_DL_DOWNLOADING
            self.write_flash(esp, param)
            self.state = self.ESP_DL_FINISH
            for _, file_handle in param.addr_filename:
                file_handle.close()
                del(file_handle)
        except:
            raise err_define.ChipFlashDownloadError(self.chip, self.esp_write_flash)

        if self.state == self.ESP_DL_FINISH:
            self.esp_burn_security_key(esp)

class ESP32D2WDDownloader(ESP32Downloader):
    def __init__(self, frame, port = "COM6", baudrate = 115200, name = '',
                 chip = "ESP32D2WD", sub_chip='', num = 1):
        super(ESP32D2WDDownloader, self).__init__(frame=frame, port=port, baudrate=baudrate, name=name, chip=chip, sub_chip=sub_chip, num=num)
        self.rom = esptool.ESP32ROM
        self.chip = chip
        self.name = name
        self.efuse_mode = param_save_load.conf_get_value(section = "EFUSE CHECK", option = "efuse_mode", default = 1, value_type = int, chip = self.chip, name = self.name)
        self.efuse_err_halt = param_save_load.conf_get_value(section = "EFUSE CHECK", option = "efuse_err_halt", default = 1, value_type = int, chip = self.chip, name = self.name)


    def flash_spi_attach_req(self,ucIsHspi,ucIsLegacy):
        """Send SPI attach command"""
        print "SEND ESP SPI ATTACH CMD"
        result = self.esp.command(self.esp.ESP_SPI_ATTACH,
                              #                    ucIsHSPI, ucIsLegacy, rsv , rsv,rsv
                              struct.pack('<IBBBB', ucIsHspi, ucIsLegacy,  0   , 0  , 0 ))[1]
        if result != "\0\0\0\0":
            raise esptool.FatalError.WithResult('Failed to config flash (result "%s")', result)

    def esp_config_spi_mode(self):
        uc_is_hspi = 0xb10081106
        uc_is_hspi=((((uc_is_hspi >> 32) & 0x3f) << 24) | (((uc_is_hspi >> 24) & 0x3f) << 18) |
                    (((uc_is_hspi >> 16) & 0x3f) << 12) | (((uc_is_hspi >> 8) & 0x3f) << 6) | (((uc_is_hspi >> 0) & 0x3f) << 0))
        try:
            #self.esp.flash_spi_attach(hspi_arg = uc_is_hspi)
            self.flash_spi_attach_req(ucIsHspi = uc_is_hspi, ucIsLegacy = 0)
        except esptool.FatalError, e:
            raise err_define.ConfiguredSPICmdError(chip = self.chip, func = self.esp_config_spi_mode)

class MyParam(object):
    def __init__(self, chip, name):
        self.addr_filename = []
        section = "ESPTOOL_PARAM"
        #filepath = "ToolSettings.conf"
        self.after= param_save_load.conf_get_value(section = section, option = "after", default="hard_reset", value_type=str, chip = chip, name=name)
        self.baud=param_save_load.conf_get_value(section = section, option = "baud", default=115200, value_type=int, chip = chip, name=name)
        self.before=param_save_load.conf_get_value(section = section, option = "before", default="default_reset", value_type=str, chip = chip, name=name)
        self.chip=param_save_load.conf_get_value(section = section, option = "chip", default="auto", value_type=str, chip = chip, name=name)
        self.compress=param_save_load.conf_get_value(section = section, option = "compress", default=0, value_type=int, chip = chip, name=name)
        self.flash_freq=param_save_load.conf_get_value(section = section, option = "flash_freq", default="keep", value_type=str, chip = chip, name=name)
        self.flash_mode=param_save_load.conf_get_value(section = section, option = "flash_mode", default="keep", value_type=str, chip = chip, name=name)
        self.flash_size=param_save_load.conf_get_value(section = section, option = "flash_size", default="keep", value_type=str, chip = chip, name=name)
        self.no_compress=param_save_load.conf_get_value(section = section, option = "no_compress", default=False, value_type=bool, chip = chip, name=name)
        self.no_progress=param_save_load.conf_get_value(section = section, option = "no_progress", default=False, value_type=bool, chip = chip, name=name)
        self.no_stub=param_save_load.conf_get_value(section = section, option = "no_stub", default=False, value_type=bool, chip = chip, name=name)
        self.operation=param_save_load.conf_get_value(section = section, option = "operation", default="write_flash", value_type=str, chip = chip, name=name)
        self.port=param_save_load.conf_get_value(section = section, option = "port", default="/dev/cu.SLAB_USBtoUART", value_type=str, chip = chip, name=name)
        self.spi_connection=param_save_load.conf_get_value(section = section, option = "spi_connection", default=0, value_type=int, chip = chip, name=name)
        self.verify=param_save_load.conf_get_value(section = section, option = "verify", default=False, value_type=bool, chip = chip, name=name)
        #setting_dict = param_save_load.conf_get_sec_dict(filepath=filepath, section=section)
        #if not setting_dict:
            #param_save_load.conf_save_param(filepath = filepath, section = section, param_dict = self.__dict__)

    def save(self, chip, name):
        param_save_load.conf_save_param(chip = chip, name = name, section = section, param_dict = self.__dict__)





class ESP8285FACTORY(ESP8285Downloader):
    def __init__(self, frame, port="COM6", baudrate=115200, name='',
                chip="ESP32", sub_chip='', num=1):
        #self.efuse_mode = param_save_load.get_Test_Param("chip_conf", "EFUSE_MODE")
        #self.crystal_freq = param_save_load.get_Test_Param("chip_conf", "FREQ")
        self.frame=frame
        self.efuse_mode=self.frame.efusemode
        self.crystal_freq=26        
        self.efuse_err_halt = 1
        self.EFUSE_ERR_FLG = 0x1
        self.EFUSE_WARNING_FLG = 0x2
        self.flash_manufacturer_id=-1
        self.flash_device_id=-1
        super(ESP8266Downloader, self).__init__(frame=frame, port=port, baudrate=baudrate, name=name, chip=chip, sub_chip=sub_chip, num=num)

    def run_firmware(self):
        if "ESP32" in self.chip:
            self.flash_spi_attach_req(0, 0)
        self.esp.flash_begin(0, 0)
        self.esp.flash_finish(reboot=True)

class ESP8266FACTORY(ESP8266Downloader):
    def __init__(self, frame, port="COM6", baudrate=115200, name='',
                chip="ESP32", sub_chip='', num=1):
        #self.efuse_mode = param_save_load.get_Test_Param("chip_conf", "EFUSE_MODE")
        #self.crystal_freq = param_save_load.get_Test_Param("chip_conf", "FREQ")
        self.frame=frame
        self.efuse_mode=self.frame.efusemode
        self.crystal_freq=26        
        self.efuse_err_halt = 1
        self.EFUSE_ERR_FLG = 0x1
        self.EFUSE_WARNING_FLG = 0x2
        self.flash_manufacturer_id=-1
        self.flash_device_id=-1
        super(ESP8266Downloader, self).__init__(frame=frame, port=port, baudrate=baudrate, name=name, chip=chip, sub_chip=sub_chip, num=num)

    def run_firmware(self):
        if "ESP32" in self.chip:
            self.flash_spi_attach_req(0, 0)
        self.esp.flash_begin(0, 0)
        self.esp.flash_finish(reboot=True)

class ESP32FACTORY(ESP32Downloader):
    def __init__(self, frame, port="COM6", baudrate=115200, name='',
                chip="ESP32", sub_chip='',num=1):
        #self.efuse_mode = param_save_load.get_Test_Param("chip_conf", "EFUSE_MODE")
        #self.crystal_freq = param_save_load.get_Test_Param("chip_conf", "FREQ")
        self.frame=frame
        self.efuse_mode=self.frame.efusemode
        self.crystal_freq=40
        self.efuse_err_halt = 1
        self.EFUSE_ERR_FLG = 0x1
        self.EFUSE_WARNING_FLG = 0x2
        self.flash_manufacturer_id=-1
        self.flash_device_id=-1
        super(ESP8266Downloader, self).__init__(frame=frame, port=port, baudrate=baudrate, name=name, chip=chip, sub_chip=sub_chip, num=num)
        #self.logger = myLogger.logger_init("ESP32Loader_{name}[{num}]".format(name = name, num = num), chip, name)

    def flash_spi_attach_req(self,ucIsHspi,ucIsLegacy):
        """Send SPI attach command"""
        print "SEND ESP SPI ATTACH CMD"
        result = self.esp.command(self.esp.ESP_SPI_ATTACH,
                              #                    ucIsHSPI, ucIsLegacy, rsv , rsv,rsv
                              struct.pack('<IBBBB', ucIsHspi, ucIsLegacy,  0   , 0  , 0 ))[1]
        if result != "\0\0\0\0":
            raise esptool.FatalError.WithResult('Failed to config flash (result "%s")', result)

    def esp_config_spi_mode(self):
        uc_is_hspi = 0xb10081106
        uc_is_hspi=((((uc_is_hspi >> 32) & 0x3f) << 24) | (((uc_is_hspi >> 24) & 0x3f) << 18) |
                    (((uc_is_hspi >> 16) & 0x3f) << 12) | (((uc_is_hspi >> 8) & 0x3f) << 6) | (((uc_is_hspi >> 0) & 0x3f) << 0))
        try:
            #self.esp.flash_spi_attach(hspi_arg = uc_is_hspi)
            self.flash_spi_attach_req(ucIsHspi = uc_is_hspi, ucIsLegacy = 0)
        except esptool.FatalError, e:
            raise err_define.ConfiguredSPICmdError(chip = self.chip, func = self.esp_config_spi_mode)


if __name__ == '__main__':
    #esp = ESP8266Downloader(frame = None, port="/dev/cu.SLAB_USBtoUART", baudrate=115200, efuse_mode=1,
                           #name='testName',
                           #chip="ESP8266",
                           #efuse_err_halt=1,
                           #num=1, check_mac=1)

    #esp.flash_download_test(com = "/dev/cu.SLAB_USBtoUART",
                            #baudrate = 1152000,
                            #_dl_list = [(0, "./bin_tmp/test.bin")],
                            #stub_mode=False,
                            #factory=False)

    esp = ESP8266Downloader(frame = None, port="/dev/cu.SLAB_USBtoUART", baudrate=115200, name='spi',
                    chip="ESP8266", num=1)
    esp.flash_download_test(com = "/dev/cu.SLAB_USBtoUART",
                            baudrate = 1152000,
                            _dl_list = [("./bin_tmp/test.bin", 0)],
                            stub_mode=False,
                            factory=False)


