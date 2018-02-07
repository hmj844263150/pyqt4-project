import sys
import os
import time
import re

esp_logstr=''
rptstr='TESTITEM'+','+'TESTVALUE'+','+'SPEC_L'+','+'SPEC_H'+','+'RESULT'+'\n'

testitem=['FREQ_OFFSET',
      'TX_POWER_BACKOFF',
      'FB_RX_NUM',
      'DUT_RX_NUM',
      'TX_VDD33_DIFF',
      'RX_NOISEFLOOR',
      'TXIQ',
      'TXDC',
      'RXIQ',
      'RXDC',
      'RSSI_DIFF',
      'VDD33',
      'TOUT'
]

item_thres_h_dict={'FREQ_OFFSET':'0x11111111',
                   'TX_POWER_BACKOFF':'0x11111111',
                   'FB_RX_NUM':'98',
                   'DUT_RX_NUM':'98',
                   'TX_VDD33_DIFF':'300',
                   'RX_NOISEFLOOR':'-345',
                   'TXIQ':'0x1111',
                   'TXDC':'124',
                   'RXIQ':'0x1111',
                   'RXDC':'384',
                   'RSSI_DIFF':'10',
                   'VDD33':'4000',
                   'TOUT':'65535'
}                   

item_thres_l_dict={'FREQ_OFFSET':'0x00000000',
                   'TX_POWER_BACKOFF':'0x00000000',
                   'FB_RX_NUM':'48',
                   'DUT_RX_NUM':'48',
                   'TX_VDD33_DIFF':'-100',
                   'RX_NOISEFLOOR':'-405',
                   'TXIQ':'0x0000',
                   'TXDC':'3',
                   'RXIQ':'0x0000',
                   'RXDC':'128',
                   'RSSI_DIFF':'-10',
                   'VDD33':'3000',
                   'TOUT':'10'
} 

       
        
def rpt_append(item,value):
    testitem_str=str_format(testitem[item])
    if(eval(value)>eval(item_thres_h_dict[testitem[item]])) or (eval(value)<eval(item_thres_l_dict[testitem[item]])):
        res='FAIL'
    else:
        res='PASS'
    value_str=value
    spec_l_str=str_format(item_thres_l_dict[testitem[item]])
    spelc_h_str=str_format(item_thres_h_dict[testitem[item]])
    res_str=str_format(res)
    
    tempstr=testitem_str+','+value_str+','+spec_l_str+','+spelc_h_str+','+res_str+'\n'
    global rptstr
    rptstr=rptstr+tempstr
    return rptstr    
 
def str_format(value):
  
    if(isinstance(value,str)):
        value=value
  
    else:
        value=str(value)
    re_filling=20
    fill_num=re_filling-len(value)
    re_fill_str=' '
    re_fill_str=re_fill_str*fill_num
    re_fill_str=value+re_fill_str
    
    return re_fill_str
def esp_gen_rpt(tool_ver,chip_type,fac_,po,mac,res,rptstr):
    _path='C:/ESP_REPORT'   
    timestr=time.strftime('%Y-%m-%d-%H-%M',time.localtime(time.time()))
    try:
        if(not os.path.exists(_path)):
            #os.makedirs('C:\\ESP_REPORT\\'+po+'__'+res+mac+timestr)
            os.makedirs(_path)
        os.chdir(_path)
        
        filename=po+'__'+res+mac+timestr+'.csv'
        title_str='********************-----ESP MODULE TEST REPORT-----********************'+'\r\n'
        ver_str='TEST TOOL VERSION:'+tool_ver+'\r\n'
        chip_str='CHIP TYPE:'+chip_type+'\r\n'
        fac_str='FACTORY:'+fac_+'\r\n'
        title=title_str+ver_str+chip_str+fac_str
        rptstr=title+rptstr
        with open(filename,'a') as fn:
                fn.write(rptstr)
    except:
        print 'esp report creat error'
        


"""
esp print type definition:
type 0 means normal print
type 1 means parameter input
type 2 means parameter output,eg,test value in reg..
type 3 means debug print,eg,some import information for debug read

"""     
def l_print(print_type=0,logpath='',log_str=''):
    esp_logpath=logpath
    try:
        if(print_type==0):
            temp_str=log_str+'\r\n'
            
            with open(esp_logpath,'a') as fn:
                fn.write(temp_str)
            print(log_str)
        elif(print_type==1):
            temp_str='[para_in]:'+log_str+'\r\n'
           
            with open(esp_logpath,'a') as fn:
                fn.write(temp_str)
            print(log_str)
        elif(print_type==2):
            temp_str='[para_out]:'+log_str+'\r\n'
            
            with open(esp_logpath,'a') as fn:
                fn.write(temp_str)
            print(log_str)
        elif(print_type==3):
            temp_str='[debug]:'+log_str+'\r\n'
            with open(esp_logpath,'a') as fn:
                fn.write(temp_str)
            print(log_str)            
        
    except IOError:
        global esp_logstr
        esp_logstr=esp_logstr+temp_str

def esp_gen_log(mac,tool_ver,chip_type,fac_):
    logpath='..//logs//'
    timestr=time.strftime('%Y-%m-%d-%H-%M',time.localtime(time.time()))
    filename=mac+timestr+'.txt'
    logpath=logpath+filename
    title_str='********************-----ESP MODULE TEST LOG-----********************'+'\r\n'
    ver_str='TEST TOOL VERSION:'+tool_ver+'\r\n'
    chip_str='CHIP TYPE:'+chip_type+'\r\n'
    fac_str='FACTORY:'+fac_+'\r\n'
    title=title_str+ver_str+chip_str+fac_str  
    try:
        with open(logpath,'a') as fn:
            fn.write(title)
    except:
        logpath=''
        return logpath
    return logpath

def main1():
    item=1
    value='0x01000001'
    po='20180126'
    mac='AABBCCDDEEFF'
    res='PASS'
    item1=2
    value1='100'
    item2=5
    value2='0x0101'
    tool_ver="TOOL_VERSION: 5.5.1_RELEASE"
    chip_type='ESP32'
    fac_='XK'
    rptstr=rpt_append(item, value)
    rptstr=rpt_append(item1,value1)
    rptstr=rpt_append(item2,value2)
    esp_gen_rpt(tool_ver,chip_type,fac_,po,mac,res,rptstr)
    
def main():
    mac='AABBCCDDEEFF' 
    tool_ver="TOOL_VERSION: 5.5.1_RELEASE"
    chip_type='ESP32'
    fac_='XK'  
    logpath=esp_gen_log(mac, tool_ver, chip_type, fac_)
    image='FOR LOG DEMO TESTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT'
    l_print(0, logpath,'FOR LOG DEMO TEST')
    l_print(1, logpath,'image is %s'%image)
    l_print(2, logpath,'FOR LOG DEMO TESTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT')
    l_print(3, logpath,'FOR LOG DEMO TESTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT')
    
if __name__=='__main__':
    main()
    