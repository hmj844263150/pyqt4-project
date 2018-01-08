
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
    def __init__(self, **params):
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
        self.chk_repeat_flg = params['chk_repeat_flg']
        self.po_type        = params['po_type']

    def client(self):
        return True

def main():
    try:
        # import ConfigParser
        # config = ConfigParser.ConfigParser()
        # config = read(u'config/setting.ini')
        params = json.loads(sys.args[1])
        uploader = Uploader(params)
    except:
        print('read params ERROR')
        return

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