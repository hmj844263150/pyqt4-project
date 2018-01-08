
import json
import sys
import os

class Uploader(object):
    server_ip     = ''
    server_port = 0
    device_type = ''
    fw_ver        = ''
    esp_mac        = ''
    cus_mac        = ''        # custom mac
    flash_id    = ''
    test_result    = ''
    factory_sid    = ''
    batch_sid     = ''
    efuse        = ''
    chk_repeat_flg    = True     # True:check mac repeat, False:no check
    po_type        = 0            # 0:normal, 1:rework(fw..), 2:rework(mac)
    def __init__(self, params):
        self.server_ip      = params['server_ip']
        self.server_port    = params['server_port']
        self.device_type    = params['device_type']
        self.fw_ver         = params['fw_ver']
        self.esp_mac        = params['esp_mac']
        self.cus_mac        = params['cus_mac']
        self.flash_id       = params['flash_id']
        self.test_result    = params['test_result']
        self.factory_sid    = params['factory_sid']
        self.batch_sid      = params['batch_sid']
        self.efuse          = params['efuse']
        if params['chk_repeat_flg'].lower()=='true':
            self.chk_repeat_flg = True
        else:
            self.chk_repeat_flg = False
        self.po_type        = int(params['po_type'])

    def client(self):
        return True

def main():

    # import ConfigParser
    # config = ConfigParser.ConfigParser()
    # config = read(u'config/setting.ini')
    params = sys.argv[1]
    print params
    params = json.loads(params)
    uploader = Uploader(params)

    print('read params ERROR')
    #return

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
"{\"server_ip\":\"192.168.1.1\", \"server_port\":\"6666\", \"device_type\":\"WROOM02\", \"fw_ver\":\"\", \"esp_mac\":\"2c3ae8080000\", \"cus_mac\":\"\", \"flash_id\":\"\", \"test_result\":\"success\", \"factory_sid\":\"esp-fae-test-a95342f3\", \"batch_sid\":\"6a5fbb0d43\", \"efuse\":\"\", \"chk_repeat_flg\":\"True\", \"po_type\":\"0\"}"
"""