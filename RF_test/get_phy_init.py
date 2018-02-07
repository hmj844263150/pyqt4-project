import xlrd
#import channel as chn
#import com
#import wifi
import time
import os
import sys





def init_data(data_list):
    
    #cmd_str="init_data"
    print "need to check this !!!!!!"
    print "in get_phy_init.py : init_data"
    cmd_str="init_data"
    for i in range(len(data_list)):
    #for i in range(32): 
        cmd_str+=" %d"%data_list[i]
        
    #print data_list
    print('cmd str  :  ',cmd_str)
    
    
    
    #result=chn.runcmd("init_data %d %d %d %d"%(d1,d2,d3,d4),chan_id='com')
    #result=chn.runcmd(cmd_str,chan_id='com')
    
    if ''!=result:
        print("true ... ")
        return True;
    else:
        print('false ... ')
        return False;   


def get_item_from_xls(fname='data_csv_130604.xlsx',item=''):
    
    
    
    line1=[]
  
    get1=0
 
    data=xlrd.open_workbook(fname)
    #table=data.sheet_by_name(sheetName) 
    table = data.sheets()[0]     
    col_num = table.ncols 
    
    
    if item=='':
        print("item error >>>")
        return -1
    else:
        if type(item)==type(1):
            if item<col_num and item>=0:
                line1=table.col_values(item ,start_rowx=1)
                return line1
            else:
                return -1
        elif type(item)==type(''):
            for j in range(table.ncols):
                if table.row_values(0)[j]==item:
                    line1=   table.col_values(j ,start_rowx=1)  
                    get1=1
                    return line1
                
            if get1==0:
                return -1
                
        else:
            print("unexcepted input...")
            return -1
        
        
        #if type(item2)==type(1):
            #if item2<col_num and item2>=0:
                #line1=table.col_values(item2 ,start_rowx=1)
            #else:
                #return -1
        #elif type(item2)==type(''):
            #for j in range(table.ncols):
                #if table.row_values(0)[j]==item2:
                    #line2=   table.col_values(j ,start_rowx=1)  
        #else:
            #print("unexcepted input...")
            #return -1
        
        
                
            
     
    
    
def get_init_list():
    line_signed=[]
    line=get_item_from_xls(fname='init_data/phy_6.0_init_param.xls',item='module_test')
    #print(type(line[0]))
    #print('test : ',type(line[0])==type(u''))
    for i in range(len(line)):
        if ( type(line[i])==type('') or type(line[i])==type(u'')  ) and '0x' in line[i]:
            line[i]=eval(line[i])
        elif line[i]<0:
            line[i]=512+line[i]
        line[i]=int(line[i])
            
            

            
    while len(line)<128:
        line.append(0)
    #print line
    return line

    

def post_init_data(comport=6,init_data_list=[],baudrate=115200):
    #list_step=128
    list_step=32

    
    
    line=init_data_list
    #print('test baudrate in post_init_data  :  %d '%baudrate)
    com.open(comport,br=baudrate)

    #print( "chip id is : %s "% wifi.rd_id() )
    start_idx=0
    end_idx=list_step
    data_list=line[start_idx:end_idx]
    #print data_list
    for i in range(4):
    #for i in range(1):
        init_data(data_list)
        start_idx+=list_step
        end_idx+=list_step
        data_list=line[start_idx:end_idx]
        #raw_input('enter to continue')
        
    com.close()
    
def get_config_para_dic(config_path):
    config_dict={}
    f=open(config_path,'r')
    lines=f.readlines()
    f.close()
    for line in lines:
        if not '//' in line[:5] and '#define' in line:
            ltmp=line.strip(' ').strip('\n\r').strip('\n').strip('\r').strip(' ')
            while '  ' in ltmp:
                ltmp=ltmp.replace('  ', ' ')
            if not ltmp=='':
                ltmp=ltmp.split(' ')
                if not len(ltmp)<=2:
                    if not ',' in ltmp[2]:
                        try:
                            if '.' in ltmp[2]:
                                config_dict[ltmp[1]]=float( ltmp[2] )
                            else:
                                config_dict[ltmp[1]]=int( ltmp[2] )
                        except:
                            #config_dict[ltmp[1]]=str( ltmp[2].lower() )
                            config_dict[ltmp[1]]=str( ltmp[2] )
                            
                        #print 'config_dict[%s]'%ltmp[1],'  ',config_dict[ltmp[1]],'  ',type(config_dict[ltmp[1]])
                    else:
                        config_dict[ltmp[1]]=[]
                        for item in ltmp[2].split(','):
                            if not item =='':
                                try:
                                    config_dict[ltmp[1]].append(int( item.strip(' ') ) )
                                except:
                                    #config_dict[ltmp[1]].append(str( item.strip(' ').lower() ) )
                                    config_dict[ltmp[1]].append(str( item.strip(' ') ) )
    
                
    #for key in config_dict.keys():
        #print key," : ",config_dict[key]," type : ",type(config_dict[key])
    return config_dict

def get_tx_rx_thresh():
    f=open('./config/tx_rx_thresh.csv')
    lines=f.readlines()
    f.close()
    tx_thresh={}
    rx_thresh={}
    freq_thresh={}
    
    for line in lines:
        ltmp=line.replace('\n','').replace(' ','')
        
        ltmp=ltmp.split(',')[1:]
        #print('test : ',ltmp)
        if 'rx' in line :
            rx_thresh[ltmp[0]]=int(ltmp[1])
        if 'tx' in line :
            tx_thresh[ltmp[0]]=   [float(ltmp[1]),float(ltmp[2])]
        if 'freq' in line:
            freq_thresh['freq_lower']=int( ltmp[0] )
            freq_thresh['freq_upper']=int( ltmp[1] )
            
    #print('test  : ',tx_thresh)
    #print('test  : ',rx_thresh)
        
    return (tx_thresh,rx_thresh,freq_thresh)
    


def get_mac_addr_from_table(filename):
    if os.path.isfile(filename):
        f= open(filename,'r')
        lines = f.readlines()
        f.close()
        for i in range(len(lines)):
            ltmp = ''+lines[i]
            if len(ltmp.split(','))>=2:
                mac = ltmp.split(',')[0]
                flg = ltmp.split(',')[1]
                print "get mac: ",mac, " type : ",type(mac)
                print "get flg: ",flg, " type : ",type(flg)
        pass
    else:
        print filename , " do not exist..."


if __name__=='__main__':
    get_mac_addr_from_table("./MAC_ADDR/MAC_SET_LIST.csv")
    
    
    
    
    
    
    #get_init_list()
    
    
    ###dic1=get_config_para_dic('config/settings.txt')
    ###for item in dic1.keys():
        ###print item , '   ' , dic1[item]
    
    ##l=get_init_list()
    ##while(1):
        ##go_on=raw_input('again?')
        ##if(go_on==''):
            ##post_init_data(6,l)
        ##else:
            ##break;
            
    #get_tx_rx_thresh()
        