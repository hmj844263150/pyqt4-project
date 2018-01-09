# input/output format

All of tool modules should according to the specified(json) I/O format, 

standard json are consist of pairs <key, value> 

## input:

Consist of each module needs, and should list all params as follow, include each params type or means:

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

And best give a example here,

"{\"server_ip\":\"120.76.204.21\", \"server_port\":\"6666\", \"device_type\":\"WROOM02\", \"fw_ver\":\"\", \"esp_mac\":\"2c3ae8080000\", \"cus_mac\":\"\", \"flash_id\":\"\", \"test_result\":\"success\", \"factory_sid\":\"esp-fae-test-a95342f3\", \"batch_sid\":\"6a5fbb0d43\", \"efuse\":\"\", \"chk_repeat_flg\":\"True\", \"po_type\":\"0\"}"

P.s: ",\"DEBUG\":\"1\"" // for output debug info

## output:

Consist of err_code and err_info just as follow,

{"err_code":"xx", "err_info":"xxxx"}

And each module's readme should list all of err_code's mean, at usual please set 0x0 as success and 0xff as other error as follow,

* "0x00": succ
* "0x01": input params error
* "0x02": error 1
* "0x03": error 2
* ...
* "0x..": error x
* "0xff": other error


