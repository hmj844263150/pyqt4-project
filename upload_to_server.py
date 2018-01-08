
import json
import sys
import os
import socket

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
        print self.HttpJson

    def client(self):
    	try:
    		print (self.server_ip, self.server_port)
    		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    		s.connect((self.server_ip, self.server_port))
    	except:
    		print ("conn to server fail")
    		return -1

    	send_data_json = json.dumps(self.HttpJson)
    	send_data_json += '\n'
    	s.send(send_data_json)
    	rsp = s.recv(1024)
    	print rsp
    	rsp = json.loads(rsp)
    	if rsp["status"] == 500:
    		print (rsp["message"])

    	s.close()
        return True

def main():

    # import ConfigParser
    # config = ConfigParser.ConfigParser()
    # config = read(u'config/setting.ini')
    params = sys.argv[1]
    #print params
    params = json.loads(params)
    uploader = Uploader(params)

	# except:
	#     print('read params ERROR')
	#     return

    try:
        if uploader.client():
            print ('SUCCESS')
        else:
            print ('FAILED')
    except:
        print ('upload ERROR')
        return

    return

if __name__ == "__main__":
    main()
    
"""
"{\"server_ip\":\"120.76.204.21\", \"server_port\":\"6666\", \"device_type\":\"WROOM02\", \"fw_ver\":\"\", \"esp_mac\":\"2c3ae8080000\", \"cus_mac\":\"\", \"flash_id\":\"\", \"test_result\":\"success\", \"factory_sid\":\"esp-fae-test-a95342f3\", \"batch_sid\":\"6a5fbb0d43\", \"efuse\":\"\", \"chk_repeat_flg\":\"True\", \"po_type\":\"0\"}"
"""