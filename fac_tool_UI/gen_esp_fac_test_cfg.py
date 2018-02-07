import os
import re
import sys 
import binascii
import struct
import logging
import datetime

def create_factory_config(test_addr,jump_residue_times):
    f_config = open("esp_fac_test_cfg.bin", "w")
    f_config.close()
    f_config = open('esp_fac_test_cfg.bin', 'r+')
    if f_config:
        #
        data_str = ['FF']*(4096)
        data_bin = binascii.a2b_hex(''.join(data_str))
        f_config.write(data_bin)
        f_config.seek(0,os.SEEK_SET)
        #write magic number
        f_config.write('fact')
        # write test times
        residue_times = struct.pack('<I',long(jump_residue_times,16))
        f_config.write(residue_times)

        # write test bin address
        addr = struct.pack('<I',long(test_addr,16))
        f_config.write(addr)

        #write test bin default test pass flag
        flag = struct.pack('<b',0)
        f_config.write(flag)

        # write checksum
        f_config.seek(0,os.SEEK_SET)
        check_bin = f_config.read(36)
        chk_sum = 0
        for loop in range(len(check_bin)):
            chk_sum ^= ord(check_bin[loop])

        f_config.seek(36,os.SEEK_SET)
        chk_sum_hex = hex(int(chk_sum))
        check_sum = binascii.a2b_hex(str(chk_sum_hex)[2:4])
        f_config.write(check_sum)

        # write end pad 0 in the file
        pad_str = ['00']*(3)
        pad_bin = binascii.a2b_hex(''.join(pad_str))
        f_config.write(pad_bin)

        f_config.close()
        print 'generate esp_fac_test_cfg.bin success'
    else:
        print 'esp_fac_test_cfg.bin open fail\n'
    
    
if __name__ == '__main__':
    test_addr = raw_input("Enter your factory test bin addr(eg. 0x101000): ")
    jump_residue_times = raw_input("Enter the times you want test bin run(default is 8 times, max is 10 times): ")
    if int(jump_residue_times) > 10:
        logging.warning('max test time is 10!!!')
        jump_residue_times = '10'
    create_factory_config(test_addr,jump_residue_times)