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
        yuvResult = []

        # read yuv data from log_file
        with open(self.log_file, 'r') as f:
            for i in f.readlines():
                yuvSum = ''
                self.video_name = i.strip().split(',')[1]
                if 'yuvsum' in i:
                    yuvSum = re.findall(r'yuvsum\:(.*?)\,', i)[0]
                current_time = datetime.now().strftime('%Y %m %d %H')
                yuvResult.append(self.get_video_name() + '-' + yuvSum + '-' + current_time if yuvSum else self.get_video_name() + '-error' + '-' + current_time)

        standard_rows = df[df['Result'] == 'standard']

        if len(standard_rows) > 0:
            # Extract the 'video name' collection of standard rows
            standard_video_names = set(standard_rows['video status'].str.split('-').str[0])

            # Convert yuvResult to the 'video name' collection
            yuv_video_names = set(video_name.split('-')[0] for video_name in yuvResult)

            # Determine if two sets intersect
            has_difference = len(standard_video_names.intersection(yuv_video_names)) != len(standard_video_names)
        else:
            has_difference = True

        print("has_difference:", has_difference)

        if has_difference:
            # Check if 'standard_rows' is empty, if so, create a new DataFrame with 'standard' value in 'result' column
            if standard_rows.empty:
                yuvResult_df = pd.DataFrame({'Result': ['standard'] * len(yuvResult), 'video status': yuvResult})
                df = df.append(yuvResult_df, ignore_index=True)
            else:
                # Append yuvResult to the 'video status' column, with 'standard' as the 'Result' value
                yuvResult_df = pd.DataFrame({'Result': ['standard'] * len(yuvResult), 'video status': yuvResult})
                df = df.append(yuvResult_df, ignore_index=True)
                # Set the 'Result' value of 'standard' rows to empty
                df.loc[standard_rows.index, 'Result'] = 'invalid'
        else:
            # Append yuvResult to the 'video status' column, matching the order of 'standard' rows
            yuvResult_df = pd.DataFrame({'video status': yuvResult})
            yuvResult_df['video name'] = yuvResult_df['video status'].str.split('-').str[0]
            yuvResult_df_sorted = yuvResult_df.set_index('video name').loc[
                standard_rows['video status'].str.split('-').str[0]].reset_index()

            # Traverse every row of yuvResult df sorted DataFrame
            for _, row in yuvResult_df_sorted.iterrows():
                # Extract the 'video status' value of the current row
                video_status_value = row['video status']

                # Use this value as the dictionary value, with the key 'video status'
                row_data = {'video status': video_status_value}

                # Use the append() method of DataFrame to append the dictionary to the df DataFrame
                df = df.append(row_data, ignore_index=True)

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
            # Only check rows with empty 'Result' column
            if pd.isnull(df.at[i, 'Result']):
                result = 'Pass'
                video_status = df.iloc[i, 1]

                # Check if 'error' is in 'video_status'
                if 'error' in video_status:
                    result = 'Fail'
                    background.append(video_status)
                # If 'error' not present, compare video names and test results
                else:
                    video_name_part = video_status.split('-')[0].strip()
                    test_result = video_status.split('-')[1].strip()

                    # Find 'standard' rows matching the video name part
                    standard_rows = df[df['Result'] == 'standard']
                    matched_standard_rows = standard_rows[standard_rows['video status'].str.startswith(video_name_part)]

                    # If no matched 'standard' rows, consider as 'Fail'
                    if matched_standard_rows.empty:
                        result = 'Fail'
                        background.append(video_status)
                    else:
                        # Check if the test result is different from the 'standard' row
                        for _, standard_row in matched_standard_rows.iterrows():
                            standard_test_result = standard_row['video status'].split('-')[1].strip()
                            if test_result != standard_test_result:
                                result = 'Fail'
                                background.append(video_status)
                                break

                # Set the 'Result' column value and background color
                df.at[i, 'Result'] = result
                if result == "Fail":
                    background.append(df.iloc[i, 0])

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
