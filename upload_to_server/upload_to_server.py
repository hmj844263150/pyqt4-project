
import json
import sys
import os
import socket

DEBUG = 0

no_err      = "0x00" 
err_params  = "0x01"
err_conn    = "0x02"
err_upload  = "0x03"
err_other   = "0xff"

class Uploader(object):
    server_ip     = ''
    server_port = 0
    HttpJson = {
        "path":"",
        "method":"",
        "testdata":{
            "device_type":   "ESP_WROOM02",
            "fw_ver":        "v1.0.0.0",
            "esp_mac":       "22:22:22:22:22:10",
            "cus_mac":       "",
            "flash_id":      "19191919",
            "test_result":   "success",
            "factory_sid":   "esp-fae-test-a95342f3",
            "batch_sid":     "6a5fbb0d43",
            "efuse":        "",
            "chk_repeat_flg": True,
            "po_type":       0,
        }
    }

    def __init__(self, params):
        self.server_ip      = params['server_ip']
        self.server_port    = int(params['server_port'])

        self.HttpJson["path"] = "/testdata"
        self.HttpJson["method"] = "POST"
        self.HttpJson["testdata"]["device_type"]    = params['device_type']
        self.HttpJson["testdata"]["fw_ver"]         = params['fw_ver']
        self.HttpJson["testdata"]["esp_mac"]        = params['esp_mac']
        self.HttpJson["testdata"]["cus_mac"]        = params['cus_mac']
        self.HttpJson["testdata"]["flash_id"]       = params['flash_id']
        self.HttpJson["testdata"]["test_result"]    = params['test_result']
        self.HttpJson["testdata"]["factory_sid"]    = params['factory_sid']
        self.HttpJson["testdata"]["batch_sid"]      = params['batch_sid']
        self.HttpJson["testdata"]["efuse"]          = params['efuse']
        if params['chk_repeat_flg'].lower()=='true':
            self.HttpJson["testdata"]["chk_repeat_flg"] = True
        else:
            self.HttpJson["testdata"]["chk_repeat_flg"] = False
        self.HttpJson["testdata"]["po_type"]        = int(params['po_type'])
        if(DEBUG): print ("class info:", self.HttpJson)

    def client(self):
        rsp = {"status":-1}
        try:
            if(DEBUG): print ("tcp:", (self.server_ip, self.server_port))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server_ip, self.server_port))
        except:
            if(DEBUG): print ("conn to server fail")
            return -1, rsp

        send_data_json = json.dumps(self.HttpJson)
        send_data_json += '\n'
        if(DEBUG): print ("send_data:", send_data_json)
        s.send(send_data_json)
        rsp = s.recv(1024)
        if(DEBUG): print ("recv_data:", rsp)
        rsp = json.loads(rsp)

        s.close()
        return 0, rsp

def main():
    global DEBUG
    err_msg = {
        "err_code" : no_err,
        "err_info" : ''
    }
    try:
        # import ConfigParser
        # config = ConfigParser.ConfigParser()
        # config = read(u'config/setting.ini')
        params = sys.argv[1]
        if params.find("DEBUG") >= 0:
            DEBUG = 1
        if(DEBUG): print ("params:", params)
        params = json.loads(params)
        uploader = Uploader(params)

    except:
        err_msg["err_code"] = err_params
        err_msg["err_info"] = "read params ERROR"
        print (err_msg)
        return

    try:
        t_err, rsp = uploader.client()
        if t_err != 0:
            err_msg["err_code"] = err_conn
            err_msg["err_info"] = "tcp conn error"
        elif rsp["status"] == 500:
            err_msg["err_code"] = err_upload
            err_msg["err_info"] = rsp["message"]
        elif rsp["status"] == 200:
            err_msg["err_code"] = no_err
            err_msg["err_info"] = "send to server success"
        else:
            err_msg["err_code"] = err_other
            err_msg["err_info"] = "unknow error"
    except:
        err_msg["err_code"] = err_conn
        err_msg["err_info"] = "tcp conn error"

    print (err_msg)
    return

if __name__ == "__main__":
    main()
    
"""
params:
"{\"server_ip\":\"120.76.204.21\", \"server_port\":\"6666\", \"device_type\":\"WROOM02\", \"fw_ver\":\"\", \"esp_mac\":\"2c3ae8080000\", \"cus_mac\":\"\", \"flash_id\":\"\", \"test_result\":\"success\", \"factory_sid\":\"esp-fae-test-a95342f3\", \"batch_sid\":\"6a5fbb0d43\", \"efuse\":\"\", \"chk_repeat_flg\":\"True\", \"po_type\":\"0\",\"DEBUG\":\"1\"}"

output:
{"err_code":"xx", "err_info":"xxxx"}
"0x00": succ
"0x01": input params error
"0x02": tcp connect error
"0x03": upload to server error
"0xff": other error
"""