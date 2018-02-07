import sys
import os
#import xlwt
import xlrd




csv_list=[               #item whose failed data will be put into a .csv 
                         
                         'dco_sweep_test_ADC_STEP',           
                         'RX_PATH_GAIN',
                         'RX_SWITCH_GAIN',
                         'TXIQ',
                         'TXBB_TXIQ',
                         'TXDC',
                         'FREQ_OFFSET',
                         'fb_rx_num_max',
                         'RXIQ_TEST_5M_diff',
                         'pass'
                         
                         
                         ]

judge_list=[             # check list: item in this list will be checked in the script
                         #the upper the more prioritized
                         'pass',
                         'dco_sweep_test_ADC_STEP',
                         'RX_PATH_GAIN',
                         'RX_SWITCH_GAIN',
                         'TXIQ',
                         'TXBB_TXIQ',
                         'TXDC',
                         'FREQ_OFFSET',
                         'fb_rx_num_max',
                         'RXIQ_TEST_5M_diff',
                         
                         #'VDD33',
                         #'FREQ_OFFSET',
                         #'rc_cal_dout',
                         #'filepath',
                         #'CHIP_ID',
                        #'CHIP_VERSION',
                        #'vdd33',
                        'VDD33',
                        'FREQ_OFFSET',
                        'rc_cal_dout',
                        'dco_sweep_test_ADC_STEP',
                        #'dco_sweep_test_DCO', 
                        'TXIQ',
                        'TXBB_TXIQ',
                        'TXDC',
                        #'TXBB_TXDC',##############################
                        'TXCAP_TMX2G_CCT_LOAD',
                        'TXCAP_PA2G_CCT_STG1',
                        'TXCAP_PA2G_CCT_STG2',   
                        'TX_PWRCTRL_ATTEN',
                        'TX_PWCTRL_CHAN_OFFSET',
                        'RX_PATH_GAIN',
                        'RX_PATH_SNR',    
                        'ADC_DAC_SNR',
                        'RX_SWITCH_GAIN',                
                        #'TXBB_TXDC',##############################
                        
                        ##=========================================================
                        'RX_GAIN_CHECK',
                        'BBRX2_RXIQ',
                        'RX_NOISEFLOOR',
                        'RXIQ',
                        'RXDC',
                        #'DVDD_testV1',
                        #'VDD_RTC_testV1',
                        #'DVDD_testV2' ,
                        #'VDD_RTC_testV2',
                        #'LightSleep_IDD_VBAT',
                        #'LightSleep_IDD_DVDD_IO',
                        #'DeepSleep_IDD_VBAT',
                        #'DeepSleep_IDD_DVDD_IO',
                        #'Chip_PD_IDD_VBAT',
                        #'Chip_PD_IDD_DVDD_IO',       
                        #'AnaWorkIDD_VBAT',
                        #'AnaWorkIDD_DVDD_IO'   , 
                        'RTC_freq_170khz',
                        'RTC_freq_70khz',
                        #'rssi',
                        #'rx_suc_num'  ,  
                        #'RXIQ_TEST_-5M',
                        #'RXIQ_TEST_5M', 
                        'RXIQ_TEST_5M_diff',
                        'rxiq_cover_fail_num',
                        #'rxiq_compute_num',
                        'rombist_rslt',
                        'timeout_fail', 
                        'site_num',
                        'RXIQ_REMAIN',
                        #'txp_pwctrl_atten',
                        'fb_rxrssi',
                        'dut_rxrssi',
                        #'fb_rx_num',
                        'fb_rx_num_max',
                        #'dut_rx_num',
                        'fb_rx_num_sum',
                        #'txp_state',
                        #'rxsdut_cnt',
                        #'rxsdut_max_rssi'   , 
                        #'txp_result',
                        #'txreq_start_time',
                        #'check_result_t',
                        'io_test_result',
                        'wifi_init_time',
                        #'WIFI_INIT_ITEM',
                        #'SVN_Version'                        
                             
                         
                         
                         ]





threshold={              #threshold for checking items
                          # 'name':[[lowlist,],[highlist,]]
                         'dco_sweep_test_ADC_STEP':[[0],[5]],
                         'RX_PATH_GAIN':[[40],[48]],
                         'RX_SWITCH_GAIN':[[1,-9,3],[4,-6,6]],
                         'TXIQ':[[-12,-25],[12,25]],
                         'TXBB_TXIQ':[[-6],[6]],
                         'TXDC':[[3],[124]],
                         'FREQ_OFFSET':[[0],[32]],
                         'fb_rx_num_max':[[15],[16]],
                         'RXIQ_TEST_5M_diff':[[-8],[8]] ,
                         
                         #'VDD33':[[],[]],  # ['VDD33', ' temp_code', ' offset']
                         #'FREQ_OFFSET':[[],[]],
                         #'rc_cal_dout'
                         #'filepath':[[],[]],
                         #'CHIP_ID':[[],[]],
                        #'CHIP_VERSION':[[],[]],
                        #'vdd33':[[3200,0,-1],[3600,116,0]],
                        'VDD33':[[3200,0,-100],[3600,180,0]],
                        #'FREQ_OFFSET':[[0],[32]],
                        'rc_cal_dout':[[3],[60]],
                        #'dco_sweep_test_ADC_STEP':[[0],[5]],#  ['_min_i', '_max_i', '_min_q', '_max_q']
                        #'dco_sweep_test_DCO':[[116,369,116,364],[147,397,145,395]],#['_low_i', '_hgh_i', '_low_q', '_hgh_q']
                        #'TXIQ':[[-12,-25],[12,25]], #['_gain', '_phase']
                        #'TXBB_TXIQ':[[-6],[6]],#['_gain', '_phase']
                        #'TXDC':[[3],[124]],#['_i', '_q']
                        #'TXBB_TXDC':[[],[]],##############################
                        'TXCAP_TMX2G_CCT_LOAD':[[0],[15]],
                        'TXCAP_PA2G_CCT_STG1':[[0],[12]],
                        'TXCAP_PA2G_CCT_STG2':[[0],[6]],   
                        'TX_PWRCTRL_ATTEN':[[-4,8,18,25,30,42],[26,30,38,47,53,63]],
                        'TX_PWCTRL_CHAN_OFFSET':[[-10],[10]],
                        'RX_PATH_GAIN':[[40],[48]],
                        'RX_PATH_SNR':[[25],[5000]],    
                        'ADC_DAC_SNR':[[34],[5000]],
                        'RX_SWITCH_GAIN':[[1,-9,3],[4,-6,6]],                
                        #'TXBB_TXDC',##############################
                        #======================================================
                        
                        'RX_GAIN_CHECK':[[16,-25,15,-4,-6,-4,5,-2,-2,-2,-2,-2,-2,-2],[24,-17,20,1,0,1,14,2,2,2,2,2,2,2]],
                        'BBRX2_RXIQ':[[-3],[3]],
                        'RX_NOISEFLOOR':[[-390],[-370]],
                        'RXIQ':[[-13,-27],[13,27]],
                        'RXDC':[[128],[384]],
                        #'DVDD_testV1':[[1.05],[1.2]],
                        #'VDD_RTC_testV1':[[],[]],
                        #'DVDD_testV2' :[[],[]],
                        #'VDD_RTC_testV2':[[],[]],
                        #'LightSleep_IDD_VBAT':[[],[]],
                        #'LightSleep_IDD_DVDD_IO':[[],[]],
                        #'DeepSleep_IDD_VBAT':[[],[]],
                        #'DeepSleep_IDD_DVDD_IO':[[],[]],
                        #'Chip_PD_IDD_VBAT':[[],[]],
                        #'Chip_PD_IDD_DVDD_IO':[[],[]],       
                        #'AnaWorkIDD_VBAT':[[],[]],
                        #'AnaWorkIDD_DVDD_IO'   :[[],[]], 
                        'RTC_freq_170khz':[[140],[210]],
                        'RTC_freq_70khz':[[60],[90]],
                        #'rssi':[[],[]],
                        #'rx_suc_num'  :[[],[]],  
                        #'RXIQ_TEST_-5M':[[-10,-31],[15,26]],
                        #'RXIQ_TEST_5M':[[-12,-21],[15,31]], 
                        'RXIQ_TEST_5M_diff':[[-8],[8]],
                        'rxiq_cover_fail_num':[[0],[0]],
                        #'rxiq_compute_num':[[0],[3]],
                        'rombist_rslt':[[0],[0]],
                        'timeout_fail':[[0,0,0],[1,1,0]], 
                        'site_num':[[0,1,1,0],[100,1,100,96]],
                        'RXIQ_REMAIN':[[-200],[-30]],
                        #'txp_pwctrl_atten':[[32],[96]],
                        'fb_rxrssi':[[0,0,0,0,0,40],[100,100,100,100,100,50]],
                        'dut_rxrssi':[[0,0,0,0,0,50],[100,100,100,100,100,60]],
                        #'fb_rx_num':[[0],[16]],
                        'fb_rx_num_max':[[15],[16]],
                        #'dut_rx_num':[[0],[16]],
                        'fb_rx_num_sum':[[64,0],[96,2]],
                        #'txp_state':[[],[]],
                        #'rxsdut_cnt':[[],[]],
                        #'rxsdut_max_rssi'   :[[],[]], 
                        #'txp_result':[[],[]],
                        #'txreq_start_time':[[],[]],
                        #'check_result_t':[[],[]],
                        'io_test_result':[[0],[0]],
                        'wifi_init_time':[[370000],[470000]],
                        #'WIFI_INIT_ITEM':[[],[]],
                        #'SVN_Version':[[4329],[4329]],                           
                         
        
        }







fail_dict_1st_order={ }
for litem in judge_list:
    fail_dict_1st_order[litem]=[0,[]]
    
                         #'dco_sweep_test_ADC_STEP':[0,[]],
                         #'RX_PATH_GAIN':[0,[]],
                         #'RX_SWITCH_GAIN':[0,[]],
                         #'TXIQ':[0,[]],
                         #'TXBB_TXIQ':[0,[]],
                         #'TXDC':[0,[]],
                         #'FREQ_OFFSET':[0,[]],
                         #'fb_rx_num':[0,[]],
                         #'RXIQ_TEST_-5M':[0,[]],
                         #'pass':[0,[]]
                         
                         #}



