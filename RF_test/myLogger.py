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

import logging
import param_save_load

LOG_LEVEL_DICT = {"CRITICAL": logging.CRITICAL,
                  "FATAL": logging.FATAL,
                  "ERROR": logging.ERROR,
                  "WARNING": logging.WARNING,
                  "INFO": logging.INFO,
                  "DEBUG": logging.DEBUG,
                  "NOTSET": logging.NOTSET
                  }
g_log_level = logging.DEBUG
g_log_level_str = "INFO"
logger_record_dict = {}

def logger_init(logger_id, chip = "", name=""):
    if logger_id in logger_record_dict.keys():
        return logger_record_dict[logger_id]

    logger = logging.getLogger(logger_id)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(filename)s][line:%(lineno)d][%(levelname)s]: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    g_log_level_str = param_save_load.conf_get_value(section = "LOG_LEVEL",
                                                     option = "{name}_LOG_LEVEL".format(name = name.upper()),
                                                     default = "ERROR",
                                                     value_type = str,
                                                     chip = chip,
                                                     name= "utility",
                                                     )


    try:
        logger.setLevel(LOG_LEVEL_DICT[g_log_level_str])
    except:
        logger.setLevel(logging.WARNING)
    logger_record_dict[logger_id] = logger
    return logger

if __name__ == "__main__":
    pass
