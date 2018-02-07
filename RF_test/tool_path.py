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

import os.path

class ToolPath(object):
    def __init__(self, chip):
        self.path_config = "./configure/{chip}".format(chip = chip)
        if not os.path.exists(self.path_config):
            os.makedirs(self.path_config)
        self.path_config_spi_download = "{base}/{filepath}".format(base=self.path_config, filepath = "spi_download.conf")
        self.path_config_hspi_download = "{base}/{filepath}".format(base=self.path_config, filepath = "hspi_download.conf")
        self.path_config_multi_download = "{base}/{filepath}".format(base=self.path_config, filepath = "multi_download.conf")
        self.path_config_utility = "{base}/{filepath}".format(base=self.path_config, filepath = "utility.conf")
        self.path_config_security= "{base}/{filepath}".format(base=self.path_config, filepath = "security.conf")
        self.path_config_factory = "./config/settings.conf"

Esp8266ToolPath = ToolPath(chip = "esp8266")
Esp8285ToolPath = ToolPath(chip = "esp8285")
Esp32ToolPath   = ToolPath(chip = "esp32")
Esp32D2WDToolPath   = ToolPath(chip = "esp32d2wd")


path_dict = {"esp32"  : Esp32ToolPath,
             "esp32d2wd"  : Esp32D2WDToolPath,
             "esp8266": Esp8266ToolPath,
             "esp8285": Esp8285ToolPath,
             }