def read_log_data(file_path,mode,block_num):
    value_list=[]
    end_flg=''
    values={ 'rc_cal_dout': [[],[]],
              'rx_para_cal':[['_1','_2','_3'],[]],
             'CHIP_ID': [[''],[]],
                'CHIP_VERSION':[[''],[]],
                'TEST_NUM':[[],[]],
                'vdd33':[[],[]],
                'VDD33':[[],[]],
                'TX_VDD33':[[],[]],#add for new version
                'TX_VDD33_DIFF':[[''],[]],#add for new version
                'txp_result':[[],[]],#add for new version
                'TOUT':[[],[]],#ADD FOR TOUT TEST
                #'temp_code':[[],[]],
                #'offset':[[],[]],
                'cal_rf_ana_gain':[[],[]],
                #'TXBB_TXIQ_gain':[[],[]],
                #'TXBB_TXIQ_phase':[[],[]],
                'TXBB_TXIQ':[['_gain','_phase'],[ ]],
                #'TXBB_TXDC_i':[[],[]],
                #'TXBB_TXDC_q':[[],[]],
                'TXBB_TXDC':[['_i','_q'],[]],##############################
                'RX_GAIN_CHECK':[['_CH1','_CH6','_CH11'],[]],
                'RX_GAIN_CHECK_POWER_hdb':[['_1','_2'],[]],
                #'BBRX2_RXIQ_gain':[[],[]],
                #'BBRX2_RXIQ_phase':[[],[]],
                'BBRX2_RXIQ':[['_gain','_phase'],[]],
                'RX_NOISEFLOOR':[['_CH1','_CH6','_CH11'],[]],
                'TXCAP_TMX2G_CCT_LOAD':[[''],[]],
                'TXCAP_PA2G_CCT_STG1':[[''],[]],
                'TXCAP_PA2G_CCT_STG2':[[''],[]],
                'TX_POWER_BACKOFF':[[''],[]],#add for new version
                'TX_PWRCTRL_ATTEN':[[''],[]],
                'TX_PWCTRL_CHAN_OFFSET':[[''],[]],
                #'TXIQ_gain':[[],[]],
                #'TXIQ_phase':[[],[]],
                'TXIQ':[['_gain','_phase'],[]],
                'BT_TXIQ':[['_gain','_phase'],[]],
                #'TXDC_i':[[],[]],
                #'TXDC_q':[[],[]],
                'TXDC':[['_i','_q'],[]],
                'BT_TXDC':[['_i','_q'],[]],
                #'RXIQ_gain':[[],[]],
                #'RXIQ_phase':[[],[]],
                'RXIQ':[['_gain','_phase'],[]],
                
                #'RXDC_c_i':[[],[]],
                #'RXDC_c_q':[[],[]],
                #'RXDC_f_i':[[],[]],
                #'RXDC_f_q':[[],[]],
                'RXDC':[['_c_i','_c_q','_f_i','_f_q'],[]],
                'RXDC_RFRX_BT':[[],[]],
                'RXDC_RFRX_WIFI':[[],[]],
                'RXDC_RXBB_BT':[[],[]],
                
                #'freq_offset_cal_total_pwr':[[],[]],
                #'freq_offset_cal_bb_gain':[[],[]],
                'freq_offset_cal':[[],[]],
                'RX_PATH_GAIN':[[''],[]],
                'RXIQ_tot_power':[[''],[]],
                'FREQ_OFFSET':[[''],[]],
                'RX_PATH_SNR':[[''],[]],
                #'adc_dac_snr_2tone_gain':[[],[]],
                #'adc_dac_snr_2tone_total_pwr':[[],[]],
                'adc_dac_snr_2tone':[[],[]],
                'ADC_DAC_SNR':[[''],[]],
                #'rx_switch_gain_check_bbrx1':[[],[]],
                #'rx_switch_gain_check_bbrx2':[[],[]],
                #'rx_switch_gain_check_total_pwr_db':[[],[]],
                #'rx_switch_gain_check_sig_pwr_db':[[],[]],
                #'rx_switch_gain_check_sw_g':[[],[]],
                'rx_switch_gain_check':[['_bbrx1','_bbrx2','_total_pwr_db','_sig_pwr_db','_sw_g'],[]],#####################################
                'RX_SWITCH_GAIN':[[''],[]],#######################################
                'dco_sweep_test_ADC_STEP':[[],[]],
                'dco_sweep_test_DCO':[[],[]],
                'wi_pad 0 and ri_pad 4':[[],[]],
                'wi_pad 3 and ri_pad 5':[[],[]],
                'RTC_freq_170khz':[[''],[]],
                'RTC_freq_70khz':[[''],[]],    
                
                'DVDD_testV1':[[],[]], 
                'VDD_RTC_testV1':[[],[]], 
                'DVDD_testV2' :[[],[]], 
                'VDD_RTC_testV2':[[],[]], 
                'LightSleep_IDD_VBAT' :[[],[]], 
                
                'LightSleep_IDD_DVDD_IO':[[],[]], 
                'DeepSleep_IDD_VBAT':[[],[]], 
                'Chip_PD_IDD_VBAT':[[],[]],
                'Chip_PD_IDD_DVDD_IO':[[],[]],
                'DeepSleep_IDD_DVDD_IO' :[[],[]], 
                'AnaWorkIDD_VBAT':[[],[]], 
                'AnaWorkIDD_DVDD_IO':[[],[]],   
                'rssi':[[''],[]],
                'rx_suc_num':[[''],[]] ,  
                
                
                'RXIQ_TEST_-5M':[['_gain','_phase'],[]],
                'RXIQ_TEST_5M':[['_gain','_phase'],[]],
                
                'RXIQ_TEST_5M_diff':[['_gain','_phase'],[]],
                
                
                'rxiq_cover_fail_num':[[],[]],
                'rxiq_compute_num':[[''],[]],
                'rombist_rslt':[[],[]],
                'timeout_fail':[[],[]],
                'site_num':[[],[]],
                'RXIQ_REMAIN':[[''],[]],            # maintain IQ OR DC , print according to the name str in value[item] [0]
                
                
                'txp_pwctrl_atten':[[''],[]],
                'fb_rxrssi':[[''],[]],
                'dut_rxrssi':[[''],[]],
                'fb_rx_num':[[''],[]],
                'fb_rx_num_max':[[''],[]],
                
                
                'dut_rx_num':[[''],[]],
                
                'fb_rx_num_sum':[[],[]],
                
                
                'txp_state':[[''],[]],
                'rxsdut_cnt':[[''],[]],
                'rxsdut_max_rssi':[[''],[]],
                
                'txp_result':[[''],[]],
                'txreq_start_time':[[],[]],
                'check_result_t':[[],[]],
                'io_test_result':[[],[]],
                'wifi_init_time':[[''],[]],
                'WIFI_INIT_ITEM':[[''],[]],
                'SVN_Version':[[''],[]],
                
                
                'rx_para_cal_tone':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_1':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_2':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_3':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_4':[[''],[]],
                
                
                
                'filepath':'',
                'timer expire':''
                
                #'Light_sleep_RTC_freq_before':[[''],[]],
                #'Light_sleep_RTC_freq_after':[[''],[]]
                
                
                #'check_result':[[],[]],
                
                #'rssi':[[''],[]],
                #'rx_suc_num':[[''],[]]
                
                }   
    v_tmp={ 'rc_cal_dout': [[],[]],
            'rx_para_cal':[['_1','_2','_3'],[]],
            'CHIP_ID': [[''],[]],
                'CHIP_VERSION':[[''],[]],
                'TEST_NUM':[[],[]],
                'vdd33':[[],[]],
                'VDD33':[[],[]],
                'TX_VDD33':[[],[]],#add for new version
                'TX_VDD33_DIFF':[[''],[]],#add for new version
                'txp_result':[[],[]],#add for new version
                'TOUT':[[],[]],#ADD FOR TOUT TEST
                
                #'temp_code':[[],[]],
                #'offset':[[],[]],
                'cal_rf_ana_gain':[[],[]],
                #'TXBB_TXIQ_gain':[[],[]],
                #'TXBB_TXIQ_phase':[[],[]],
                'TXBB_TXIQ':[['_gain','_phase'],[ ]],
                #'TXBB_TXDC_i':[[],[]],
                #'TXBB_TXDC_q':[[],[]],
                'TXBB_TXDC':[['_i','_q'],[]],##############################
                'RX_GAIN_CHECK':[['_CH1','_CH6','_CH11'],[]],
                'RX_GAIN_CHECK_POWER_hdb':[['_ '],[]],
                #'BBRX2_RXIQ_gain':[[],[]],
                #'BBRX2_RXIQ_phase':[[],[]],
                'BBRX2_RXIQ':[['_gain','_phase'],[]],
                'RX_NOISEFLOOR':[['_CH1','_CH6','_CH11'],[]],
                'TXCAP_TMX2G_CCT_LOAD':[[''],[]],
                'TXCAP_PA2G_CCT_STG1':[[''],[]],
                'TXCAP_PA2G_CCT_STG2':[[''],[]],
                'TX_POWER_BACKOFF':[[''],[]],#add for new version
                
                'TX_PWRCTRL_ATTEN':[[''],[]],
                'TX_PWCTRL_CHAN_OFFSET':[[''],[]],
                #'TXIQ_gain':[[],[]],
                #'TXIQ_phase':[[],[]],
                'TXIQ':[['_gain','_phase'],[]],
                'BT_TXIQ':[['_gain','_phase'],[]],
                #'TXDC_i':[[],[]],
                #'TXDC_q':[[],[]],
                'TXDC':[['_i','_q'],[]],
                'BT_TXDC':[['_i','_q'],[]],
                #'RXIQ_gain':[[],[]],
                #'RXIQ_phase':[[],[]],
                'RXIQ':[['_gain','_phase'],[]],
                
                #'RXDC_c_i':[[],[]],
                #'RXDC_c_q':[[],[]],
                #'RXDC_f_i':[[],[]],
                #'RXDC_f_q':[[],[]],
                'RXDC':[['_c_i','_c_q','_f_i','_f_q'],[]],
                'RXDC_RFRX_BT':[[],[]],
                'RXDC_RFRX_WIFI':[[],[]],
                'RXDC_RXBB_BT':[[],[]],                
                #'freq_offset_cal_total_pwr':[[],[]],
                #'freq_offset_cal_bb_gain':[[],[]],
                'freq_offset_cal':[[],[]],
                'RX_PATH_GAIN':[[''],[]],
                'RXIQ_tot_power':[[''],[]],
                'FREQ_OFFSET':[[''],[]],
                'RX_PATH_SNR':[[''],[]],
                #'adc_dac_snr_2tone_gain':[[],[]],
                #'adc_dac_snr_2tone_total_pwr':[[],[]],
                'adc_dac_snr_2tone':[[],[]],
                'ADC_DAC_SNR':[[''],[]],
                #'rx_switch_gain_check_bbrx1':[[],[]],
                #'rx_switch_gain_check_bbrx2':[[],[]],
                #'rx_switch_gain_check_total_pwr_db':[[],[]],
                #'rx_switch_gain_check_sig_pwr_db':[[],[]],
                #'rx_switch_gain_check_sw_g':[[],[]],
                'rx_switch_gain_check':[['_bbrx1','_bbrx2','_total_pwr_db','_sig_pwr_db','_sw_g'],[]],#####################################
                'RX_SWITCH_GAIN':[[''],[]],#######################################
                'dco_sweep_test_ADC_STEP':[[],[]],
                'dco_sweep_test_DCO':[[],[]],
                'wi_pad 0 and ri_pad 4':[[],[]],
                'wi_pad 3 and ri_pad 5':[[],[]],
                'RTC_freq_170khz':[[''],[]],
                'RTC_freq_70khz':[[''],[]],  
                
                'DVDD_testV1':[[],[]], 
                'VDD_RTC_testV1':[[],[]], 
                'DVDD_testV2' :[[],[]], 
                'VDD_RTC_testV2':[[],[]], 
                'LightSleep_IDD_VBAT' :[[],[]], 
                
                'LightSleep_IDD_DVDD_IO':[[],[]], 
                'DeepSleep_IDD_VBAT':[[],[]], 
                'DeepSleep_IDD_DVDD_IO' :[[],[]], 
                'Chip_PD_IDD_VBAT':[[],[]],
                'Chip_PD_IDD_DVDD_IO':[[],[]],                
                'AnaWorkIDD_VBAT':[[],[]], 
                'AnaWorkIDD_DVDD_IO':[[],[]],   
                'rssi':[[''],[]],
                'rx_suc_num':[[''],[]]  ,                
                
                'RXIQ_TEST_-5M':[['_gain','_phase'],[]],
                'RXIQ_TEST_5M':[['_gain','_phase'],[]], 
                'RXIQ_TEST_5M_diff':[['_gain','_phase'],[]],
                
                'rxiq_cover_fail_num':[[],[]],
                'rxiq_compute_num':[[''],[]], 
                
                'rombist_rslt':[[],[]],
                'timeout_fail':[[],[]],     
                'site_num':[[],[]],
                'RXIQ_REMAIN':[[''],[]],
                
                'txp_pwctrl_atten':[[''],[]],
                'fb_rxrssi':[[''],[]],
                'dut_rxrssi':[[''],[]],
                'fb_rx_num':[[''],[]],
                'fb_rx_num_max':[[''],[]],
                'dut_rx_num':[[''],[]],
                
                'fb_rx_num_sum':[[],[]],
                
                
                'txp_state':[[''],[]],
                'rxsdut_cnt':[[''],[]],
                'rxsdut_max_rssi':[[''],[]],      
                
                'txp_result':[[''],[]],
                'txreq_start_time':[[],[]],
                'check_result_t':[[],[]],
                'io_test_result':[[],[]],
                'wifi_init_time':[[''],[]],
                'WIFI_INIT_ITEM':[[''],[]],
                'SVN_Version':[[''],[]],
                
                'rx_para_cal_tone':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_1':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_2':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_3':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_4':[[''],[]],                
                
                
                
                'filepath':'',
                'timer expire':''
                
                #'Light_sleep_RTC_freq_before':[[''],[]],
                #'Light_sleep_RTC_freq_after':[[''],[]],                
                ##'check_result':[[],[]],
                
                #'rssi':[[''],[]],
                #'rx_suc_num':[[''],[]]    
                

                } 
    
    if mode=='module':
        end_flg='TEST_NUM'
    elif mode=='ate_log':
        end_flg='---------------CHECK BOARD PASS'
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']  
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
    elif mode=='ate_0530_2noisefloor':
        end_flg='AnaWorkIDD_DVDD_IO'
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']
        values['RX_NOISEFLOOR'][0].pop()
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
        v_tmp['RX_NOISEFLOOR'][0].pop()     
    elif mode=='ate_0530_4noisefloor':
        end_flg='AnaWorkIDD_DVDD_IO'
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']
        values['RX_NOISEFLOOR'][0].append('_CH14')
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
        v_tmp['RX_NOISEFLOOR'][0].append('_CH14')
    elif mode=='ate_new':
        end_flg='---------------CHECK'  
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']
        values['RX_NOISEFLOOR'][0].append('_CH14')
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
        v_tmp['RX_NOISEFLOOR'][0].append('_CH14')
    elif mode=='module2515':
        #end_flg='MODULE_TEST END'
        end_flg='TEST_NUM'
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
        values['RX_NOISEFLOOR'][0].append('_CH14')
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
        v_tmp['RX_NOISEFLOOR'][0].append('_CH14')   
    elif mode=='ESP32':
        end_flg='MODULE_TEST EDN!!!'
        #end_flg='TEST_NUM'
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
        #values["BT_TXIQ"]=[['_gain','_phase'],[]]
        #values["BT_TXDC"]=[['_i','_q'],[]]        
        #values['RX_NOISEFLOOR'][0].append('_CH14')
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
        #v_tmp["BT_TXIQ"]=[['_gain','_phase'],[]]
        #v_tmp["BT_TXDC"]=[['_i','_q'],[]]
        #v_tmp['RX_NOISEFLOOR'][0]       
    elif mode=='ate' :
        end_flg='---------------CHECK'  
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']        
    elif mode=='130608_fpga' :
        #end_flg='user code done' 
        end_flg='rx_suc_num'
        #values['rc_cal_dout']= [[''],[]]
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']
        values['RX_NOISEFLOOR'][0].pop()  
        #v_tmp['rc_cal_dout']= [[''],[]]
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
        v_tmp['RX_NOISEFLOOR'][0].pop()  
    elif mode=='130624_fpga' :
        #end_flg='user code done' 
        end_flg='rxsdut_max_rssi'
        #values['rc_cal_dout']= [[''],[]]
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']
        values['RX_NOISEFLOOR'][0].pop()  
        #v_tmp['rc_cal_dout']= [[''],[]]
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
        v_tmp['RX_NOISEFLOOR'][0].pop()     
    elif mode=='130626_fpga' :
        #end_flg='user code done' 
        #end_flg='txp_state'
        #end_flg='AnaWorkIDD_DVDD_IO'
        #end_flg='txp_result'
        end_flg='txp_result'
        #values['rc_cal_dout']= [[''],[]]
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']
        values['RX_NOISEFLOOR'][0].pop()  
        #v_tmp['rc_cal_dout']= [[''],[]]
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
        v_tmp['RX_NOISEFLOOR'][0].pop()   
    elif mode =='ate130716':
        end_flg='AnaWorkIDD_DVDD_IO'
        #values['rc_cal_dout']= [[''],[]]
        values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']
        values['RX_NOISEFLOOR'][0].pop()  
        #v_tmp['rc_cal_dout']= [[''],[]]
        v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
        v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
        v_tmp['RX_NOISEFLOOR'][0].pop()           
        
        
    f=open(file_path,'r')
    lines=f.readlines()
    for line in lines:
        if 'site_num,' in line:
            line=line.replace(',','=').replace(';',',')
        elif 'dco_sweep_test_ADC_STEP' in line or 'dco_sweep_test_DCO' in line:
            line=line.replace(';',',')
        #elif 'rc_cal_dout' in line or 'RTC_freq_170khz' in line or 'RTC_freq_70khz' in line:
            #line=line.replace('=',',')
        elif 'RTC_freq_170khz' in line or 'RTC_freq_70khz' in line:
            line=line.replace('=',',')            
        elif 'rssi' in line or 'rx_suc_num' in line:
            line=line.replace(':',',')
        elif 'TOUT' in line:
            line = line.replace('=',',')
        line=line.replace(':',',').replace('PPM','').replace('us','').replace('dB','').strip('\n').strip('\n\r').strip(' ').strip(';').strip(',').split(',')
        if '=' in line[0]:
            line[0]=line[0].split('=')[0].strip(' ')+','+line[0]
            line=','.join(line)
            line=line.split(',')
        
        item=line[0]
        if item == "dut_rx_num" or item == "fb_rx_num" or item=="dut_rssi" or item=="fb_rssi":
            continue
        
        line=','.join(line[1:]).split(';')
        for i in range(len(line)):
            line[i]=line[i].split(',')
        if item in values.keys():
            #print "test item:", item,'\r\n'
            if item == "TX_VDD33":
                #print "test line: ",line,'\r\n'
                #print "values['vdd33'],",values['vdd33']
                if not values['vdd33'][1]==[]:
                    values['TX_VDD33_DIFF'][1].append([(values['vdd33'][1][0][0]-int(line[0][0].split('=')[1]))])
                else:
                    values['TX_VDD33_DIFF'][1].append([(3300-int(line[0][0].split('=')[1]))])
            if item == "TOUT":
                values['TOUT'][1].append(int(line[0][0]))
                #print "values tout:",values['TOUT']
            elif '=' in line[0][0]:
                line=line[0]
                v=[]
                for i in range(len(line)):
                    if '=' in line[i]:
                        line[i]=line[i].split('=')
                        values[item][0].append(line[i][0])
                        try:
                            #print "debug : LINE;"
                            #print line
                            v.append(int(line[i][1]))
                        except:
                            v.append(line[i][1])
                values[item][1].append(v)
            elif 'IQ' in item or 'DC' in item or 'rx_switch_gain_check'==item or 'RX_GAIN_CHECK_POWER_hdb'==item: #any line include ';'
                for j in range(len(line[0])):
                    v=[]
                    for k in range(len(line)):
                        v.append(line[k][j])
                    values[item][1].append(v)
            elif item=='timer expire':
                if 'pass' in line[0][0]:
                    value_list[-1][item]='pass'
                elif 'fail' in line[0][0]:
                    value_list[-1][item]='fail'
            elif item == 'TX_VDD33':
                print "item:",item
                print "line:",line,'\r\n'
            else:  
                values[item][1].append(line[0])
        if end_flg in item:
            if not values['CHIP_ID'][1]==[]:
                values['filepath']=file_path
            if not values['RXIQ_TEST_-5M'][1]==[] and not values['RXIQ_TEST_5M'][1]==[]:
                values['RXIQ_TEST_5M_diff'][1].append([   str( int(values['RXIQ_TEST_-5M'][1][0][0])-int(values['RXIQ_TEST_5M'][1][0][0]))     ])
                values['RXIQ_TEST_5M_diff'][1].append([   str( int(values['RXIQ_TEST_-5M'][1][1][0])-int(values['RXIQ_TEST_5M'][1][1][0]))     ])
            if not values['fb_rx_num'][1]==[]:
                values['fb_rx_num_max'][1].append(  [ str( max( [ int(d) for d in values['fb_rx_num'][1][0] ])    )]  )
            value_list.append(values)
                       
            values=v_tmp
            v_tmp={ 'rc_cal_dout': [[''],[]],
                    'rx_para_cal':[['_1','_2','_3'],[]],
                    'CHIP_ID': [[''],[]],
                'CHIP_VERSION':[[''],[]],
                'TEST_NUM':[[],[]],
                'vdd33':[[],[]],
                'VDD33':[[],[]],
                'TX_VDD33':[[],[]],#add for new version
                'TX_VDD33_DIFF':[[''],[]],#add for new version
                'txp_result':[[],[]],#add for new version
                'TOUT':[[],[]],#ADD FOR TOUT TEST
                
                'cal_rf_ana_gain':[[],[]],
                'TXBB_TXIQ':[['_gain','_phase'],[ ]],
                'TXBB_TXDC':[['_i','_q'],[]],##############################
                'RX_GAIN_CHECK':[['_CH1','_CH6','_CH11'],[]],
                'RX_GAIN_CHECK_POWER_hdb':[['_ '],[]],
                'BBRX2_RXIQ':[['_gain','_phase'],[]],
                'RX_NOISEFLOOR':[['_CH1','_CH6','_CH11'],[]],
                'TXCAP_TMX2G_CCT_LOAD':[[''],[]],
                'TXCAP_PA2G_CCT_STG1':[[''],[]],
                'TXCAP_PA2G_CCT_STG2':[[''],[]],
                'TX_POWER_BACKOFF':[[''],[]],#add for new version
                
                'TX_PWRCTRL_ATTEN':[[''],[]],
                'TX_PWCTRL_CHAN_OFFSET':[[''],[]],
                'TXIQ':[['_gain','_phase'],[]],
                'TXDC':[['_i','_q'],[]],
                'BT_TXIQ':[['_gain','_phase'],[]],
                'BT_TXDC':[['_i','_q'],[]],
                
                'RXIQ':[['_gain','_phase'],[]],
                'RXDC':[['_c_i','_c_q','_f_i','_f_q'],[]],
                'RXDC_RFRX_BT':[[],[]],
                'RXDC_RFRX_WIFI':[[],[]],
                'RXDC_RXBB_BT':[[],[]],                
                'freq_offset_cal':[[],[]],
                'RX_PATH_GAIN':[[''],[]],
                'FREQ_OFFSET':[[''],[]],
                'RXIQ_tot_power':[[''],[]],
                'RX_PATH_SNR':[[''],[]],
                'adc_dac_snr_2tone':[[],[]],
                'ADC_DAC_SNR':[[''],[]],
                'rx_switch_gain_check':[['_bbrx1','_bbrx2','_total_pwr_db','_sig_pwr_db','_sw_g'],[]],#####################################
                'RX_SWITCH_GAIN':[[''],[]],#######################################
                'dco_sweep_test_ADC_STEP':[[],[]],
                'dco_sweep_test_DCO':[[],[]],
                'wi_pad 0 and ri_pad 4':[[],[]],
                'wi_pad 3 and ri_pad 5':[[],[]],
                'RTC_freq_170khz':[[],[]],
                'RTC_freq_70khz':[[],[]],   
                
                'DVDD_testV1':[[],[]], 
                'VDD_RTC_testV1':[[],[]], 
                'DVDD_testV2' :[[],[]], 
                'VDD_RTC_testV2':[[],[]], 
                'LightSleep_IDD_VBAT' :[[],[]], 
                
                'LightSleep_IDD_DVDD_IO':[[],[]], 
                'DeepSleep_IDD_VBAT':[[],[]], 
                'DeepSleep_IDD_DVDD_IO' :[[],[]], 
                'Chip_PD_IDD_VBAT':[[],[]],
                'Chip_PD_IDD_DVDD_IO':[[],[]],                
                'AnaWorkIDD_VBAT':[[],[]], 
                'AnaWorkIDD_DVDD_IO':[[],[]],    
                'rssi':[[''],[]],
                'rx_suc_num':[[''],[]]  ,                  

                'RXIQ_TEST_-5M':[['_gain','_phase'],[]],
                'RXIQ_TEST_5M':[['_gain','_phase'],[]],
                'RXIQ_TEST_5M_diff':[['_gain','_phase'],[]],
                
                'rxiq_cover_fail_num':[[],[]],
                'rxiq_compute_num':[[''],[]],   
                'rombist_rslt':[[],[]],
                'timeout_fail':[[],[]],   
                'site_num':[[],[]],
                'RXIQ_REMAIN':[[''],[]],
                


                'txp_pwctrl_atten':[[''],[]],
                'fb_rxrssi':[[''],[]],
                'dut_rxrssi':[[''],[]],
                'fb_rx_num':[[''],[]],
                'fb_rx_num_max':[[''],[]],
                
                'dut_rx_num':[[''],[]],
                
                'fb_rx_num_sum':[[],[]],
                
                
                'txp_state':[[''],[]],
                'rxsdut_cnt':[[''],[]],
                'rxsdut_max_rssi':[[''],[]],  
                
                'txp_result':[[''],[]],
                'txreq_start_time':[[],[]],
                'check_result_t':[[],[]],
                'io_test_result':[[],[]],
                'wifi_init_time':[[''],[]],
                'WIFI_INIT_ITEM':[[''],[]],
                'SVN_Version':[[''],[]],
                
                'rx_para_cal_tone':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_1':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_2':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_3':[[''],[]],
                'rx_para_cal_tone_sig_pwr_db_4':[[''],[]],   
                'filepath':'',
                'timer expire':''
                } 
            
            
            if mode=='module':
                end_flg='TEST_NUM'
            elif mode=='ate_log':
                end_flg='---------------CHECK BOARD PASS'
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']                
            elif mode=='ate_new':
                end_flg='---------------CHECK'  
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']  
                v_tmp['RX_NOISEFLOOR'][0].append('_CH14')
            elif mode=='module2515':
                #end_flg='TEST_NUM'
                end_flg='TEST_NUM'
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
                v_tmp['RX_NOISEFLOOR'][0].append('_CH14')  
            elif mode=='ESP32':
                #end_flg='TEST_NUM'
                end_flg='MODULE_TEST EDN!!!'
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
                #v_tmp['RX_NOISEFLOOR'][0].append('_CH14')             
            elif mode=='ate' :
                end_flg='---------------CHECK'  
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
            elif mode=='ate_0530_2noisefloor':
                #end_flg='---------------CHECK'  
                end_flg='AnaWorkIDD_DVDD_IO'
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
                v_tmp['RX_NOISEFLOOR'][0].pop()
                
            elif mode=='ate_0530_4noisefloor':
                #end_flg='---------------CHECK'  
                end_flg='AnaWorkIDD_DVDD_IO'                
               
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q'] 
                v_tmp['RX_NOISEFLOOR'][0].append('_CH14')    
            elif mode=='130608_fpga' :
                end_flg='rx_suc_num'
                
                #v_tmp['rc_cal_dout']= [[''],[]]
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
                v_tmp['RX_NOISEFLOOR'][0].pop()               
            elif mode=='130624_fpga' :
                #end_flg='user code done' 
                end_flg='rxsdut_max_rssi'
                
                #v_tmp['rc_cal_dout']= [[''],[]]
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
                v_tmp['RX_NOISEFLOOR'][0].pop()   
            elif mode=='130626_fpga' :
                #end_flg='user code done' 
                end_flg='txp_state'
                
                #v_tmp['rc_cal_dout']= [[''],[]]
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
                v_tmp['RX_NOISEFLOOR'][0].pop()  
            elif mode =='ate130716':
                end_flg='AnaWorkIDD_DVDD_IO'
                #values['rc_cal_dout']= [[''],[]]
                #values['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                #values['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']
                #values['RX_NOISEFLOOR'][0].pop()  
                #v_tmp['rc_cal_dout']= [[''],[]]
                v_tmp['dco_sweep_test_ADC_STEP'][0]=['_min_i','_max_i','_min_q','_max_q']
                v_tmp['dco_sweep_test_DCO'][0]=['_low_i','_hgh_i','_low_q','_hgh_q']   
                v_tmp['RX_NOISEFLOOR'][0].pop()              
    return value_list


