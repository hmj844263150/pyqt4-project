# input:

config:     path of the setting file
operation:  0:read mac, 1:load to ram, 2:burn cus_mac, 3:load to flash(without check)

## example:

"{\"config\":\"config/setting.ini\", \"operation\":\"0\"}"

option: ,\"cus_mac\":\"2c3ae808000f\" -- use for burn custom mac

P.s: ",\"DEBUG\":\"1\"" :  for output debug info

# output:

{"err_code":"xx", "err_info":"xxxx"}

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
"""
