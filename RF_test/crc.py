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

def calcrc_onebyte(abyte):
    abyte=abyte&0xff
    crc_1byte = 0
    for i in range(8):
        if ((crc_1byte^abyte)&0x01)>0:
            crc_1byte ^= 0x18
            crc_1byte >>= 1
            crc_1byte |= 0x80
        else:
            crc_1byte >>= 1
        abyte >>= 1
    return crc_1byte

def calcrc(dlist):
    crc = 0
    clen = len(dlist)
    for i in range(clen):
        crc = calcrc_onebyte(crc ^ dlist[i])
    return crc

def esp_crc8(dlist):
    crc = 0
    clen = len(dlist)
    for i in range(clen):
        crc = crc ^ dlist[i]
        for j in range(8):
            if (crc & 0x1) > 0: 
                crc = (crc >> 1) ^ 0x8c
            else:
                crc = crc >> 1
    return crc


def crc_cal_by_bit(data_list):
    length = len(data_list)
    CRC_CCITT = 0x1021
    crc = 0;
    #unsigned char i ;

    while length>0:
        for data in data_list:
            length-=1
            i = 0x80
            while i >= 1:
                crc*=2;
                if (crc&0x10000) != 0:
                    crc^=0x11021
                    crc = crc&0xffffffff
                if data&i != 0:
                    crc^= CRC_CCITT
                i/=2
    return crc

def calc_0_num(self, dnum, zero_num):
    while (dnum != 0):
        if(dnum%2 == 1):
            zero_num -= 1
        dnum = dnum >> 1
    return zero_num