def sv_item_to_csv(_dict,mode,fname):
    if 'fpga' in mode or 'ate' in mode:
        ORDER_LIST=[ 'filepath',
                     'CHIP_ID',
                    'CHIP_VERSION',                    
                    'vdd33',
                    'VDD33',
                    'FREQ_OFFSET',
                    'rc_cal_dout',                                     
                    'dco_sweep_test_ADC_STEP',
                    'dco_sweep_test_DCO', 
                    'TXIQ',
                    'TXBB_TXIQ',
                    'TXDC',
                    'TXBB_TXDC',##############################
                    
                    'TXCAP_TMX2G_CCT_LOAD',
                    'TXCAP_PA2G_CCT_STG1',
                    'TXCAP_PA2G_CCT_STG2',   
                    'TX_PWRCTRL_ATTEN',
                    'TX_PWCTRL_CHAN_OFFSET',
                    'RX_PATH_GAIN',
                    
                    
                    'RX_PATH_SNR',    
                    'ADC_DAC_SNR',
                    
                    'RX_SWITCH_GAIN',                
                    #'TXBB_TXDC',##############################
                    'RX_GAIN_CHECK',
                    
                    'BBRX2_RXIQ',
                    'RX_NOISEFLOOR',
                    
                    
                    
                    
                    
                    'RXIQ',
                    'RXDC',
                    
                                     
                    
                    
                   
                    
                    
                    
                    'DVDD_testV1',
                    'VDD_RTC_testV1',
                    'DVDD_testV2' ,
                    'VDD_RTC_testV2',
                    'LightSleep_IDD_VBAT',
                    
                    'LightSleep_IDD_DVDD_IO',
                    'DeepSleep_IDD_VBAT',
                    'DeepSleep_IDD_DVDD_IO',
                    'Chip_PD_IDD_VBAT',
                    'Chip_PD_IDD_DVDD_IO',       
                    'AnaWorkIDD_VBAT',
                    'AnaWorkIDD_DVDD_IO'   ,    
                    
                    
                    'RTC_freq_170khz',
                    'RTC_freq_70khz',
                    'rssi',
                    'rx_suc_num'  ,   
                    
                    'RXIQ_TEST_-5M',
                    'RXIQ_TEST_5M', 
                    'RXIQ_TEST_5M_diff',
                    'rxiq_cover_fail_num',
                    'rxiq_compute_num',
                    'rombist_rslt',
                    'timeout_fail', 
                    'site_num',
                    'RXIQ_REMAIN',
                    
                    'txp_pwctrl_atten',
                    'fb_rxrssi',
                    'dut_rxrssi',
                    'fb_rx_num',
                    'fb_rx_num_max',
                    'dut_rx_num',
                    
                    'fb_rx_num_sum',
                    
                    
                    'txp_state',
                    'rxsdut_cnt',
                    'rxsdut_max_rssi'   , 
                    
                    'txp_result',
                    'txreq_start_time',
                    'check_result_t',
                    'io_test_result',
                    'wifi_init_time',
                    'WIFI_INIT_ITEM',
                    'SVN_Version',
                    
                    
                    'rx_para_cal_tone',
                    'rx_para_cal_tone_sig_pwr_db_1',
                    'rx_para_cal_tone_sig_pwr_db_2',
                    'rx_para_cal_tone_sig_pwr_db_3',
                    'rx_para_cal_tone_sig_pwr_db_4',                    
                    
                    'rx_para_cal',
                    
                    'cal_rf_ana_gain',
                    'TEST_NUM',
                    'RX_GAIN_CHECK_POWER_hdb',
                    'freq_offset_cal',
                    'RXIQ_tot_power',
                    'adc_dac_snr_2tone',
                    'rx_switch_gain_check',
                    'wi_pad 0 and ri_pad 4',
                    'wi_pad 3 and ri_pad 5'
                    
                                       
                    
                    
                    ]  
    else: # module
        ORDER_LIST=[ 'filepath',
                 'CHIP_ID',
                'CHIP_VERSION',
                
                'rc_cal_dout',
                'vdd33',
                'VDD33',
                
                'TXBB_TXIQ',
                'TXBB_TXDC',##############################
                'RX_GAIN_CHECK',
                
                'BBRX2_RXIQ',
                'RX_NOISEFLOOR',
                'TXCAP_TMX2G_CCT_LOAD',
                'TXCAP_PA2G_CCT_STG1',
                'TXCAP_PA2G_CCT_STG2',
                'TX_PWRCTRL_ATTEN',
                'TX_PWCTRL_CHAN_OFFSET',
                'TXIQ',
                'TXDC',
                'RXIQ',
                'RXDC',
                
                'RX_PATH_GAIN',
                'FREQ_OFFSET',
                
                'RX_PATH_SNR',
                
                'ADC_DAC_SNR',
                
                'RX_SWITCH_GAIN',
                'dco_sweep_test_ADC_STEP',
                'dco_sweep_test_DCO',
                
                
                
                'DVDD_testV1',
                'VDD_RTC_testV1',
                'DVDD_testV2' ,
                'VDD_RTC_testV2',
                'LightSleep_IDD_VBAT',
                
                'LightSleep_IDD_DVDD_IO',
                'DeepSleep_IDD_VBAT',
                'DeepSleep_IDD_DVDD_IO',
                'Chip_PD_IDD_VBAT',
                'Chip_PD_IDD_DVDD_IO',       
                'AnaWorkIDD_VBAT',
                'AnaWorkIDD_DVDD_IO'   ,    
                
                'cal_rf_ana_gain',
                'TEST_NUM',
                'RX_GAIN_CHECK_POWER_hdb',
                'freq_offset_cal',
                'RXIQ_tot_power',
                'adc_dac_snr_2tone',
                'rx_switch_gain_check',
                'wi_pad 0 and ri_pad 4',
                'wi_pad 3 and ri_pad 5',  
                'RTC_freq_170khz',
                'RTC_freq_70khz' ,
                
                'rssi',
                'rx_suc_num'  ,   
                
                'RXIQ_TEST_-5M',
                'RXIQ_TEST_5M',   
                'RXIQ_TEST_5M_diff',
                'rxiq_cover_fail_num',
                'rxiq_compute_num',  
                'rombist_rslt',
                'timeout_fail',   
                'site_num',
                'RXIQ_REMAIN',
                
                'txp_pwctrl_atten',
                'fb_rxrssi',
                'dut_rxrssi',
                'fb_rx_num',
                'fb_rx_num_max',
                'dut_rx_num',
                
                'fb_rx_num_sum',
                
                'txp_state',
                'rxsdut_cnt',
                'rxsdut_max_rssi'   ,
                'txp_result',
                'txreq_start_time',
                'check_result_t',
                'io_test_result',
                'wifi_init_time',
                'WIFI_INIT_ITEM',
                'SVN_Version',
                
                'rx_para_cal_tone',
                'rx_para_cal_tone_sig_pwr_db_1',
                'rx_para_cal_tone_sig_pwr_db_2',
                'rx_para_cal_tone_sig_pwr_db_3',
                'rx_para_cal_tone_sig_pwr_db_4',   
                
                'rx_para_cal'
                
                ]     
    a=open(fname,'w')
    
    cstr=''
    #print('len dictlist:',len(dict_list))
    #for i in range(len(dict_list)):
    #print('tttttttttt3')
    values=_dict
    #print('dco_sweep_test_ADC_STEP',values['dco_sweep_test_ADC_STEP'])
    #print('dco_sweep_test_DCO',values['dco_sweep_test_DCO'])
    #print('RTC_freq_170khz',values['RTC_freq_170khz'])
    
    #print('RTC_freq_70khz',values['RTC_freq_70khz'])
    
    
    for item in ORDER_LIST:
        #print('test item   :',item)
        #debug
        #print("""
        #=============================================================================
        #""")
        
        if item in values.keys():
            if type( values[item] ) ==type(''):
                #print(item , values[item] ) #debug
                cstr+=( values[item] + ',' )
            else:
                print(item,values[item])
                for nm in values[item][0]:
                    if not values[item][1]==[]:
                        if ( len(values[item][0])==len(values[item][1]) ):
                            for k in range(len(values[item][1][0])):
                                _str=item+nm+'_%d'%(k+1)
                                cstr+=(_str+',')
                        else:
                            _str=item+nm
                            cstr+=(_str+',')
                                       
    if not cstr=='':            
        cstr+='\n'
    
    
    a.write(cstr)
    a.close()
    del a
    
