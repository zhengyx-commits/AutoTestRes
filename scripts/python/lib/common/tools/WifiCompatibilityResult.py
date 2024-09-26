#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/12/8 10:42
# @Author  : chao.li
# @Site    :
# @File    : WifiCompatibilityResult.py
# @Software: PyCharm


import logging
import os
import re
import time

import pandas as pd

from util.Decorators import singleton


@singleton
class WifiCompatibilityResult:
    '''
    Singleton class,should not be inherited
    handle WiFi compatibility text result

    Attributes:
        logdir : log path
        current_number : current index
        wifi_excelfile : compatibility excel file
        log_file : compatibility result csv

    '''

    def __init__(self, logdir):
        self.logdir = logdir
        self.current_number = 0
        self.wifi_excelfile = f'{self.logdir.split("results")[0]}/results/WifiCompatibilityExcel.xlsx'
        if not hasattr(self, 'logFile'):
            self.log_file = f'{self.logdir}/WifiCompatibility_' + time.asctime() + '.csv'
        with open(self.log_file, 'a', encoding='utf-8') as f:
            title = 'Serial Ap_Type	SSID Band Wireless_mode	Bandwidth Channel Authentication_Method Passwd Hide_Ssid PMF Theoretical_Rate Result'
            f.write(','.join(title.split()))
            f.write('\n')

    def save_result(self, result):
        '''
        write result to log_file
        @param casename: wifi case name
        @param result: result
        @return: None
        '''
        logging.info('Writing to csv')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(result)
            f.write('\n')
        logging.info('Write done')

    def write_to_excel(self):
        '''
        format csv to excel
        @return: None
        '''
        logging.info('Write to excel')
        df = pd.read_csv(self.log_file)
        # 转置数据
        # df = pd.DataFrame(df.values.T, index=df.columns, columns=df.index)
        if not os.path.exists(self.wifi_excelfile):
            df.to_excel(self.wifi_excelfile, sheet_name=time.asctime().replace(' ', '_').replace(':', '-'))
        else:
            with pd.ExcelWriter(self.wifi_excelfile, engine='openpyxl', mode='a') as f:
                df.to_excel(f, sheet_name=time.asctime().replace(' ', '_').replace(':', '-'))
        logging.info('Write done')
