#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/11 09:38
# @Author  : chao.li
# @Site    :
# @File    : LoggingTxt.py
# @Software: PyCharm

import logging
import os
import re
import subprocess
from datetime import datetime

import pandas as pd
import pytest

from util.Decorators import singleton

# from tkinter import filedialog


@singleton
class LoggingHandler():
    '''
    Singleton class,should not be inherited
    handle some test log

    Attributes:
        logdir : log path
        log_file : yuv result file
        current_number : yuv current
        yuv_excel : yuv excel
        omx_logcat : omx logcat
        cpu_info : cpu info log
        video_name : video name
        not_compare :
        drop_times : drop times
        drop_set : drop set

    '''

    def __init__(self, logdir):
        self.logdir = logdir
        self.current_number = 0
        self.yuv_excel = f'{self.logdir.split("results")[0]}/results/YUVCheckExcel.xlsx'
        self.omx_logcat = f'{self.logdir}/omxLogcat.log'
        self.cpu_info = f'{self.logdir}/cpu_info.log'
        self.video_name = ''
        self.not_compare = []
        self.drop_times = 0
        self.drop_set = ()
        self.log_file = f'{self.logdir}/' + datetime.now().isoformat() + '.txt'
        logging.info(f'FilePath:{self.log_file}')
        if not os.path.exists(self.yuv_excel):
            self.create_yuv_excel()

    def check_result_error(self):
        '''
        check yuv result log has error or not
        @return: check result
        '''
        res = subprocess.run(f"cat {self.log_file} |grep -i 'error'", encoding='utf-8', shell=True,stdout=subprocess.PIPE)
        return 'Fail' if res.stdout else 'Pass'

    def clean_status(self):
        '''
        reset video_name,drop_times,drop_set
        @return: None
        '''
        self.video_name = ''
        self.drop_times = 0
        self.drop_set = ()

    def get_video_name(self):
        '''
        re-format video name
        if name length biger than 50 , replace middle name with ....
        @return: video name
        '''
        if len(self.video_name) > 48:
            return self.video_name[:24] + '....' + self.video_name[-24:]
        else:
            return self.video_name

    def create_yuv_excel(self):
        '''
        create yuv excel and formate title
        :return:
        '''
        df = pd.DataFrame(columns=['Result', ])
        df.to_excel(self.yuv_excel, index=False)

    def write_yuv_excel(self):
        '''
        read yuv data from log_file
        write data to excel
        @return: None
        '''
        logging.info('Writing yuv data...')
        df = pd.read_excel(self.yuv_excel)
        originList = []
        if len(df.values) > 1:
            originList = df.iloc[:, 1].values
        yuvResult = []
        # read yuv data from log_file
        with open(self.log_file, 'r') as f:
            for i in f.readlines():
                yuvSum = ''
                self.video_name = i.strip().split(',')[1]
                if 'yuvsum' in i:
                    yuvSum = re.findall(r'yuvsum\:(.*?)\,', i)[0]
                yuvResult.append(self.get_video_name() + '-' + yuvSum if yuvSum else self.get_video_name() + '-error')
        # reshape Dataframe
        if len(df) < len(yuvResult):
            df = df.reindex(range(len(yuvResult) + 1))
            if len(df.values) > 1:
                for i in range(len(originList)):
                    if isinstance(originList[i], str) and originList[i].split('-')[0] != yuvResult[i].split('-')[0]:
                        yuvResult.append(yuvResult.pop(i))
        df[datetime.now()] = pd.Series(yuvResult)
        df.to_excel(self.yuv_excel, index=False)

    def check_yuv_data(self):
        '''
        check yuv data
        if not current, label the data in red
        @return: None
        '''
        logging.info('Checking yuv data')
        df = pd.read_excel(self.yuv_excel)
        background = []
        for i in range(len(df.values)):
            df.iloc[i, 0] = 'Pass'
            temp = ''
            for j in range(1, len(df.values[i])):
                if isinstance(df.values[i][j], str):
                    temp = df.values[i][j]
                    break
            if 'error' in temp:
                background.append(df.values[i][j])
                df.iloc[i, 0] = 'Fail'
                continue
            for j in range(1, len(df.values[i])):
                if temp != df.values[i][j] and isinstance(df.values[i][j], str):
                    # self.notCompare.append((i + 1, j))
                    background.append(df.values[i][j])
                    df.iloc[i, 0] = 'Fail'
                    background.append(df.values[i, 0])
        df.to_excel(self.yuv_excel, index=False)
        writer = pd.ExcelWriter(self.yuv_excel, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        redFontFormat = workbook.add_format({'font_color': '#9C0006'})
        for i in background:
            worksheet.conditional_format(1, 0, len(df), len(df.values[0]), {
                'type': 'text',
                'criteria': 'beginsWith',
                'value': i,
                'format': redFontFormat
            })
        writer.save()

    def save_yuv_resulttxt(self, name, player_type, decode_type, error='OK', yuv_info='', drop_count=0, avsync_check_enable='',
                           random_seek_info=''):
        '''
        yuv data write to log_file after playback
        :param name: video name
        :param player_type: playback type
        :param error: error info
        :param yuv_info: yuv data
        :param drop_count: drop count
        :return:
        '''
        logging.info('Writing yuv result txt')
        self.current_number += 1
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write('{},{},{},{},{},{},DropCount: {},DropIndex: {},avSync:{}, randomSeekinfo:{}'.format(
                self.current_number,
                name,
                player_type,
                decode_type,
                error,
                yuv_info,
                drop_count,
                self.drop_set,
                avsync_check_enable,
                random_seek_info
            ))
            f.write('\n')
        logging.info('Write done')

    def frame_drop_check(self):
        '''
        check frame drop, need /result/omxLogcat.log
        :return:
        '''
        with open(self.omx_logcat, 'r') as f:
            result = ''.join(f.readlines())
            inSet = set(re.findall(r'In PTS (.*?),', result, re.S))
            outSet = set(re.findall(r'Out PTS: (.*?)\.\.', result, re.S))
            self.drop_set = inSet ^ outSet
            self.drop_times = len(self.drop_set)


log = LoggingHandler(pytest.result_dir)

# if __name__ == '__main__':
#     # /home/amlogic/AutoTestRes/scripts/python/multimediaplayer/results/
#     # 手动选择文件进行yuv对比
#     # sudo apt-get python3-tk
#     filePath = __file__.split('/lib')[0] + '/results/'
#     filename = filedialog.askopenfilename(title='选择.nov文件', initialdir=(filePath))
#     # print(filename)
#     log = LoggingHandler(__file__.split('/lib')[0])
#     log.logFile = filename
#     log.writeInYUVExcel()
#     log.checkYUVSum()