def sv_log_to_csv(dict_list,mode,fname):
    if 'fpga' in mode or 'ate' in mode:
        ORDER_LIST=[ 'filepath',
                     'CHIP_ID',
                    'CHIP_VERSION',
                    
                    
                    'vdd33',
                    'VDD33',
                    'FREQ_OFFSET',
                    'rc_cal_dout',
                    'dco_sweep_test_ADC_STEP',
                    'dco_sweep_test_DCO', 
                    'TXIQ',
                    'TXBB_TXIQ',
                    'TXDC',
                    'TXBB_TXDC',##############################
                    
                    'TXCAP_TMX2G_CCT_LOAD',
                    'TXCAP_PA2G_CCT_STG1',
                    'TXCAP_PA2G_CCT_STG2',   
                    'TX_PWRCTRL_ATTEN',
                    'TX_PWCTRL_CHAN_OFFSET',
                    'RX_PATH_GAIN',
                    
                    
                    'RX_PATH_SNR',    
                    'ADC_DAC_SNR',
                    
                    'RX_SWITCH_GAIN',                
                    
                    'RX_GAIN_CHECK',
                    
                    'BBRX2_RXIQ',
                    'RX_NOISEFLOOR',
                    
                    'RXIQ',
                    'RXDC',
                    
                    'DVDD_testV1',
                    'VDD_RTC_testV1',
                    'DVDD_testV2' ,
                    'VDD_RTC_testV2',
                    'LightSleep_IDD_VBAT',
                    
                    'LightSleep_IDD_DVDD_IO',
                    'DeepSleep_IDD_VBAT',
                    'DeepSleep_IDD_DVDD_IO',
                    'Chip_PD_IDD_VBAT',
                    'Chip_PD_IDD_DVDD_IO',             
                    'AnaWorkIDD_VBAT',
                    'AnaWorkIDD_DVDD_IO'   ,
                    
                    'RTC_freq_170khz',
                    'RTC_freq_70khz',
                    'rssi',
                    'rx_suc_num'  ,  
                    
                    
                    'RXIQ_TEST_-5M',
                    'RXIQ_TEST_5M',   
                    'RXIQ_TEST_5M_diff',
                    'rxiq_cover_fail_num',
                    'rxiq_compute_num',  
                    'rombist_rslt',
                    'timeout_fail',  
                    'site_num',
                    'RXIQ_REMAIN',
                    
                    'txp_pwctrl_atten',
                    'fb_rxrssi',
                    'dut_rxrssi',
                    'fb_rx_num',
                    'fb_rx_num_max',
                    'dut_rx_num',
                    
                    'fb_rx_num_sum',
                    
                    'txp_state',
                    'rxsdut_cnt',
                    'rxsdut_max_rssi'   ,  
                    'txp_result',
                    'txreq_start_time',
                    'check_result_t',
                    'io_test_result',
                    'wifi_init_time',
                    'WIFI_INIT_ITEM',
                    'SVN_Version',
                    
                    'rx_para_cal_tone',
                    'rx_para_cal_tone_sig_pwr_db_1',
                    'rx_para_cal_tone_sig_pwr_db_2',
                    'rx_para_cal_tone_sig_pwr_db_3',
                    'rx_para_cal_tone_sig_pwr_db_4',   
                    
                    'rx_para_cal',
                    
                    'cal_rf_ana_gain',
                    'TEST_NUM',
                    'RX_GAIN_CHECK_POWER_hdb',
                    'freq_offset_cal',
                    'RXIQ_tot_power',
                    'adc_dac_snr_2tone',
                    'rx_switch_gain_check',
                    'wi_pad 0 and ri_pad 4',
                    'wi_pad 3 and ri_pad 5'
                    ]      
    else:  #ate and module
        ORDER_LIST=[ 'filepath',
                     'CHIP_ID',
                    'CHIP_VERSION',
                    
                    'rc_cal_dout',
                    'vdd33',
                    'VDD33',
                    
                    'TXBB_TXIQ',
                    'TXBB_TXDC',##############################
                    'RX_GAIN_CHECK',
                    
                    'BBRX2_RXIQ',
                    'RX_NOISEFLOOR',
                    'TXCAP_TMX2G_CCT_LOAD',
                    'TXCAP_PA2G_CCT_STG1',
                    'TXCAP_PA2G_CCT_STG2',
                    'TX_PWRCTRL_ATTEN',
                    'TX_PWCTRL_CHAN_OFFSET',
                    'TXIQ',
                    'TXDC',
                    'RXIQ',
                    'RXDC',
                    
                    'RX_PATH_GAIN',
                    'FREQ_OFFSET',
                    
                    'RX_PATH_SNR',
                    
                    'ADC_DAC_SNR',
                    
                    'RX_SWITCH_GAIN',
                    'dco_sweep_test_ADC_STEP',
                    'dco_sweep_test_DCO',
                    
                    'DVDD_testV1',
                    'VDD_RTC_testV1',
                    'DVDD_testV2' ,
                    'VDD_RTC_testV2',
                    'LightSleep_IDD_VBAT',
                    
                    'LightSleep_IDD_DVDD_IO',
                    'DeepSleep_IDD_VBAT',
                    'DeepSleep_IDD_DVDD_IO',
                    'Chip_PD_IDD_VBAT',
                    'Chip_PD_IDD_DVDD_IO',      
                    'AnaWorkIDD_VBAT',
                    'AnaWorkIDD_DVDD_IO'   ,    
                    
                    'cal_rf_ana_gain',
                    'TEST_NUM',
                    'RX_GAIN_CHECK_POWER_hdb',
                    'freq_offset_cal',
                    'RXIQ_tot_power',
                    'adc_dac_snr_2tone',
                    'rx_switch_gain_check',
                    'wi_pad 0 and ri_pad 4',
                    'wi_pad 3 and ri_pad 5',  
                    'RTC_freq_170khz',
                    'RTC_freq_70khz',
                    'rssi',
                    'rx_suc_num'  , 
                    
                    'RXIQ_TEST_-5M',
                    'RXIQ_TEST_5M', 
                    'RXIQ_TEST_5M_diff',
                    'rxiq_cover_fail_num',
                    'rxiq_compute_num',   
                    'rombist_rslt',
                    'timeout_fail',    
                    'site_num',
                    'RXIQ_REMAIN',
                    
                    
                    'txp_pwctrl_atten',
                    'fb_rxrssi',
                    'dut_rxrssi',
                    'fb_rx_num',
                    'fb_rx_num_max',
                    'dut_rx_num',
                    
                    'fb_rx_num_sum',
                    
                    
                    'txp_state',
                    'rxsdut_cnt',
                    'rxsdut_max_rssi'  ,
                    'txp_result',
                    'txreq_start_time',
                    'check_result_t',
                    'io_test_result',
                    'wifi_init_time',
                    'WIFI_INIT_ITEM',
                    'SVN_Version',
                    
                    
                    'rx_para_cal_tone',
                    'rx_para_cal_tone_sig_pwr_db_1',
                    'rx_para_cal_tone_sig_pwr_db_2',
                    'rx_para_cal_tone_sig_pwr_db_3',
                    'rx_para_cal_tone_sig_pwr_db_4',  
                    
                    
                    'rx_para_cal'
                    ]         
    a=open(fname,'a')
    
    
    cstr=''
    for i in range(len(dict_list)):
        
        values=dict_list[i]
        #print("tttttttttttttttttttttttttttttt",type(values))
        
        
        #print("item rx_switch_gain_check",values['rx_switch_gain_check'])
        #print("vdd33 :   :",values['vdd33'])
        for item in ORDER_LIST:
            if item in values.keys():
                if type( values[item] )==type(''):
                    cstr+= ( values[item]+',' )
                else:
                    for lst in values[item][1]:
                        for num in lst:
                            try:
                                cstr+=(num+',')
                            except:
                                cstr+=(str(num)+',')
        if not cstr=='' and not values['CHIP_ID'][1]==[]:
            #print("test cstr   :",cstr)
            cstr+='\n'
            
            pass
        #print('cstr:',cstr)
        #cstr=''
    a.write(cstr)
    a.close()
    del a
                
                
        
        
        


