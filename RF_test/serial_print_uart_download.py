import sys
import os.path
import time
import timeit
import serial
#from xtcom_interface import *
#import time_test
#import win32api
#import win32con




#if 1==uart_connect(3, 115200):
#    if 1==uart_sync()




def uartdownload(image_path="image/download.img"):
    #image_path = "image/download.img"
    connect_res = 0
    sync_res = 0
    com_port = get_port()
    while True:
        connect_res = uart_connect(com_port, 576000)
        
        if connect_res == 1:
            record_port(com_port)
            time.sleep(0.1)
            sync_res =  uart_sync()
            if sync_res == 1:
                break
            else:
                print("sync error...trying to connect again")
                uart_disconnect()
                time.sleep(0.1)
        
        
        
        else:
            print("trying to connect again")
            com_port=int(raw_input("Please enter the com_port number:(-1 to exit)"))
            #uart_disconnect()#error if added
            if -1==com_port:
                exit(0)
            #else:
                #pass
                #record_port(com_port)#for test
            
    time.sleep(0.1)##################
            

    #sync_res = 0
    #while True:
        ##time.sleep(0.1)
        #sync_res =  uart_sync()
        #if sync_res == 1:
            #break
        #else:
            #print("sync error ...")
            #uart_disconnect()
            #break


    if connect_res==1 and sync_res==1:
        time.sleep(0.1)##############################
        print("Start UartDownload...")
        
        
        uart_download(image_path)
        uart_disconnect()
        print("download disconnect...")
        
        
def get_serial_line(com_num,baudrate):
    log=""
    #print("test point 1...")
    ser=serial.Serial(com_num-1,baudrate,timeout=15)
    s=ser.readline()
    #print("test point 2...")
    #log+=s
    #print(s)#############################################
    #while not "cmd syntax error!" in s:
    while not "MODULE_TEST END" in s:
        log+=s
        #print(s)
        s=ser.readline()
        #log+=s
    print(s)
    log+=s
    if log=='':
        print("fail to get com...")
    
    #record_log_test(log,"record_line.txt")
    ser.close()
    return log

def test_get_serial(com,baud):
    ser=serial.Serial(com-1,baud,timeout=5)
    while True:
        line = ser.readline()
        print "test print: ",line

def get_serial_line_id(ser,start_flg,end_flg,sta_num=-1,retry=False,chip_type = "ESP8266",mode=0,wd='null'):
    log=""
    ver=''
    _id=''
    sleep_start=0
    sleep_flg=0
    ser.baudrate = 115200
    ser.timeout = 1
    if ser.isOpen() == False:
        ser.open()
    
    print "com num: ",ser.port
    print "baud rate:",ser.baudrate
    print "====================="
    print "RETRY:",retry,chip_type
    print "====================="
   # if retry:
    #if(wd.slot_num!='1'):
        #ser.flush()
        #raw_input("retry test...")
        #ser.write("esp_en_retest\r")
    if mode == 1:
        ser.write("esp_en_retest\r")
    else:
        ser.write('esp_set_flash_jump_start 1\r')
    #ser=serial.Serial(com_num-1,baudrate,timeout=10)
    #print "test ser.isopen: ",ser.isOpen
    try:
        s=ser.readline()
    except:
        return ''
    #s=''.join(s)
    print('test serial opened ...')
    
    #while not 'MODULE_TEST START!!!' in s:
    while not start_flg in s:        
        print "pres: ",s
        #ser.write('esp_set_flash_jump_start 1\r')
        try:
            s=ser.readline()
        except:
            return ''
        if s=='':
            print(3,'get_serial_line_id timeout....')
            
            break
    print("test point 2...")
    #log+=s
    #print(s)#############################################
    #while not "cmd syntax error!" in s:
    #while not "MODULE_TEST END" in s:
    while not s=='' and not end_flg in s:
        print("debug:",s)
        log+=s
        if 'CHIP_VERSION' in s:
            #ver=s[-5:-2]
            ver=s.split(':')[1].strip('\n\r').strip('\n').strip(' ')#130608 added to fit the chip id like 0x1001 (4 bits)
        if 'CHIP_ID' in s:
            #_id=s[-7:-2]
            _id=s.split(':')[1].strip('\n\r').strip('\n').strip(' ')#130608 added to fit the chip id like 0x1001 (4 bits)
        #print(s)
        if 'MODULE_TEST EDN' in s:
            sleep_start=1
        try:
            s=ser.readline()
        except:
            return ''
        if s=='':
            if sleep_start==1:
                sleep_flg=1
            print(3,'get_serial_line_id timeout....')
            
            break
        #log+=s
    #print(s)
    
    log+=s
    if s=='':
        if not chip_type == "ESP32":
            print("fail to get com...")
            log = ''
    
    #record_log_test(log,"record_line.txt")
    #if s=='' and not sleep_start==1:
        #log=''
    #ser.close()
    ser.flushInput()
    ser.flushOutput()
    #print ("get serial ok , but not close com")
    #print('test log :  ', log)
    return (log,ver,_id)


