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

import ConfigParser
import tool_path
import os

def save_param(filepath, section, param_dict):
    filepath = tool_path.path_dict[chip.lower()]
    cf = ConfigParser.ConfigParser()
    cf.read(filepath)
    if not cf.has_section(section = section):
        cf.add_section(section=section)
    for key, value in param_dict.items():
        cf.set(section=section, option=key, value=value)
    cf.write(open(filepath, "w"))

def _conf_get_file_path(chip, name):
    filepath = ""
    path_obj = tool_path.path_dict[chip.lower()]
    for item, path in path_obj.__dict__.iteritems():
        if name in item:
            filepath = path
            break
    return filepath

def conf_save_param(chip, name, section, param_dict):
    filepath = _conf_get_file_path(chip, name)
    cf = ConfigParser.ConfigParser()
    cf.read(filepath)
    if not cf.has_section(section = section):
        cf.add_section(section=section)
    for key, value in param_dict.items():
        cf.set(section=section, option=key, value=value)
    cf.write(open(filepath, "w"))

def get_sec_dict(filepath, section):
    cf = ConfigParser.ConfigParser()
    try:
        cf.read(filepath)
        sec_dict = dict(cf.items(section = section))
        return sec_dict
    except ConfigParser.NoSectionError:
        return {}

def conf_get_sec_dict(chip, name, section):
    filepath = _conf_get_file_path(chip, name)
    cf = ConfigParser.ConfigParser()
    try:
        cf.read(filepath)
        sec_dict = dict(cf.items(section = section))
        return sec_dict
    except ConfigParser.NoSectionError:
        return {}








def param_save(config_file,param_dict,separate = ":",item_postfix = ""):
    try:
        f=open(config_file,'r')
        lines = f.readlines()
        f.close()
    except:
        lines = []

    for key in param_dict.keys():
        found = False
        for i in range(len(lines)):
            line = lines[i]
            if key in line:
                lines[i]=key+item_postfix+separate+"%s\n"%(str( param_dict[key]))
                found = True
                break
        if not found:
            lines.append(key+item_postfix+separate+"%s\n"%(str(param_dict[key])))
    param_str = "".join(lines)
    f=open(config_file,'w')
    f.write(param_str)
    f.close()

def _get_value(section, option, default, value_type, filepath):
    cf = ConfigParser.ConfigParser()
    cf.read(filepath)
    value = None
    try:
        if value_type == int:
            value = cf.getint(section, option)
        elif value_type in [str, unicode]:
            value = cf.get(section, option)
        elif value_type is bool:
            value = cf.getboolean(section, option)
        elif value_type is float:
            value = cf.getfloat(section, option)
        else:
            value = default
    except ConfigParser.NoOptionError:
        cf.set(section, option, default)
        cf.write(open(filepath, "w"))
        value = default
    except ConfigParser.NoSectionError:
        cf.add_section(section)
        cf.set(section, option, default)
        cf.write(open(filepath, "w"))
        value = default
    except ValueError:
        cf.set(section, option, default)
        cf.write(open(filepath, "w"))
        value = default
    return value

def conf_get_value(section, option, default, value_type, chip, name):
    filepath = _conf_get_file_path(chip, name)
    return _get_value(section, option, default, value_type, filepath)

def conf_update_value(section, option, new_value, value_type, chip, name):
    filepath = _conf_get_file_path(chip, name)
    cf = ConfigParser.ConfigParser()
    cf.read(filepath)
    value = None
    try:
        if value_type == int:
            value = cf.getint(section, option)
        elif value_type in [str, unicode]:
            value = cf.get(section, option)
        elif value_type is bool:
            value = cf.getboolean(section, option)
        elif value_type is float:
            value = cf.getfloat(section, option)
        else:
            pass
        if new_val != value:
            cf.set(section, option, new_val)
            cf.write(open(filepath, "w"))
    except ConfigParser.NoOptionError:
        cf.set(section, option, new_val)
        cf.write(open(filepath, "w"))
    except ConfigParser.NoSectionError:
        cf.add_section(section)
        cf.set(section, option, new_val)
        cf.write(open(filepath, "w"))
    except ValueError:
        cf.set(section, option, new_val)
        cf.write(open(filepath, "w"))

#def param_load(config_file,param,separate = ":"):
    #try:
        #f = open(config_file,'r')
        #lines = f.readlines()
        #f.close()
    #except:
        #lines = []

    #if type(param) == type({}):
        #for key in param.keys():
            #found = False
            #for line in lines:
                #if key in line:
                    #found = True
                    ##print "test line:",line
                    #try:
                        #param[key]=line.split("%s"%separate)[1]
                    #except:
                        #param[key]=line.split(":")[1]

                #if found:
                    #break
    #elif type(param) == type(""):
        #for line in lines:
            #if param in line:
                #return line.split("%s"%separate)[1]
    #else:
        #print "param type error"
        #return None



def get_Config(section, key):
    config = ConfigParser.ConfigParser()
    path = os.path.abspath('.') + '/config/settings.conf'
    config.read(path)
    ret = config.get(section, key)
    if ret.isdigit():
        return int(ret)
    else:
        return ret

def get_Test_Param(section, key):
    config = ConfigParser.ConfigParser()
    path = os.path.abspath('.') + file_name
    config.read(path)
    ret = config.get(section, key)
    if ret.isdigit():
        return int(ret)
    else:
        return ret

#file_name = get_Config('common_conf', 'FILE_PATH')
file_name=''

if __name__ == "__main__":
    cf = ConfigParser.ConfigParser()
    try:
        cf.read("ToolSettings.conf")
        int_val = cf.getint("EFUSE", "EFUSE_MODE")
    except ConfigParser.NoOptionError:
        print("no option error")
        int_val = 1
    except ConfigParser.NoSectionError:
        print("ConfigParser.NoSectionError")
        int_val = 1

    print("int_val:", int_val)

    print("cf sec: ", cf.sections())
    a = cf.getint(section="ESP8266_MultiDownload", option="efuse_mode")
    print("cf opt: ", cf.options("ESP8266_SPIDownload"))
    print("cf item: ", dict(cf.items("ESP8266_SPIDownload")))
    pass