def read_binary_log(file_path):
    offset=15
    f=open(file_path,'r')
    lines=f.readlines()
    #RG=['CHIP_ID','CHIP_VERSION','VDD33','temp_code','offset','cal_rf_ana_gain','TXBB_TXIQ_gain','TXBB_TXIQ_phase',
         #'TXBB_TXDC_i','TXBB_TXDC_q','RX_GAIN_CHECK','BBRX2_RXIQ_gain','BBRX2_RXIQ_phase','RX_NOISEFLOOR','TXCAP_TMX2G_CCT_LOAD',
         #'TXCAP_PA2G_CCT_STG1','TXCAP_PA2G_CCT_STG2','TX_PWRCTRL_ATTEN','TX_PWCTRL_CHAN_OFFSET','TXIQ_gain','TXIQ_phase',
         #'TXDC_i','TXDC_q','RXIQ_gain','RXIQ_phase','RXDC_c_i','RXDC_c_q','RXDC_f_i','RXDC_f_q','freq_offset_cal_total_pwr',
         #'freq_offset_cal_bb_gain','FREQ_OFFSET','RX_PATH_SNR','adc_dac_snr_2tone_gain','adc_dac_snr_2tone_total_pwr','ADC_DAC_SNR',
         #'rx_switch_gain_check_bbrx1','rx_switch_gain_check_bbrx2','rx_switch_gain_check_total_pwr_db','rx_switch_gain_check_sig_pwr_db',
         #'rx_switch_gain_check_sw_g','RX_SWITCH_GAIN','dco_sweep_test_ADC_STEP','dco_sweep_test_DCO','check_result'
         #]
    values={ 'CHIP_ID': [[1,5],'U32',0,[]],
             'CHIP_VERSION':[[5,6],'U8',0,[]],
             'VDD33':[[6,8],'U16',1,[]],
             'temp_code':[[8,9],'U8',1,[]],
             'offset':[[9,11],'S16',1,[]],
             'cal_rf_ana_gain':[[11,14],'U8',0,[]],
             'TXBB_TXIQ_gain':[[14,23],'S8',1,[]],
             'TXBB_TXIQ_phase':[[23,32],'S8',1,[]],
             'TXBB_TXDC_i':[[32,41],'S8',1,[]],
             'TXBB_TXDC_q':[[41,50],'S8',1,[]],
             'RX_GAIN_CHECK':[[50,92],'S8',1,[]],
             'BBRX2_RXIQ_gain':[[92,98],'S8',1,[]],
             'BBRX2_RXIQ_phase':[[98,104],'S8',1,[]],
             'RX_NOISEFLOOR':[[104,110],'S16',1,[]],
             'TXCAP_TMX2G_CCT_LOAD':[[110,113],'U8',1,[]],
             'TXCAP_PA2G_CCT_STG1':[[113,116],'U8',1,[]],
             'TXCAP_PA2G_CCT_STG2':[[116,119],'U8',1,[]],
             'TX_PWRCTRL_ATTEN':[[119,125],'S8',1,[]],
             'TX_PWCTRL_CHAN_OFFSET':[[125,139],'S8',1,[]],
             'TXIQ_gain':[[139,140],'S8',1,[]],
             'TXIQ_phase':[[140,141],'S8',1,[]],
             'TXDC_i':[[141,146],'U8',1,[]],
             'TXDC_q':[[146,151],'U8',1,[]],
             'RXIQ_gain':[[151,156],'S8',1,[]],
             'RXIQ_phase':[[156,161],'S8',1,[]],
             'RXDC_c_i':[[161,221],'U16',1,[]],
             'RXDC_c_q':[[221,281],'U16',1,[]],
             'RXDC_f_i':[[281,341],'U16',1,[]],
             'RXDC_f_q':[[341,401],'U16',1,[]],
             'freq_offset_cal_total_pwr':[[401,405],'U32',1,[]],
             'freq_offset_cal_bb_gain':[[405,406],'U8',1,[]],
             'FREQ_OFFSET':[[406,407],'S8',1,[]],
             'RX_PATH_SNR':[[407,409],'S16',1,[]],
             'adc_dac_snr_2tone_gain':[[409,412],'U8',1,[]],
             'adc_dac_snr_2tone_total_pwr':[[412,416],'U32',1,[]],
             'ADC_DAC_SNR':[[416,417],'U8',1,[]],
             'rx_switch_gain_check_bbrx1':[[417,427],'U16',0,[]],
             'rx_switch_gain_check_bbrx2':[[427,437],'U16',0,[]],
             'rx_switch_gain_check_total_pwr_db':[[437,442],'U8',1,[]],
             'rx_switch_gain_check_sig_pwr_db':[[442,447],'U8',1,[]],
             'rx_switch_gain_check_sw_g':[[447,452],'S8',1,[]],
             'RX_SWITCH_GAIN':[[452,455],'S8',1,[]],
             'dco_sweep_test_ADC_STEP':[[455,459],'S8',1,[]],
             'dco_sweep_test_DCO':[[459,467],'U16',1,[]],
             'check_result':[[467,471],'U32',0,[]]
             
             }
             
             
    #print('line0:',lines[0])
    v=''
    vl=[]
    counter=0
    m=2
    v2=''
    vt=[]
    for i in range(len(lines)):
        if lines[i]=='0\n':
            offset=i
            #print('maaaaaaaaaaaaaaa',i)
        for key in values.keys():
            if i in range(offset+values[key][0][0],offset+values[key][0][1]):
                v=lines[i].strip('\n')+v
                v2=v
                counter+=1
                if counter==int(values[key][1][1:])/8:
                    stmp=v
                    if values[key][1][0]=='U' and values[key][2]==1:
                        v=int(v,16)
                    elif (values[key][1][0]=='U' or values[key][1][0]=='S') and values[key][2]==0:
                        v='0x'+v
                    elif values[key][1][0]=='S' and values[key][2]==1:
                        vtmp=int(v,16)
                        if int(values[key][1][1:])==8:
                            m1=128
                            m2=256
                        elif int(values[key][1][1:])==16:
                            m1=32768
                            m2=65536
                        if vtmp>=m1:
                            v=vtmp-m2
                        else:
                            v=vtmp
                        
                    else:
                        print("uuuuuuuuuuuuuuuuuuuuuuuuuuunexpected///////")
                    
                            
                        
                        pass
                    print(stmp,'   ',v)
                    vl.append(v)
                    values[key][3].append(v)
                    vt.append(v2)
                    v=''
                    v2=''
                    counter=0
            else:
                pass
            
            if i==(offset+values[key][0][1]-1):
                vl=[]    
                vt=[]
                  
                
    
    return values


