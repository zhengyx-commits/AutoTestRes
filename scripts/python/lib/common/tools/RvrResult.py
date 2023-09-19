#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/1/5 16:48
# @Author  : chao.li
# @Site    :
# @File    : RvrResult.py
# @Software: PyCharm

import logging
import os
import re
import time

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from util.Decorators import singleton


@singleton
class RvrResult():
    '''
    Singleton class,should not be inherited
    handle rvr text result

    Attributes:
        logdir : log path
        current_number : current index
        rvr_pdffile : rvr pdf file
        rvr_excelfile : rvr excel file
        log_file : rvr result csv
        detail_file : rvr detail result (contain rssi value)

    '''

    def __init__(self, logdir, step):
        self.logdir = logdir
        self.current_number = 0
        self.rvr_pdffile = PdfPages(f'{self.logdir.split("results")[0]}/results/RvrResult.pdf')
        self.rvr_excelfile = f'{self.logdir.split("results")[0]}/results/RvrCheckExcel.xlsx'
        if not hasattr(self, 'logFile'):
            self.log_file = f'{self.logdir}/Rvr_' + time.asctime() + '.csv'
        if not hasattr(self, 'detialFile'):
            self.detail_file = f'{self.logdir}/Rvr_Detial.log'
            with open(self.detail_file, 'a', encoding='utf-8') as f:
                f.write("This is rvr test detial data\n\n")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            title = 'Priority	Test_Category	Sub_Category	Coex_Method	BT_WF_Isolation	Standard	Freq_Band	BW	Data_Rate	CH_Freq_MHz	Protocol	Direction	Total_Path_Loss	RxP	Beacon_RSSI	Data_RSSI	Throughput	MCS_Rate'
            f.write(','.join(title.split()))
            f.write('\n')

    def save_result(self, result):
        '''
        write result to log_file
        @param casename: wifi case name
        @param result: tx,rx result
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
        if not os.path.exists(self.rvr_excelfile):
            df.to_excel(self.rvr_excelfile, sheet_name=time.asctime().replace(' ', '_').replace(':', '-'))
        else:
            with pd.ExcelWriter(self.rvr_excelfile, engine='openpyxl', mode='a') as f:
                df.to_excel(f, sheet_name=time.asctime().replace(' ', '_').replace(':', '-'))
        logging.info('Write done')

    def write_to_pdf(self):
        '''
        format excel to pdf
        @return: None
        '''
        df = pd.read_excel(self.rvr_excelfile, sheet_name=None)
        all_data = []
        # print(list(df.keys()))
        # ['Fri_Feb_11_16-44-19_2022', 'Fri_Feb_11_16-45-16_2022', 'Fri_Feb_11_16-45-49_2022']
        io = pd.io.excel.ExcelFile(self.rvr_excelfile)
        for i in list(df.keys()):
            all_data.append(pd.read_excel(io, sheet_name=i).values)

        io.close()
        title = all_data[0][:, 0].tolist()
        all_data = [i.tolist() for i in all_data]
        plt.figure(figsize=(10, 10))
        plt.suptitle("This is a Rvr test report summary")
        plt.subplots_adjust(wspace=0.3, hspace=0.8)
        x_label = list(range(0, 48, 3))
        for i in title:
            ax = plt.subplot(5, 2, 1 + title.index(i))
            ax.set_title(i)
            for j in range(len(all_data)):
                plt.plot(x_label, all_data[j][title.index(i)][1:], label=list(df.keys())[j])
            plt.plot(x_label, [100 for i in range(len(x_label))], label='Singal Debility')
            plt.xlabel("Version")
            plt.ylabel("Throughput rate Mb/s")
            plt.legend()
        self.rvr_pdffile.savefig()
        self.rvr_pdffile.close()

# rvr = RvrResult('/Users/coco/Automation/AutoTestRes/scripts/python')
# rvr.writeInPdf()
