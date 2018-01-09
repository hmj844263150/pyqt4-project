## input:

* server_ip:        server's ip address
* server_port:      server's port
* device_type:      target module's type such as WROOM02
* fw_ver:           target firmware version number
* esp_mac:          chip default mac
* cus_mac:          chip custom mac
* flash_id:         chip flash id
* test_result:      success/fail
* factory_sid: 
* batch_sid:
* efuse:            total efuse value
* chk_repeat_flg:   check mac repeat or not True/False
* po_type:          batch type, 0-normal, 1-rework(re-fw), 2-rework(re-mac)..

## example:

"{\"server_ip\":\"120.76.204.21\", \"server_port\":\"6666\", \"device_type\":\"WROOM02\", \"fw_ver\":\"\", \"esp_mac\":\"2c3ae8080000\", \"cus_mac\":\"\", \"flash_id\":\"\", \"test_result\":\"success\", \"factory_sid\":\"esp-fae-test-a95342f3\", \"batch_sid\":\"6a5fbb0d43\", \"efuse\":\"\", \"chk_repeat_flg\":\"True\", \"po_type\":\"0\"}"

P.s: ",\"DEBUG\":\"1\"" :  for output debug info

# output:
{"err_code":"xx", "err_info":"xxxx"}

* "0x00": succ
* "0x01": input params error
* "0x02": tcp connect error
* "0x03": upload to server error
* "0xff": other error

"""