def read_threshold(sheetName='ATE',rowName='UPPER_RX_GAIN_CHECK',tname='Threshold.xlsx'):
    #sys.path.append("C:/Documents and Settings/Wang Jia Lin/Desktop/")
    line=[]
    re=-1
    data=xlrd.open_workbook(tname)
    sheetNames=data.sheet_names()
    if sheetName in sheetNames:
        table=data.sheet_by_name(sheetName)    
    
        col_0=table.col_values(0)
        for i in range( len(table.col_values(0) )):
            if col_0[i]==rowName:
                line=table.row_values(i)
                while(line[-1]==''):
                    line.pop()
                re=line[1:]
                break
                #ok find
        return re
            
            
def make_thresh():
    UPPER_RX_GAIN_CHECK=read_threshold(sheetName='ATE_fpga',rowName='UPPER_RX_GAIN_CHECK',tname='./Threshold/Threshold.xlsx')
    LOWER_RX_GAIN_CHECK=read_threshold(sheetName='ATE_fpga',rowName='LOWER_RX_GAIN_CHECK',tname='./Threshold/Threshold.xlsx')   
    UPPER_RX_NOISEFLOOR=read_threshold(sheetName='ATE_fpga',rowName='UPPER_RX_NOISEFLOOR',tname='./Threshold/Threshold.xlsx')
    LOWER_RX_NOISEFLOOR=read_threshold(sheetName='ATE_fpga',rowName='LOWER_RX_NOISEFLOOR',tname='./Threshold/Threshold.xlsx')    

    UPPER_TX_PWRCTRL_ATTEN=read_threshold(sheetName='ATE_fpga',rowName='UPPER_TX_PWRCTRL_ATTEN',tname='./Threshold/Threshold.xlsx')
    LOWER_TX_PWRCTRL_ATTEN=read_threshold(sheetName='ATE_fpga',rowName='LOWER_TX_PWRCTRL_ATTEN',tname='./Threshold/Threshold.xlsx')     
        
    UPPER_TX_PWCTRL_CHAN_OFFSET=read_threshold(sheetName='ATE_fpga',rowName='UPPER_TX_PWCTRL_CHAN_OFFSET',tname='./Threshold/Threshold.xlsx')
    LOWER_TX_PWCTRL_CHAN_OFFSET=read_threshold(sheetName='ATE_fpga',rowName='LOWER_TX_PWCTRL_CHAN_OFFSET',tname='./Threshold/Threshold.xlsx')     

    UPPER_TXIQ=read_threshold(sheetName='ATE_fpga',rowName='UPPER_TXIQ',tname='./Threshold/Threshold.xlsx')
    LOWER_TXIQ=read_threshold(sheetName='ATE_fpga',rowName='LOWER_TXIQ',tname='./Threshold/Threshold.xlsx')    
     
    UPPER_TXDC=read_threshold(sheetName='ATE_fpga',rowName='UPPER_TXDC',tname='./Threshold/Threshold.xlsx')
    LOWER_TXDC=read_threshold(sheetName='ATE_fpga',rowName='LOWER_TXDC',tname='./Threshold/Threshold.xlsx')      
    
    UPPER_RXIQ=read_threshold(sheetName='ATE_fpga',rowName='UPPER_RXIQ',tname='./Threshold/Threshold.xlsx')
    LOWER_RXIQ=read_threshold(sheetName='ATE_fpga',rowName='LOWER_RXIQ',tname='./Threshold/Threshold.xlsx')     
    
    UPPER_RXDC=read_threshold(sheetName='ATE_fpga',rowName='UPPER_RXDC',tname='./Threshold/Threshold.xlsx')
    LOWER_RXDC=read_threshold(sheetName='ATE_fpga',rowName='LOWER_RXDC',tname='./Threshold/Threshold.xlsx')     
  
    UPPER_FREQ_OFFSET=read_threshold(sheetName='ATE_fpga',rowName='UPPER_FREQ_OFFSET',tname='./Threshold/Threshold.xlsx')
    LOWER_FREQ_OFFSET=read_threshold(sheetName='ATE_fpga',rowName='LOWER_FREQ_OFFSET',tname='./Threshold/Threshold.xlsx') 
    
    UPPER_RX_PATH_SNR=read_threshold(sheetName='ATE_fpga',rowName='UPPER_RX_PATH_SNR',tname='./Threshold/Threshold.xlsx')
    LOWER_RX_PATH_SNR=read_threshold(sheetName='ATE_fpga',rowName='LOWER_RX_PATH_SNR',tname='./Threshold/Threshold.xlsx')     
    
    UPPER_ADC_DAC_SNR=read_threshold(sheetName='ATE_fpga',rowName='UPPER_ADC_DAC_SNR',tname='./Threshold/Threshold.xlsx')
    LOWER_ADC_DAC_SNR=read_threshold(sheetName='ATE_fpga',rowName='LOWER_ADC_DAC_SNR',tname='./Threshold/Threshold.xlsx')    
    
    data=xlrd.open_workbook('record.xlsx')
    table=data.sheet_by_name('record')  
    THR_L=[]
    THR_H=[]
    for col in range(table.ncols):
        THR_H.append(9999)
        THR_L.append(-9999)
        
    THR_H[44:58]=UPPER_RX_GAIN_CHECK
    THR_L[44:58]=LOWER_RX_GAIN_CHECK
    
    THR_H[58:72]=UPPER_RX_GAIN_CHECK
    THR_L[58:72]=LOWER_RX_GAIN_CHECK
    THR_H[72:86]=UPPER_RX_GAIN_CHECK
    THR_L[72:86]=LOWER_RX_GAIN_CHECK
    for ind in range(98,101):
        THR_H[ind]=UPPER_RX_NOISEFLOOR[0]
        THR_L[ind]=LOWER_RX_NOISEFLOOR[0]
    
    THR_H[110:116]=UPPER_TX_PWRCTRL_ATTEN
    THR_L[110:116]=LOWER_TX_PWRCTRL_ATTEN
    THR_H[116:130]=UPPER_TX_PWCTRL_CHAN_OFFSET
    THR_L[116:130]=LOWER_TX_PWCTRL_CHAN_OFFSET
    
    THR_H[130:132]=UPPER_TXIQ
    THR_L[130:132]=LOWER_TXIQ
    for ind in range(132,137):
        THR_H[ind]=UPPER_TXDC[0]
        THR_L[ind]=LOWER_TXDC[0]
    for ind in range(137,142):
        THR_H[ind]=UPPER_TXDC[1]
        THR_L[ind]=LOWER_TXDC[1]
    for ind in range(142,147):
        THR_H[ind]=UPPER_RXIQ[0]  
        THR_L[ind]=LOWER_RXIQ[0] 
    for ind in range(147,152):
        THR_H[ind]=UPPER_RXIQ[1] 
        THR_L[ind]=LOWER_RXIQ[1] 
        
        
        
    for ind in range(152,182):
        THR_H[ind]=UPPER_RXDC[0]  
        THR_L[ind]=LOWER_RXDC[0]
    for ind in range(182,212):
        THR_H[ind]=UPPER_RXDC[1]
        THR_L[ind]=LOWER_RXDC[1] 
    for ind in range(212,242):
        THR_H[ind]=UPPER_RXDC[2]
        THR_L[ind]=LOWER_RXDC[2]
    for ind in range(242,272):
        THR_H[ind]=UPPER_RXDC[3] 
        THR_L[ind]=LOWER_RXDC[3]
        
    THR_H[274:275]=UPPER_FREQ_OFFSET
    THR_L[274:275]=LOWER_FREQ_OFFSET
    
    
    THR_L[275:276]=LOWER_RX_PATH_SNR
    THR_L[280:281]=LOWER_ADC_DAC_SNR
    
    a=open('record.csv','w')
         
    wstr=''
    for n in THR_H:
    
        wstr+=(str(n)+',')
            
    wstr+='\n'
    a.write(wstr)    
    wstr=''
    for n in THR_L:
        
        wstr+=(str(n)+',')
                
    wstr+='\n'
    a.write(wstr)    
    wstr=''    
    a.close()
    del a
    
    
    return [[THR_H],[THR_L]]
    
        
        

#def judge_thr():
    #data=xlrd.open_workbook('record.xlsx')
    #table=data.sheets()[0]
    
    #nrows=table.nrows
    #ncols=table.ncols
    
    #for col in range(ncols):
        #ltmp=table.col_values(col)
        #thr_h=ltmp[0]
        #thr_l=ltmp[1]
        #values=ltmp[3:]
        
        #for i in range(len(values)):
            #if values[i]<thr_l or values[i]>thr_h:
                #table.put_cell(i+3,col,2,values[i],0)
                
    #table.put_cell(11,2,2,123456,1)
    
                
        
    
    #for col in range(table.ncols):
        #print("col: ",col, table.col_values(col))
        
        #clist=table.col_values(col)
        ##if 'RX_GAIN_CHECK' in clist:
            ##THR_H[44:
    

def make_csv():
    folder='ate'
    orderlist=['rc_cal_dout','CHIP_ID','CHIP_VERSION','VDD33','temp_code','offset','cal_rf_ana_gain','TXBB_TXIQ_gain','TXBB_TXIQ_phase',
         'TXBB_TXDC_i','TXBB_TXDC_q','RX_GAIN_CHECK','BBRX2_RXIQ_gain','BBRX2_RXIQ_phase','RX_NOISEFLOOR','TXCAP_TMX2G_CCT_LOAD',
         'TXCAP_PA2G_CCT_STG1','TXCAP_PA2G_CCT_STG2','TX_PWRCTRL_ATTEN','TX_PWCTRL_CHAN_OFFSET','TXIQ_gain','TXIQ_phase',
         'TXDC_i','TXDC_q','RXIQ_gain','RXIQ_phase','RXDC_c_i','RXDC_c_q','RXDC_f_i','RXDC_f_q','freq_offset_cal_total_pwr',
         'freq_offset_cal_bb_gain','FREQ_OFFSET','RX_PATH_SNR','adc_dac_snr_2tone_gain','adc_dac_snr_2tone_total_pwr','ADC_DAC_SNR',
         'rx_switch_gain_check_bbrx1','rx_switch_gain_check_bbrx2','rx_switch_gain_check_total_pwr_db','rx_switch_gain_check_sig_pwr_db',
         'rx_switch_gain_check_sw_g','RX_SWITCH_GAIN','dco_sweep_test_ADC_STEP','dco_sweep_test_DCO','check_result'
         ]
    th=make_thresh()
    THR_H=th[0]
    THR_L=th[1]
    flist=os.listdir(folder)
    print(flist)
    for i in range(len(flist)):
        
        filename=flist[i]
        if '.txt' in filename:
            fpath= folder+'/'+filename
            values=read_binary_log(fpath)
        print(fpath)
        if i==0:
            a=open('record.csv','a')
            
            wstr=''
            for kk in orderlist:
                if len(values[kk][3])==1:
                    wstr+=(kk+',')
                else:
                    for nn in range(len(values[kk][3])):
                        wstr+=(kk+"_%d"%nn+',')
                    
            wstr+='\n'
            a.write(wstr)
            wstr=''
            for kk in orderlist:
                if len(values[kk][3])==1:
                    wstr+=(str(values[kk][3][0])+',')
                else:
                    for nn in range(len(values[kk][3])):
                        wstr+=(str(values[kk][3][nn])+',')
                        
            wstr+='\n'
            a.write(wstr)  
            wstr=''
            
            a.close()
            del a    
        
        
        else:
            a=open('record.csv','a')
            for kk in orderlist:
                if len(values[kk][3])==1:
                    wstr+=(str(values[kk][3][0])+',')
                else:
                    for nn in range(len(values[kk][3])):
                        wstr+=(str(values[kk][3][nn])+',')
                        
            wstr+='\n'
            a.write(wstr)
            wstr=''
            a.close()
            del a             
        
        


