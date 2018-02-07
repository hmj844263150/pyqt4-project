import serial
import time


def uart_send_command(ser,cmd_str,pattern,ser_tout = 1,delay = 1, baud = None):
    if not ser.isOpen():
        #return (False,None)
        ser.open()
    if not baud == None:
        print "set new baud: ", baud
        ser.baudrate = baud
        
        
    #ser.flush()
    #ser.flushInput()
    #ser.setTimeout(ser_tout)
    #ser.timeout = ser_tout
    #print("set timeout: ", ser_tout)
    #ser.setTimeout(0.5)
    ser.timeout = 0.5
    print("set timeout: ", 0.5)    
    start_time = time.time()

    if not cmd_str == '':
        ser.write(cmd_str+"\r")
    #ser.flush()
    
    if pattern == None:
        return (True,None)
    while True:
        line = ser.read(1024)
        print "debug line:",line
        
        if pattern.upper() in line.upper():
            #ser.close()
            return (True,line)  
        elif line == '':
            ser.close()
            return (False,None)
        else:
            pass
        if delay>0:
            time.sleep(delay)
        if time.time() - start_time >= ser_tout:
            return (False, None)
    pass

def check_chip_keep_alive(ser,frame=None,at_mode = False):
    if not at_mode:
        cmd_str = "esp_read_mac"
        pattern = "mac:"
    else:
        cmd_str = "AT+GMR\r\n"
        pattern = "AT version:"
    ser_tout = 0.5
    #time.sleep(0.1)
    ser.open
    retry = 0
    while True and retry<3:
        res,line = uart_send_command(ser,cmd_str,pattern,ser_tout,0.1)
        if res:
            pass
        else:
            print "chip not ack"
            retry+=1
            
            #break
        
        if not frame == None:
            #retry += 1  #enable the program run
            try:
                if frame.STOP_FLG == 1:
                    print "break"
                    break
            except:
                print "frame stop flg error"
                #try:
                    #ser.close()
                #except:
                    #pass
                return
                #break
    
    ser.close()
        
        
def redo_rf_test(ser):
    ser.flush()
    ser.flushInput()
    cmd_str = "esp_en_retest"
    pattern = None
    ser_tout = 1
    res,line = uart_send_command(ser,cmd_str,pattern,ser_tout,0)
    ser.close()
        



if __name__ == "__main__":
    #ser = serial.Serial(port="COM6", baudrate=115200,timeout=1)
    #cmd_str = "esp_read_mac"
    #pattern = "mac:"
    #res,line = uart_send_command(ser,cmd_str,pattern,ser_tout = 1)
    #if res:
        #print "res:",line
    #else:
        #print "err"
    
    ser = serial.Serial(port="COM6", baudrate=115200,timeout=1)
    #check_chip_keep_alive(ser)    
    
    redo_rf_test(ser)
    