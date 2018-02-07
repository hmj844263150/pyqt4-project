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
import esptool as esptool


class ChipStopped(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s Chip stopped %s." % (chip, func.__name__))

class ChipSyncError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s Chip sync error %s." % (chip, func.__name__))

class ChipStubError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s Chip stub error %s." % (chip, func.__name__))

class ChipHspiError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s Chip hspi error %s." % (chip, func.__name__))

class ChipEfuseCheckError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s Chip efuse check error %s." % (chip, func.__name__))
class ChipFlashIDError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s Chip flash ID error %s." % (chip, func.__name__))
class ChipFlashParamError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s Chip flash param error %s." % (chip, func.__name__))
class ChipFlashDownloadError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s Chip flash download error %s." % (chip, func.__name__))
class ChipEfuseDisRomConsoleError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s efuse disable rom console error %s." % (chip, func.__name__))

class NotImplementedFuncError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s NotImplementedFuncError %s." % (chip, func.__name__))

class ReadMacRegError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s ReadMacRegError %s." % (chip, func.__name__))

class ConfiguredSPICmdError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s ConfiguredSPICmdError %s." % (chip, func.__name__))

class BurnSecureBootKeyError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s BurnSecureBootKeyError %s." % (chip, func.__name__))

class BurnFlashEncryptKeyError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s BurnFlashEncryptKeyError %s." % (chip, func.__name__))

class EfuseSetDisableError(esptool.FatalError):
    """
    Wrapper class for the error thrown when a particular ESP bootloader function
    is not implemented in the ROM bootloader.
    """
    def __init__(self, chip, func):
        esptool.FatalError.__init__(self, "%s EfuseSetDisableError %s." % (chip, func.__name__))