def log_csv(ftype,folder,mode):
    if not os.path.isdir('./csv_files'):
        os.makedirs('./csv_files')
    log_flg_list=[]
    flist=os.listdir(folder)
    file_counter=0
    #cnttmp=0
    for ii in range(len(flist)):
        
        filename=flist[ii]
        if ftype in filename or ".txt" in filename:
            file_counter+=1
            
            fpath=folder+'/'+filename
            vl=read_log_data(fpath, mode)
            
            
            #====================================================================
            if 'ate' in mode or 'fpga' in mode:
                value_dict=vl[0]
                break_flg=0
                for item in judge_list:
                    
                    if item in value_dict.keys():                              #    
                        if item =='fb_rx_num_max':
                            #fb_rx_num_max=max([ float(data) for data in value_dict[item][1][0] ])
                            fb_rx_num_max=int( value_dict[item][1][0][0])
                            if fb_rx_num_max<threshold[item][0][0] or fb_rx_num_max>threshold[item][1][0]:
                                # print('failed in %s   ;  %s'%(item,filename) )
                                # print('%f  !< %f !< %f '%( float(threshold[item][0][0]),float(fb_rx_num_max),float(threshold[item][1][0])))
                                fail_dict_1st_order[item][0]+=1
                                fail_dict_1st_order[item][1].append(filename)
                                break_flg=1
                                break;      
                        elif item=='RXIQ_TEST_5M_diff':
                            #RXIQ_TEST_data_gain=float(value_dict['RXIQ_TEST_-5M'][1][0][0])-float(value_dict['RXIQ_TEST_5M'][1][0][0])
                            #RXIQ_TEST_data_phase=float(value_dict['RXIQ_TEST_-5M'][1][1][0])-float(value_dict['RXIQ_TEST_5M'][1][1][0])
                            RXIQ_TEST_data_gain=float(value_dict['RXIQ_TEST_5M_diff'][1][0][0])#-float(value_dict['RXIQ_TEST_5M_diff'][1][0][0])
                            RXIQ_TEST_data_phase=float(value_dict['RXIQ_TEST_5M_diff'][1][1][0])#-float(value_dict['RXIQ_TEST_5M_diff'][1][1][0])                            
                            if RXIQ_TEST_data_gain<threshold[item][0][0] or RXIQ_TEST_data_gain>threshold[item][1][0] or RXIQ_TEST_data_phase<threshold[item][0][0] or RXIQ_TEST_data_phase>threshold[item][1][0] :
                                # print('failed in %s   ;  %s'%(item,filename) )
                                # print('%f  !< %f !< %f '%( float(threshold[item][0][0]),float(RXIQ_TEST_data_gain),float(threshold[item][1][0])))
                                 #print('%f  !< %f !< %f '%( float(threshold[item][0][0]),float(RXIQ_TEST_data_phase),float(threshold[item][1][0])))
                                fail_dict_1st_order[item][0]+=1
                                fail_dict_1st_order[item][1].append(filename)
                                break_flg=1
                                break;                                 
                            
                        
                        elif len(threshold[item][0])==1 :  #[[1,2,3],[1,2,3]]   ;   [[1],[4]]
                            #if item=='ADC_DAC_SNR':
                                #cnttmp+=1
                            #judge
                            #print('error:3  ',item, value_dict[item]) #debug
                            #print(threshold[item])   #debug
                            for i in range(len(value_dict[item][1])):
                                for j in range(len(value_dict[item][1][i])):
                                    if float(value_dict[item][1][i][j])<float(threshold[item][0][0]) or float(value_dict[item][1][i][j])>float(threshold[item][1][0]):
                                        # print('failed in %s   ;  %s'%(item,filename) )
                                        # print('%f  !< %f !< %f '%( float(threshold[item][0][0]),float(value_dict[item][1][i][j]),float(threshold[item][1][0])))
                                        fail_dict_1st_order[item][0]+=1
                                        fail_dict_1st_order[item][1].append(filename)
                                        break_flg=1
                                        break;     
                                if break_flg==1:
                                    break
                            if break_flg==1:
                                break                        
                        
                        elif len(value_dict[item][1])==len(threshold[item][0]):  #[[5,5,5],[14,14,14]]  ; [[0,2],[8,15]]
                            #if len(value_dict[item][1][0])==len(threshold[item][0]):
                                
                                # print("""
                                # ===================================
                                # warning : 
                                
                                # n*n data detected 
                                # """)
                                 #print(item,value_dict[item])
                                 #print('===================================')
                                
                            #else:
                            #judge   num:1
                            
                            #print('error:1  ',item, value_dict[item]) #debug
                            #print(threshold[item])   #debug
                            for i in range(len(value_dict[item][1])):
                                
                                for j in range(len(value_dict[item][1][i])):
                                    if float( value_dict[item][1][i][j] ) < float( threshold[item][0][i] ) or float( value_dict[item][1][i][j]) > float(threshold[item][1][i]):
                                         #print('failed in %s   ;  %s'%(item,filename) )
                                         #print('%f  !< %f !< %f '%( float(threshold[item][0][i]),float(value_dict[item][1][i][j]),float(threshold[item][1][i])))
                                        fail_dict_1st_order[item][0]+=1
                                        fail_dict_1st_order[item][1].append(filename)
                                        break_flg=1
                                        break
                                if break_flg==1:
                                    break
                            if break_flg==1:
                                break
                                            
                                            #pass
                                               
                                    #pass
                                           
                                               
                                
                                #pass
                            
                        elif len(value_dict[item][1][0])==len(threshold[item][0]): #[[1,2,3,4],[1,2,3,4],[1,2,3,4]] ; [[1,1,1,1],[4,4,4,4]]
                            #judge
                            #judge   num:2
                            #print('error:2  ',item, value_dict[item]) #debug
                            #print(threshold[item])   #debug
                            for i in range(len(value_dict[item][1])):
                                for j in range(len(value_dict[item][1][i])):
                                    if float( value_dict[item][1][i][j])<float(threshold[item][0][j]) or float( value_dict[item][1][i][j]) > float(threshold[item][1][j]):
                                        #print('failed in %s   ;  %s'%(item,filename) )
                                         #print('%f  !< %f !< %f '%( float(threshold[item][0][j]),float(value_dict[item][1][i][j]),float(threshold[item][1][j])))
                                        fail_dict_1st_order[item][0]+=1
                                        fail_dict_1st_order[item][1].append(filename)
                                        break_flg=1
                                        break;  
                                if break_flg==1:
                                    break
                            if break_flg==1:
                                break
                            
                            
                            
                            
                            #pass
                        
                        #else:
                            #print('pass!')
                            
                                        
                                        
                            
                            #pass
                            
                    
                    
                    #pass
                    
                #pass
            
            
            
            
            
                if break_flg==0:
                    if not 'pass' in log_flg_list:
                        log_flg_list.append('pass')
                        sv_item_to_csv(vl[0],mode,'csv_files/data_PassKeyItem.csv')
                     #print("pass...")
                    fail_dict_1st_order['pass'][0]+=1
                    fail_dict_1st_order['pass'][1].append(filename)  
                    sv_log_to_csv(vl,mode,'csv_files/data_PassKeyItem.csv')
                else:
                    if item in csv_list:
                        if not item in log_flg_list:
                            log_flg_list.append(item)
                            sv_item_to_csv(vl[0],mode,'csv_files/data_fail_in_'+item+'.csv')
                        sv_log_to_csv(vl,mode,'csv_files/data_fail_in_'+item+'.csv')
                    if not 'fail' in log_flg_list:
                        log_flg_list.append('fail')
                        sv_item_to_csv(vl[0],mode,'csv_files/data_fail_altogether.csv')
                    sv_log_to_csv(vl,mode,'csv_files/data_fail_altogether.csv')
                    
                    
                    
            #====================================================================
            #print ('len vl:::',len(vl))
            if ii==0:
                
            
            
                #a=open('data_csv_all.csv','w')
                #print('test vl ,' ,vl)
                sv_item_to_csv(vl[0],mode,'csv_files/data_csv_all.csv')
                
            sv_log_to_csv(vl,mode,'csv_files/data_csv_all.csv')
    #print("---------------------failed item statistic---------------------------")
    #print('')
    f_str='item , fail_num , total_num , fail_rate \n'
    rate_list=[]
    fail_num_t=0
    for fitem in judge_list:
        
        if fitem in fail_dict_1st_order.keys() and not fitem in rate_list:
            rate_list.append(fitem)
            if not fitem == 'pass':
                fail_num_t+=int(fail_dict_1st_order[fitem][0])
            #print(fitem,'  ,  ',fail_dict_1st_order[fitem][0] )
            #print(fail_dict_1st_order[fitem][1])
            f_str+='%s , %d , %d , %f  \n'%(fitem,fail_dict_1st_order[fitem][0],file_counter,(fail_dict_1st_order[fitem][0]*1.0/file_counter) )
    f_str+="total fail, %d , %d, %f \n"%(fail_num_t,file_counter,(fail_num_t*1.0/file_counter) )
    #print('______________________________________________________________________')
    ff=open('csv_files/fail_rate.csv','w')
    ff.write(f_str)
    ff.close()
    #print('cnttmp:  ',cnttmp)
       
def data_process_dictList_2(dict_list,THRESHOLD_DICT,adc_en=1):  
    #print("adc_en:",adc_en)
    log='logs here: \n'
    r='pass'
    fail_list = []
    #====================================================================
    for i in range( len(dict_list)):
        value_dict=dict_list[i]
        break_flg=0
        #for item in judge_list:
        single_res = True
        
        for item in THRESHOLD_DICT.keys():
            if item in value_dict.keys() and not value_dict[item][1]==[]:  
                if item == "fb_rxrssi":
                    print('test 1 when item : ', item )
                    print('test 2 value item : ',value_dict[item])
                    print('test 3 threshold item: ', THRESHOLD_DICT[item])
                    
                if item == "TOUT":
                    if adc_en:
                        if value_dict[item][1][0]<THRESHOLD_DICT[item][0][0] or value_dict[item][1][0]>THRESHOLD_DICT[item][1][0]:
                            log+='Part failure in %s  : %d < %d < %d \n '%(item,THRESHOLD_DICT[item][0][0],value_dict[item][1][0],THRESHOLD_DICT[item][1][0])
                            fail_list.append(item)
                            single_res = False                        
                elif item == "RX_NOISEFLOOR":
                    val_tmp = [int(x[0].strip(" ")) for x in value_dict[item][1]]
                    if list(set(val_tmp))==[-340] or list(set(val_tmp))==[-392]:
                        log+='Part failure in %s  : %s \n '%(item,str(val_tmp))
                        fail_list.append(item)
                        single_res = False
                        
                elif item =='fb_rx_num_max':
                    fb_rx_num_max=int( value_dict[item][1][0][0])
                    if fb_rx_num_max<THRESHOLD_DICT[item][0][0] or fb_rx_num_max>THRESHOLD_DICT[item][1][0]:
                        log+='Part failure in %s  : %d !< %d !< %d \n '%(item,THRESHOLD_DICT[item][0][0],fb_rx_num_max,THRESHOLD_DICT[item][1][0])
                        fail_list.append(item)
                        single_res = False
                elif item=="TXDC":
                    txdc_i = [int(x) for x in value_dict[item][1][0]]
                    txdc_q = [int(x) for x in value_dict[item][1][1]]
                    txdc_i.sort()
                    txdc_q.sort()
                    if txdc_i[1]<THRESHOLD_DICT[item][0][0] or txdc_i[2]>THRESHOLD_DICT[item][1][0]:
                        log+='Part failure in %s_%s : %d %d %d %d  \n'%(item,'i',txdc_i[0],txdc_i[1],txdc_i[2],txdc_i[3])
                        single_res = False
                        fail_list.append(item)  
                        
                    if txdc_q[1]<THRESHOLD_DICT[item][0][0] or txdc_q[2]>THRESHOLD_DICT[item][1][0]:
                        log+='Part failure in %s_%s : %d %d %d %d  \n'%(item,'q',txdc_q[0],txdc_q[1],txdc_q[2],txdc_q[3])
                        single_res = False
                        fail_list.append(item)                                              
                    print "-----------------"
                elif item=='RXIQ_TEST_5M_diff':
                    RXIQ_TEST_data_gain=float(value_dict['RXIQ_TEST_5M_diff'][1][0][0])#-float(value_dict['RXIQ_TEST_5M_diff'][1][0][0])
                    RXIQ_TEST_data_phase=float(value_dict['RXIQ_TEST_5M_diff'][1][1][0])#-float(value_dict['RXIQ_TEST_5M_diff'][1][1][0])                            
                    if RXIQ_TEST_data_gain<THRESHOLD_DICT[item][0][0] or RXIQ_TEST_data_gain>THRESHOLD_DICT[item][1][0] or RXIQ_TEST_data_phase<THRESHOLD_DICT[item][0][0] or RXIQ_TEST_data_phase>THRESHOLD_DICT[item][1][0] :
                        log+='Part failure in %s    \n '%item
                        fail_list.append(item)
                        single_res = False
                
                elif len(THRESHOLD_DICT[item][0])==1 :  #[[1,2,3],[1,2,3]]   ;   [[1],[4]]
                    for i in range(len(value_dict[item][1])):
                        for j in range(len(value_dict[item][1][i])):
                            if float(value_dict[item][1][i][j])<float(THRESHOLD_DICT[item][0][0]) or float(value_dict[item][1][i][j])>float(THRESHOLD_DICT[item][1][0]):
                                log+='Part failure in %s  #%d,#%d : %f !< %f !< %f  \n'%(item,i,j,float(THRESHOLD_DICT[item][0][0]),float(value_dict[item][1][i][j]),float(THRESHOLD_DICT[item][1][0]))
                                single_res = False
                                fail_list.append(item)
                elif len(value_dict[item][1])==len(THRESHOLD_DICT[item][0]):  #[[5,5,5],[14,14,14]]  ; [[0,2],[8,15]]
                    for i in range(len(value_dict[item][1])):
                        
                        for j in range(len(value_dict[item][1][i])):
                            if float( value_dict[item][1][i][j] ) < float( THRESHOLD_DICT[item][0][i] ) or float( value_dict[item][1][i][j]) > float(THRESHOLD_DICT[item][1][i]):
                                log+='Part failure in %s  #%d,#%d  :  %f !< %f !< %f  \n '%(item,i ,j,float( THRESHOLD_DICT[item][0][i] ),float( value_dict[item][1][i][j]),float(THRESHOLD_DICT[item][1][i]))
                                single_res = False
                                fail_list.append(item)
                elif len(value_dict[item][1][0])==len(THRESHOLD_DICT[item][0]): #[[1,2,3,4],[1,2,3,4],[1,2,3,4]] ; [[1,1,1,1],[4,4,4,4]]
                    for i in range(len(value_dict[item][1])):
                        for j in range(len(value_dict[item][1][i])):
                            if float( value_dict[item][1][i][j])<float(THRESHOLD_DICT[item][0][j]) or float( value_dict[item][1][i][j]) > float(THRESHOLD_DICT[item][1][j]):
                                log+='Part failure in %s  #%d,#%d : %f !< %f !< %f  \n '%(item,i,j,float(THRESHOLD_DICT[item][0][j]),float( value_dict[item][1][i][j]),float(THRESHOLD_DICT[item][1][j]))
                                single_res = False
                                fail_list.append(item)
        if single_res == True:
            log+="single_chip passed\r\n"
    
    if not dict_list==[]:
        if dict_list[-1]['timer expire']=='pass' :
            pass
        else:
            #log+='light sleep test failed ! \n'######light sleep 
            pass
    else:
        log+='get test result print failed !\n '
        
    
    
    
    if 'Part failure' in log:
    #if not log=='logs here: \n':
        print('Failure Detected....')
        print(log)
                           
        
        return (False,log,fail_list)
    else:
        #print('Analog Test Passed\n\r')
        return (True,'Analog Test Passed\n\r',fail_list)   
    
    