def get_serial_line_ser_test(ser,start_flg,end_flg,sta_num=-1):
    log=""
    ver=''
    _id=''
    sleep_start=0
    sleep_flg=0
    #print("test point 1...")
    #print "debug : delay 0.2s"
    #time.sleep(0.2)
    ser=serial.Serial(com_num-1,baudrate,timeout=1.2)
    #ser=serial.Serial(com_num-1,baudrate,timeout=10)
    s=ser.readline()
    print('test serial opened ...')
    
    #while not 'MODULE_TEST START!!!' in s:
    while not start_flg in s:
        print('test s : ' , s)
        
        s=ser.readline()
        if s=='':
            print('get_serial_line_id timeout....')
            break
    #print("test point 2...")
    #log+=s
    #print(s)#############################################
    #while not "cmd syntax error!" in s:
    #while not "MODULE_TEST END" in s:
    while not s=='' and not end_flg in s:
        #print(s)
        log+=s
        if 'CHIP_VERSION' in s:
            #ver=s[-5:-2]
            ver=s.split(':')[1].strip('\n\r').strip('\n').strip(' ')#130608 added to fit the chip id like 0x1001 (4 bits)
        if 'CHIP_ID' in s:
            #_id=s[-7:-2]
            _id=s.split(':')[1].strip('\n\r').strip('\n').strip(' ')#130608 added to fit the chip id like 0x1001 (4 bits)
        #print(s)
        if 'MODULE_TEST END' in s:
            sleep_start=1
        s=ser.readline()
        if s=='':
            if sleep_start==1:
                sleep_flg=1
            print('get_serial_line_id timeout....')
            break
        #log+=s
    #print(s)
    log+=s
    #if log=='':
        #print("fail to get com...")
    
    #record_log_test(log,"record_line.txt")
    #if s=='' and not sleep_start==1:
        #log=''
    ser.close()
    #print('test log :  ', log)
    return (log,ver,_id)





def record_log_test(ser,path,filename,tool_version = ''):
    #path='logs'
    if os.path.exists(path):
        #if 1==os.path.isfile(os.path.join(path,filename)):
            #win32api.SetFileAttributes(os.path.abspath(os.path.join(path,filename)) , win32con.FILE_ATTRIBUTE_NORMAL)
        f = open(os.path.join(path,filename), "a")
        #print(os.path.abspath(os.path.join(path,filename)))
        if tool_version == '':
            f.write(ser)
        else:
            f.write(tool_version+"\r\n"+ser)
        f.close()
        del f
        # to make the file readonly:
        #win32api.SetFileAttributes(os.path.abspath(os.path.join(path,filename)) , win32con.FILE_ATTRIBUTE_READONLY)        

    else:
        print("folder does not exist...")

        
           
        
        
