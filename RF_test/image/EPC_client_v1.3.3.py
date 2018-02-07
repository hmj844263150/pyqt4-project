#! _*_ coding=UTF-8 _*_
import sys
import time
import socket
import json

host = '192.168.0.101'
port = 10000

DEBUG = 0

def load_data(rst, custom_mac):
    print {'opt_rst':rst, 'data':custom_mac}
    sys.stdout.flush()
    s = sys.stdin.readline()
    
    if s.find('success') >= 0:
        print "SUCCESS"
        return True
    elif s.find('repeat_mac') >= 0:
        print "repeat_mac"
        return True
    else:
        print "fail"
        return False

#----------------------------------------------------------------------
def tcp_Client(server_ip, port, pro_info):
    """"""
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  
    try:
        s.connect((server_ip,port))  
    except:
        print 'error: connect to server failed'
        sys.exit()
    
    if DEBUG: print 'step 1:send req'
    send_data = {'msg_type':'data_req', 'station_no':pro_info.station_no, 'data_type':pro_info.data_type,
                 'bacth_no':pro_info.bacth_no, 'esp_default_mac':pro_info.esp_default_mac, 
                 'data_token':pro_info.data_token}
    send_data_json = json.dumps(send_data)
    s.send(send_data_json)
    if DEBUG: print 'step 1:wait rsp'
    
    rsp = s.recv(1024)
    try:
        rsp = json.loads(rsp)
        if DEBUG: print rsp
    except:
        print 'error: the rep are not a json'
        s.send('quit')
        s.close()        
        return
    
    if DEBUG: print 'step 2:excute load mac'
    send_data['msg_type'] = 'opt_rst'
    if rsp['err_no'] == 0:
        custom_data = rsp["custom_data"]
        send_data["custom_data"] = custom_data
        if load_data(rsp['err_no'], custom_data):
            if DEBUG: print 'load mac success'
            send_data['write_rst'] = 'success'
        else:
            if DEBUG: print 'load mac failed'
            send_data['write_rst'] = 'failed'
    elif rsp['err_no'] == 1:
        if DEBUG: print 'already had req data, so got old value'
        custom_data = rsp["custom_data"]
        if load_data(rsp['err_no'], custom_data):
            send_data['msg_type'] = 'repeat_mac'
        else:
            s.send('quit')
            s.close()
            return 
    elif rsp['err_no'] == 2:
        if DEBUG: print 'no uable value in db'
        load_data(rsp['err_no'], '')
        s.send('quit')
        s.close()
        return         
    else:
        if DEBUG: print 'get other error'
        load_data(rsp['err_no'], '')
        s.send('quit')
        s.close()
        return    
    
    
    if send_data['msg_type'] == 'repeat_mac':
        if DEBUG: print 'step 2.5: send repeat req'
        send_data_json = json.dumps(send_data)
        s.send(send_data_json)        
        
        rsp = s.recv(1024)
        try:
            rsp = json.loads(rsp)
            if DEBUG: print rsp
        except:
            if DEBUG: print 'the rep are not a json'
            return           
        
        if rsp['err_no'] == 0:
            custom_data = rsp["custom_data"]
            send_data["custom_data"] = custom_data
            if load_data(rsp['err_no'], custom_data):
                if DEBUG: print 'load mac success'
                send_data['write_rst'] = 'success'
            else:
                if DEBUG: print 'load mac failed'
                send_data['write_rst'] = 'failed'     
        else:
            if DEBUG: print 'no uable value in db'
            load_data(rsp['err_no'], '')
            s.send('quit')
            s.close()
            return
    
    if DEBUG: print 'step 3: send opt rst'
    send_data['msg_type'] = 'opt_rst'
    send_data_json = json.dumps(send_data)
    s.send(send_data_json)
    
    rsp = s.recv(1024)
    try:
        rsp = json.loads(rsp)
        if DEBUG: print rsp
    except:
        if DEBUG: print 'the rep are not a json'
        return    
    
    if rsp['err_no'] != 0:
        print 'error:'+ str(rsp['err_no'])
    s.send('quit')       
        
    s.close()
    sys.exit()

########################################################################
class Production(object):
    """"""
    station_no=''
    bacth_no=''
    esp_default_mac=''
    data_type=''
    data_token=''
    
    #----------------------------------------------------------------------
    def __init__(self,station_no,bacth_no,esp_default_mac,data_type,data_token):
        """Constructor"""
        self.station_no = station_no
        self.bacth_no = bacth_no
        self.esp_default_mac = esp_default_mac
        self.data_type = data_type
        self.data_token = data_token
       

#----------------------------------------------------------------------
def main(sys_param):
    try:
        server_ip, port, station_no, bacth_no, esp_default_mac, data_type, data_token = sys_param[:7]
    except:
        print "error: input params error"
        sys.exit()
    pro_info = Production(station_no,bacth_no,esp_default_mac,data_type, data_token)
    tcp_Client(server_ip, int(port), pro_info)
    sys.exit()
    

if __name__ == "__main__": 
    if sys.argv[1].lower().find('debug') >= 0:
        DEBUG = 1    
    sys_param = sys.argv[1].split(",")  # store the input parameter  
    main(sys_param) 
    
"""
input params example:
IP,PORT,STATION,BACTH_NO,DEF_MAC,DATA_TYPE,TOKEN
192.168.2.126,10000,CH,C0392,5C-CF-7F-F2-28-7a,custom_mac,OATG2Pf2Qw3afpm5kdoLCsB64CBpH941,bebug
"""