def data_process_dictList(dict_list,THRESHOLD_DICT):# dict_list=[{},{},...],
                                                    #  THRESHOLD_DICT:{'item':[[upper],[lower]],...}
    log='logs here: \n'
   
   
    test_list1=['TXBB_TXIQ','BBRX2_RXIQ','TXIQ','TXDC','RXIQ','RXDC','dco_sweep_test_DCO','dco_sweep_test_ADC_STEP','wi_pad 0 and ri_pad 4','wi_pad 3 and ri_pad 5']
    r='pass'
    for i in range(len(dict_list)):                
        values=dict_list[i]
        #print(values['wi_pad 0 and ri_pad 4'])
        #print(values['wi_pad 3 and ri_pad 5'])
        print("""values['TXIQ'] : """,values['TXIQ'])
        print("""values['RXIQ'] : """,values['RXIQ'])
        THRESHOLD_DICT['TXBB_TXIQ'][0]=[ int(values['TXIQ'][1][0][0])+int(THRESHOLD_DICT['TXIQ_DIFF'][0][0]),int(values['TXIQ'][1][1][0])+int(THRESHOLD_DICT['TXIQ_DIFF'][0][1])]
        THRESHOLD_DICT['TXBB_TXIQ'][1]=[ int(values['TXIQ'][1][0][0])-int(THRESHOLD_DICT['TXIQ_DIFF'][1][0]),int(values['TXIQ'][1][1][0])-int(THRESHOLD_DICT['TXIQ_DIFF'][1][1]) ]
        print("""THRESHOLD_DICT['TXBB_TXIQ']""",THRESHOLD_DICT['TXBB_TXIQ'])
        THRESHOLD_DICT['BBRX2_RXIQ'][0]=[ int(values['RXIQ'][1][0][0])+int(THRESHOLD_DICT['RXIQ_DIFF'][0][0]),int(values['RXIQ'][1][1][0])+int(THRESHOLD_DICT['RXIQ_DIFF'][0][1]) ]
        THRESHOLD_DICT['BBRX2_RXIQ'][1]=[ int(values['RXIQ'][1][0][0])-int(THRESHOLD_DICT['RXIQ_DIFF'][1][0]),int(values['RXIQ'][1][1][0])-int(THRESHOLD_DICT['RXIQ_DIFF'][1][1]) ]
        print("""THRESHOLD_DICT['BBRX2_RXIQ']""",THRESHOLD_DICT['BBRX2_RXIQ'])
        for item in THRESHOLD_DICT.keys():
            #print('values[item]',item,values[item])
            if item=='vdd33':
                values[item][1][0]=[ values[item][1][0][0], ]
            if not item=='TXIQ_DIFF' and not item=='RXIQ_DIFF':
                v_tmp=values[item][1]
            if item in test_list1: 
                
                    
                for j in range(len(v_tmp)):
                    for k in range(len(v_tmp[j])):
                        if int( v_tmp[j][k] )<int( THRESHOLD_DICT[item][1][j] ) or int( v_tmp[j][k] )>int( THRESHOLD_DICT[item][0][j] ):
                            log+="Part Fail In %s #%i %s: [ %s !> %s !> %s ] \r\n"%(item,k+1,values[item][0][j],THRESHOLD_DICT[item][0][j],v_tmp[j][k],THRESHOLD_DICT[item][1][j])
                            #r="FAIL"
                pass
            #elif item=='timer expire':
                #print('test:',values[item])
                #if values[item]=='pass':
                    #log+='Part fail in light sleep test..'
            elif item=='RXIQ_DIFF' or item=='TXIQ_DIFF':
                pass
            else:
                for j in range(len(v_tmp)):
                    for k in range(len(v_tmp[j])):
                        
                        #print('item',item,'j:' , j , 'k:', k)
                        
                        if int( v_tmp[j][k] )<int( THRESHOLD_DICT[item][1][k] ) or int( v_tmp[j][k] )>int( THRESHOLD_DICT[item][0][k] ):
                            log+="Part Fail In %s #%i %s: [ %s !> %s !> %s ] \r\n"%(item,k+1,values[item][0][j],THRESHOLD_DICT[item][0][k],v_tmp[j][k],THRESHOLD_DICT[item][1][k])
                            #r="FAIL"
                pass
        if not log=='logs here: \n':
            log+='------------------------------TEST_NUM= %s ------------------------------\n'%values['TEST_NUM'][1][0][0]
        #print('3333333333333',values['timer expire'])
        if values['TEST_NUM'][1][0][0]==9 and (not values['timer expire']=='pass'):
            #print('3333333333333',values['timer expire'])
            log+='Part fail in light sleep test..'
    if not log=='logs here: \n':
        print('Failure Detected....')
        print(log)
                           
        
        return (False,log)
    else:
        print('Analog Test Passed \n\r')
        return (True,'Analog Test Passed \n\r')
            
def get_threshold_dict(sheetName='ATE',tname='Threshold.xlsx'):
    line=[]
    re=-1
    threshold_dict={}
    data=xlrd.open_workbook(tname)
    sheetNames=data.sheet_names()
    if sheetName in sheetNames:
        table=data.sheet_by_name(sheetName)    
    
        col_0=table.col_values(0)
        for i in range( len(table.col_values(0) )):
            if not col_0[i]=='':
                line=table.row_values(i)
                #print line
                
                
                while(line[-1]==''):
                    line.pop()
                if 'UPPER' in line[0]:
                    threshold_dict[line[0][6:]]=[[],line[1:]]
                elif 'LOWER' in line[0]:
                    #print("""111threshold_dict[line[0].strip('LOWER_')]""",threshold_dict[line[0].strip('LOWER_')])
                    threshold_dict[line[0][6:]][0]=line[1:]
                    #print("""222threshold_dict[line[0].strip('LOWER_')]""",threshold_dict[line[0][6:]])
                #ok find
    #for k in threshold_dict.keys():
        #print "key: ",k
        #print 'val :',threshold_dict[k]
    return threshold_dict        
        
def get_file_list(folder):
    flist=[]
    for subitem in os.listdir(folder):
        if '.txt' or '.log' in subitem:
            print(subitem)
            flist.append(folder+'/'+subitem)
    print("""
    
    
    
    list:
    """)
    for item in flist:
        print(item)
    return flist


#def judge_in_log:
    #fail_list_1st_order=['dco_sweep_test_ADC_STEP','RX_PATH_GAIN','RX_SWITCH_GAIN','TXIQ','TXBB_TXIQ','TXDC','FREQ_OFFSET','fb_rx_num',]
    #fail_list_2nd_order=[]
    #fail_list_3nd_order=[]
    #mode='ate130716'
    
    
    #cnt=0
    #filelist=get_file_list('test')
    #for file_path in filelist:
        #value_dict=read_log_data(file_path,mode)[0]
        #for item in value_dict.keys():
            #print(item,value_dict[item])
        #for item 
        
        
        
#=============================================================================================
    
#def judge_in_csv():
    
    #filelist=get_file_list('test')
    
    
    #fail_dict_1st_order={
                         #'dco_sweep_test_ADC_STEP':[0,[]],
                         #'RX_PATH_GAIN':[0,[]],
                         #'RX_SWITCH_GAIN':[0,[]],
                         #'TXIQ':[0,[]],
                         #'TXBB_TXIQ':[0,[]],
                         #'TXDC':[0,[]],
                         #'FREQ_OFFSET':[0,[]],
                         #'fb_rx_num':[0,[]]
                         
                         #}
    #threshold={
                         #'dco_sweep_test_ADC_STEP':[[0],[5]],
                         #'RX_PATH_GAIN':[[40],[48]],
                         #'RX_SWITCH_GAIN':[[1,-9,3],[4,-6,6]],
                         #'TXIQ':[[-12,-25],[12,25]],
                         #'TXBB_TXIQ':[[-6],[6]],
                         #'TXDC':[[3],[124]],
                         #'FREQ_OFFSET':[[0],[32]],
                         #'fb_rx_num':[[15],[16]]        
        
        #}
    
    
    #print('======================================')
    #print(fail_dict_1st_order.keys() )
    #for k in fail_dict_1st_order.keys():
        #print(fail_dict_1st_order[k])
    #print('======================================')
    ##fail_list_2nd_order=[]
    ##fail_list_3nd_order=[]    
    
    #f=open('data_csv.csv','r')
    #line=f.readline()
    #item_list=line.split(',')
    #for i in range(len(item_list)):
        #for j in range(len(fail_dict_1st_order)):
            #if fail_dict_1st_order[j] in item_list[i]:
                
            
            
            
        ##if item_list[i] 
    
    
    ##pass

#=============================================================================================




def read_csv_to_list(fname='chip_datalog_ATE_20130604.csv',col=0,start=1,end=''):   
    
    line=[]
    f=open(fname,'r')
    lines=f.readlines()
    
    
    
    if type(col)==type(''):
        ltmp=lines[0].split(',')
        for i in range(len( ltmp) ):
            if col==ltmp[i].strip('\n'):
                col=i
                #print('col :',col)
                break
        
        
        
    #print('col 222   ',col)
    for i in range(len(lines)):
        if i==0:
            print("len col :",len(lines[i].split(',')))
            print(lines[i].split(',')[col])
                  
        if i>=start:
            if not lines[i].split(',')[col] =='':
                line.append( float(lines[i].split(',')[col] ))
        else:
            
            pass
        
    return line  


            
if __name__=='__main__':
    #judge_thr()
    #make_csv()
    #=======================================================
    thre=get_threshold_dict('ATE','./Threshold/full_Threshold.xlsx')
    values_dictlist=read_log_data('./logs/print/2015-08-18_print/0x0_A132AA_prnt_1_2015-08-18_13_51_43.txt','module2515')
    data_process_dictList_2(values_dictlist,thre)
    
    #log_csv('.log','./test/chip_id','ate_0530_4noisefloor')
    #=====================================================
    #folder=raw_input("please enter the folder name : \n")

    
    #try:
        #log_csv('.log',folder,'ate130716')
    #except:
        #print("wrong folder name ,or other error")
    #=====================================================
    #judge_in_csv()
    
    
    
    
    
    #pass