#def get_serial3(com_num,baudrate):
    ##connected=0
    
    #ser=serial.Serial(com_num-1,baudrate,timeout=5.85)
  
    #s=ser.read(25000)
    #record_log_test(s,"test_log.txt")
    #ser.close()
    

#def get_serial(com_num,baudrate):
    ##connected=0
    #ser=serial.Serial(com_num-1,baudrate)
    #str1=ser.read(1000)
    #lines = str1.split('\n')
    #ser.close()
    #for s in lines:
        #print (s.strip())
        #fields = s.strip().split(',')
        #if not "DC" in fields[0]:
            #values=[]
            #for i in fields[1:]:    
                #try:
                    #values.append(float(i))
                #except:
                    #print(i)
        #else:
            #values = []
            #for i in ','.join(fields[1:]).split(';'):
                #values2 = []
                #for j in i.split(','):
                    #try:
                        #values2.append(float(j))
                    #except:
                        #print ("failed to decode: %s" % j)
                #values.append(values2)
        #print(fields[0], values)
        #if fields[0]=='RX_GAIN_CHECK':
            ## Check thresholds for RX_GAIN_CHECK
            #upper_limit = [1,3,3,3,3,3,3,3,3,3,3,3,3,3,3]
            #lower_limit = [-1,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3]
            #for i in range(len(values)):
                #if values[i]>upper_limit[i] or values[i]<lower_limit[i]:
                    #print "PART FAILURE IN %s #%i : [ %s !> %s !> %s ]" % (fields[0], i+1, str(upper_limit[i]), str(values[i]), str(lower_limit[i]))
    
        

def get_port():
    path='port_number_record/port.txt'
    
    if os.path.isfile(path):
        print('com_port record exists..')
        f=open(path,"r")
        com_port=int(f.readline())
        #print(com_port)
        #print(type(com_port))
        f.close()
        del f
        #_read.close()
        return com_port
        
    else:
        print(''' %s com_port record do not exist.'''%path)
        com_port = int(raw_input("Please enter the com_port number:"))
        return com_port

def record_port(com_port):
    path='port_number_record'
    
    if os.path.exists(path):
        f = open(os.path.join(path,"port.txt"), "w")
        f.write(str(com_port))
        f.close()
        del f

    else:
        print("port record folder does not exist...")

def uart_download_time_test(port=3,num=1):
    t = timeit.Timer("xtcom_interface.uart_connect(%d,%d)"%(port,576000) ,"import xtcom_interface")
    print("uart_connect()  takes :  ", t.timeit(num), "sec")
    time.sleep(0.1)
    t = timeit.Timer("xtcom_interface.uart_sync()"  ,"import xtcom_interface")
    print("uart_sync()  takes :  ", t.timeit(num), "sec")
    time.sleep(0.1)
    t = timeit.Timer("xtcom_interface.uart_download()"  ,"import xtcom_interface")
    print("uart_download()  takes :  ", t.timeit(num), "sec")
    t = timeit.Timer("xtcom_interface.uart_disconnect()"  ,"import xtcom_interface")
    print("uart_disconnect()  takes :  ", t.timeit(num), "sec")
        
if __name__ == '__main__':

    #uartdownload()
    #flag=''
    #while flag=='':
    #uart_download_time_test(3,1)
    flg=''
    while flg=='':
        
        uartdownload()
        #time.sleep(0.3)
        
        #com_port=get_port()
        #log=get_serial_line(com_port,115200)
        
        ## to make the file readonly:
        #win32api.SetFileAttributes("logs/record_line.txt" , win32con.FILE_ATTRIBUTE_NORMAL)        
        
        #record_log_test(log,'logs',"record_line.txt")   
        #print("serial port log recorded...")
        
        flag=raw_input('Press enter to continue downloading, Press any key followed by enter to exit')
    
    
    
    
    

