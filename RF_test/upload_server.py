import socket
import json

HOST = "120.76.204.21"
PORT = 6666



def sock_request(host,port,timeout,data_req):
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        print("set timeout %d"%timeout)
        sock.settimeout(timeout)        
        sock.connect((host,port))
        #print 'data_req:'
        #print data_req
        sock.send(data_req)
        #print("recv")
        resp = sock.recv(2048)
        sock.close()
        #print "resp:"
        #print resp  
        return resp
        
    except socket.error,arg:
        print("error: %s"%arg)
        print("UPLOAD TEST RESULT ERROR")
        sock.close()
        return ''
    

def get_test_print_num(host,port,timeout = 3,device_type="",esp_mac = '',batch_sid="",dryrun = "false"):
    #get_dict = dict([("path","/testdata/print")])
    get_dict = dict([("dryrun",dryrun),("esp_mac",esp_mac)])  #set false to just read result, not write
    body_dict = {}
    body_dict['device_type'] = device_type #"ESP_WROOM02"
    #body_dict['esp_mac'] = esp_mac #'18:fe:34:a1:32:aa'
    body_dict['batch_sid'] = batch_sid #"1234567890"
    
    data_req = dict()
    data_req["path"] = "/testdata/print"
    data_req["method"] = "Post"
    data_req["get"] = get_dict
    data_req["body"] = body_dict
    
    data_req = json.dumps(data_req)
    data_req += "\n"
    #print("data req:\n",data_req)
    
    resp = sock_request(host,port,timeout, data_req)
    if resp == '':
        return False,-1
    else:
        try:
            print_num = json.loads(resp)["print_times"]
            return True,print_num
        except:
            return False,-1
            

def upload_test_res(host,port,timeout = 3,device_type = "ESP_WROOM02",fw_ver="v1.0.0.0",esp_mac = "",cus_mac="",flash_id = "",test_result='',factory_sid="",batch_sid="",efuse = '',chk_repeat_flg=0,po_type=0):
    test_data = {}
    test_data['device_type'] = device_type #"ESP_WROOM02"
    test_data['fw_ver'] = fw_ver #"v1.0.0.0"
    test_data['esp_mac'] = esp_mac #"18:fe:34:a1:32:aa"
    #test_data['esp_mac'] = '11:11:11:11:00:03'
    test_data['cus_mac'] = cus_mac
    test_data['flash_id'] = flash_id #"0x4015"
    test_data['test_result'] = test_result #"success"
    test_data['factory_sid'] = factory_sid #"factory001"
    test_data['batch_sid'] = batch_sid #"factory001_20160704ac"
    test_data['efuse'] = efuse #'128389279848293884929838929384938934'
    test_data['po_type'] = str(po_type)
    if chk_repeat_flg == 0:
        test_data['chk_repeat_flg'] = 'false'
    elif chk_repeat_flg == 1:
        test_data['chk_repeat_flg'] = 'true'

    data_dict = [("path","/testdata"),("method","POST"),("testdata","")]
    data_dict = dict(data_dict)
    
    data_dict["testdata"] = test_data
    print "data dict", data_dict

    data = json.dumps(data_dict)
    data+="\n"
    print "data request is ", data
    
    resp = sock_request(host,port,timeout,data)
    print "resp from server is", resp
    if resp == '':
        return (False,'',None)
    else:
        r_data = json.loads(resp.strip("\n"))
        print r_data
        try:
            upload_res = r_data["status"]
            print "test data:",upload_res
        
            if upload_res == 200:
                upload_res = True
            else:
                upload_res = False
        except:
            upload_res = False
        
        try:
            cus_mac = r_data["cus_mac"]
            print "cus_mac:",cus_mac
        except:
            cus_mac = ''
        return (upload_res,cus_mac,r_data)        
        
#def get_print_times():
    #resp = check_test_print_res(device_type="ESP_WROOM02",esp_mac="18:fe:34:a1:32:aa",batch_id="SrLcuWF",dryrun = "true")
    #if resp == '':
        #return (False,-1)
    #else:
        #print ("test")
        ##try:
        #if True:
            #d_resp = json.loads(resp.strip("\n"))
            #print "d_resp:",d_resp
            #print_times = d_resp["print_times"]
            #return (True,print_times)
        ##except:
            ##return (False,-1)
    
if __name__=="__main__":
    res = upload_test_res(
                          host=HOST,
                          port=PORT,
                          device_type = "ESP_WROOM02",
                          fw_ver="v1.0.0.0",
                          esp_mac = "18:fe:34:a1:32:aa",
                          flash_id = "0x4016",
                          test_result='success',
                          factory_sid = "esp-own-test-FID-dbd42d01",
                          batch_sid = "bf54c4adf0",
                          efuse = '',
                          chk_repeat_flg=0,
                          po_type=0
                          )
    
    
    print("upload res:",res)
    
    print "\n\n\n"
    #check_test_print_res(device_type="ESP_WROOM02",esp_mac="18:fe:34:a1:32:aa",batch_id="1111122222",dryrun = "true")
    
    res = get_test_print_num(host=HOST,port=PORT,device_type="ESP_WROOM02",esp_mac="18:fe:34:a1:32:aa",batch_sid="SrLcuWF",dryrun = "true")
    print("printed res:")
    print(res)
    
    res = get_test_print_num(host=HOST,port=PORT,device_type="ESP_WROOM02",esp_mac="18:fe:34:a1:32:aa",batch_sid="SrLcuWF",dryrun = "false")
    print "set print:"
    print res
    
    
    