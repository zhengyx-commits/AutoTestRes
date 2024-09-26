#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/1 13:49
# @Author  : chao.li
# @Site    :
# @File    : KpiAnalyze.py
# @Software: PyCharm
import sys
import time
import logging
import codecs
import fcntl
import subprocess
import os
import _io
import signal
import threading
from collections import Counter

import pandas as pd
import re
import openpyxl
import pytest
import xlrd
import xlwt
from xlutils.copy import copy
from openpyxl import load_workbook
from datetime import datetime, timedelta
from copy import deepcopy
import glob
import shutil


def _bytes_repr(c):
    """py2: bytes, py3: int"""
    if not isinstance(c, int):
        c = ord(c)
    return '\\x{:x}'.format(c)


def _text_repr(c):
    d = ord(c)
    if d >= 0x10000:
        return '\\U{:08x}'.format(d)
    else:
        return '\\u{:04x}'.format(d)


def backslashreplace_backport(ex):
    s, start, end = ex.object, ex.start, ex.end
    c_repr = _bytes_repr if isinstance(ex, UnicodeDecodeError) else _text_repr
    return ''.join(c_repr(c) for c in s[start:end]), end


codecs.register_error('backslashreplace_backport', backslashreplace_backport)


def _bytes_to_escaped_unicode(bytes_str):
    """
    Converts a bytes object to a unicode string with non-printables escaped
    """
    if isinstance(bytes_str, bytes):
        return (bytes_str.decode('utf-8', 'backslashreplace_backport').
                encode('unicode_escape').decode('utf-8', errors='ignore'))
    else:
        return bytes_str.encode('unicode_escape').decode('utf-8', errors='ignore')


def save_result(xlsx_name):
    g_conf_device_id = pytest.config['device_id']
    if '.xlsx' in xlsx_name:
        target_name = xlsx_name.split('.xlsx')[0]
    else:
        target_name = xlsx_name
    if "ott_hybrid_t" in pytest.target.get("prj"):
        dirpath = "/var/www/res/android_t_kpi_result"
    else:
        dirpath = "/var/www/res/android_s_kpi_result"
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_path = f'{timestamp}_{g_conf_device_id}'
    logging.info(new_path)
    directory = os.path.join(dirpath, new_path)
    os.makedirs(directory)
    file_list = glob.glob(f'{target_name}.*')
    for file_path in file_list:
        shutil.move(file_path, directory)
        # shutil.copyfile(file_path, f"{directory}/{file_path}")


class KpiAnalyze:
    def __init__(self, for_framework, adb=None, config=None, kpi_name=None, targetfile=None, kpifileobj=None, kpifileobj_xlsx=None, **kwargs):
        self.for_framework = for_framework
        self.id_list_key_max = ""
        self.id_list_key_min = ""
        self.store_enable = False
        self.id_min_found = False
        self.id_max_found = True
        self.repeat_count = 1
        self.count = 0
        # kpi分析参数
        self.kpi_name = kpi_name  # kpi的xml文件名称（信息保存在config中）
        self.id_dict = {}  # kpi分析用于记录需要获取的log内容的ID
        self.res_dict = {}  # kpi分析用于存储计算结果的名称
        # self.offset_dict = {}  # kpi analyze any offset in config.yaml
        self.id_list_keys = []  # kpi分析用于记录log内容的所有ID
        self.offset_list = []
        self.kpi_mean_list = ["mean"]
        self.kpi_min_list = ["min"]
        self.kpi_max_list = ["max"]
        self.config_offset_list = []
        self.kpi_dict = {}
        self.kpi_index = {}  # 用于记录kpi的log内容和出现时间
        self.kpi_index_list = []
        self.kpi_key_logtime = []
        self.kpifileobj_xlsx = kpifileobj_xlsx
        if for_framework:
            from tools.yamlTool import yamlTool
            logging.info(f'kpi analyze for framework')
            # kpi分析参数
            self.kpi_config = yamlTool(os.getcwd() + config).get_note('kpi_config')
            self.repeat_count = self.kpi_config.get('kpi_debug').get('repeat_count')
            logging.info(f"self.repeat_count:{self.repeat_count}")
        else:
            from yamlTool import yamlTool
            logging.info('kpi for temporary')
            if adb is None or config is None:
                raise EnvironmentError("adb and config is needed")
            # self.kpi_config = yamlTool(os.getcwd() + f'/../config/{config}')
            if ".." in config:
                self.kpi_config = yamlTool(os.getcwd() + f'/../config/{config}')
            else:
                self.kpi_config = yamlTool(config)
            self.kpi_config = self.kpi_config.get_note('kpi_config')
        self.kpifile = open(kpifileobj, 'w')
        self.serialnumber = adb
        self.uboot_case = False
        if targetfile is None:
            print("start logcat")
            if "boot" not in kwargs.values():
                self.catch_thread = threading.Thread(target=self.start_catch_logcat, name='Kpi catch logcat -b all')
                self.catch_thread.setDaemon(True)
                self.catch_thread.start()
            else:
                self.uboot_case = True
                self.uboot_time = []
        else:
            print("Don't need catch")
            self.logcat_file = open(targetfile, 'r')
        # print(self.kpi_config)
        # self.kpi_name = self.kpi_config.get("kpi_debug")["name"]  # 获取需要分析的kpi名称
        # # print(self.kpi_name)
        if self.kpi_name + "_config_id" in self.kpi_config:
            # 若存在相应的分析内容的json数据，则将其存入_id_dict中
            self.id_dict = self.kpi_config.get(self.kpi_name + "_config_id")
            # print(len(list(self.id_dict.keys())))
            # get the last key in dictionary
            for key in self.id_dict.keys():
                self.id_list_keys.append(key)
            self.id_list_key_min = self.id_list_keys[0]
            self.id_list_key_max = self.id_list_keys[-1]
            # print(self.id_list_key_max)
        if self.kpi_name + "_config_result" in self.kpi_config:
            # 若存在相应的分析内容的json数据，则将其存入_res_dict中
            self.res_dict = self.kpi_config.get(self.kpi_name + "_config_result")
            # print(self.res_dict)

    def start_catch_logcat(self):
        '''
        start logcat and save to logcat_xxxx.log
        @return: None
        '''
        self.logcat_file = open(f'logcat_{self.serialnumber}_{self.kpifile.name.split(".")[0]}.log', 'w', encoding='utf-8')
        logging.info('start to catch logcat -b all')
        subprocess.Popen(
            f'adb -s {self.serialnumber} logcat -c'.split(),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.log = subprocess.Popen(f'adb -s {self.serialnumber} logcat -v threadtime'.split(),
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        fcntl.fcntl(self.log.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        while True:
            if self.log:
                line = self.log.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                if not self.logcat_file.closed: self.logcat_file.write(line)

    def stop_catch_logcat(self):
        '''
        stop logcat
        kill popen
        kill adb
        stop file context
        @return:
        '''
        if hasattr(self, 'log') and isinstance(self.log, subprocess.Popen):
            logging.warning('pls pass in the popen object')
            self.log.terminate()
            os.kill(self.log.pid, signal.SIGTERM)
            self.log = None
        if hasattr(self, 'logcat_file') and not isinstance(self.logcat_file, _io.TextIOWrapper):
            self.logcat_file.close()
        logging.info('stop to catch logcat -b all')

    def get_year(self):
        year_now = str(datetime.now().year)
        return year_now

    def save_txt(self, key, value, readline_time):
        value = value + "," + str(readline_time)
        if not re.findall(".*\.(.*)", value):
            value = value + "," + str(readline_time) + ".000000"
        self.kpifile.write("id:" + key + "  '" + value + "' found, Time: " +
                           str(readline_time.timestamp() * 1000) + "||")

    def kpi_analysis(self, out=''):
        self.id_dict2 = deepcopy(self.id_dict)
        self.speed_to_start = False
        def analyze(out):
            if "tcp connect" in self.id_dict.values():
                if (self.count == len(self.id_dict2.keys())) and (self.id_min_found is True):
                    # reset id_dict
                    self.count = 0
                    self.id_dict2 = deepcopy(self.id_dict)
                    self.id_min_found = False
            str_out = _bytes_to_escaped_unicode(out)
            self.id_found = False
            if self.id_dict2 != {} and self.res_dict != {}:
                # print("190", self.id_dict2)
                #  当id和result数据均找到后，开始分析
                for key, value in self.id_dict2.items():
                    if value in str_out and (self.id_found is False):
                        # print(str_out)
                        self.id_found = True
                        # print("183", key, value)
                        # readline_time = datetime.strptime(str_out[0:18], "%m-%d %H:%M:%S.%f")
                        readline_time = datetime.strptime(self.get_year() + '-' + str_out[0:18], "%Y-%m-%d %H:%M:%S.%f")
                        # print(readline_time)
                        # print(readline_time.timestamp()*1000)
                        # 如果该log的内容中存在需要抓取的信息，将信息存入分析文件中
                        if key == self.id_list_key_max and len(self.id_dict.keys()) > 2:
                            #if "vod_p_kpi" in self.kpi_name:
                            # if "tcp connect" not in self.id_dict.values():
                            if self.id_min_found is True and f"poppy-{value}" not in self.id_dict2.values():
                                self.count += 1
                                print(key, value)
                                self.save_txt(key, value, readline_time)
                                if "tcp connect" in self.id_dict.values():
                                    value = f"poppy-{value}"
                                self.id_dict2[key] = value
                                self.kpifile.write("\n")
                                self.id_min_found = False
                                self.speed_to_start = False
                            if "tcp connect" in self.id_dict.values():
                                self.kpifile.write("\n")
                            tmp_key_dict.clear()
                            # seek_switch_tmp_dict.clear()
                        else:
                            """
                            "1": interceptKeyTi keyCode=23 down=true
                            "16": interceptKeyTi keyCode=23 down=false
                            """
                            # for android P start kpi, get last time
                            if ((((key == "1" and value == "interceptKeyTi keyCode=23 down=true") or (value == "interceptKeyTi keyCode=23 down=false") or
                                    (key == "1" and value == "interceptKeyTq keycode=") or (key == "1")) and ("_s_t_" not in self.kpi_name))) and ("rtsp_s_4kP30_h264_speed_to_start" not in self.kpi_name):
                                self.id_min_found = True
                                print(key, value)
                                tmp_key_dict[key] = value + "," + str(readline_time)
                            # for android S start kpi, get last time
                            elif (value == "onKeyDown: startPlay clicked" or value == "1_1 creat AmPlayer" or value == "1_2 setDataSource") and ("vod_s_t_kpi" in self.kpi_name) and ("live_s_t_switch_exit" not in self.kpi_name):
                            # elif (value == "1_1 creat AmPlayer" or value == "1_2 setDataSource"):
                                self.id_min_found = True
                                print(key, value)
                                tmp_key_dict[key] = value + "," + str(readline_time)
                            elif (value == "AmCtcPlayer setParameter:set speed:1000") and ("rtsp_s_4kP30_h264_speed_to_start" in self.kpi_name):
                                self.id_min_found = True
                                self.kpifile.write("\n")
                                self.save_txt(key, value, readline_time)
                                print(key, value)
                            elif (value == "setPlaybackRate, rate: 1.000000" and "rtsp_s_4kP30_h264_speed_to_start" in self.kpi_name):
                                if self.id_min_found:
                                    self.speed_to_start = True
                                    print(key, value)
                                    self.save_txt(key, value, readline_time)
                            # for android S live switch kpi, get first time
                            elif (key == "2" or value == "AM_KPI::Stage 7_1 stop") and ("_s_t_" in self.kpi_name) and ("vod_s_t_seek" not in self.kpi_name):
                            # elif (key == "1") and ("_s_t_" in self.kpi_name) and ("vod_s_t_seek" not in self.kpi_name):
                                if self.id_min_found:
                                    if key not in tmp_key_dict.keys():
                                        # self.kpifile.write("\n")
                                        tmp_key_dict[key] = value + "," + str(readline_time)
                                        for k, v in tmp_key_dict.items():
                                            if not re.findall(".*\.(.*)", v):
                                                v = v + "," + str(readline_time) + ".000000"
                                            self.id_min_found = True
                                            self.kpifile.write("id:" + k + "  '" + v + "' found, Time: " +
                                                               str(datetime.strptime(self.get_year() + '-' + v[-21:], "%Y-%m-%d %H:%M:%S.%f").timestamp()*1000) + "||")
                                            print(k, v)
                            # for android S rtsp speed to start, get first time after key log
                            elif (value == "put: repeat_count =0, omx_index=") and ("rtsp_s_4kP30_h264_speed_to_start" in self.kpi_name):
                                # print("278", key, value)
                                # print("self.speed_to_start", self.speed_to_start)
                                if self.id_min_found:
                                    if self.speed_to_start:
                                        key = "6"
                                        self.speed_to_start = False
                                    if key not in tmp_key_dict.keys():
                                        # self.kpifile.write("\n")
                                        tmp_key_dict[str(key)] = value + "," + str(readline_time)
                                        for k, v in tmp_key_dict.items():
                                            if not re.findall(".*\.(.*)", v):
                                                v = v + "," + str(readline_time) + ".000000"
                                            self.id_min_found = True
                                            self.kpifile.write("id:" + k + "  '" + v + "' found, Time: " +
                                                               str(datetime.strptime(self.get_year() + '-' + v[-21:], "%Y-%m-%d %H:%M:%S.%f").timestamp()*1000) + "||")
                                            print(k, v)
                                    if key == "6":
                                        self.kpifile.write("\n")
                                        break

                            elif (key == "1") and ("_s_t_" in self.kpi_name) and ("vod_s_t_seek" in self.kpi_name):
                                self.id_min_found = True
                                self.kpifile.write("\n")
                                self.save_txt(key, value, readline_time)
                            elif (key == "1") and ("_s_t_" in self.kpi_name) and ("live_s_t_switch_exit" in self.kpi_name):
                                tmp_key_dict.clear()
                                self.id_min_found = True
                                self.kpifile.write("\n")
                                self.save_txt(key, value, readline_time)
                            else:
                                if len(tmp_key_dict) != 0 and ("vod_s_t_seek" not in self.kpi_name) and ("live_s_t_switch" not in self.kpi_name):
                                    self.count += 1
                                    if "rtsp_s_4kP30_h264_speed_to_start" not in self.kpi_name:
                                        self.kpifile.write("\n")
                                    for k, v in tmp_key_dict.items():
                                        if not re.findall(".*\.(.*)", v):
                                            v = v + "," + str(readline_time)
                                            print("fail2", v)
                                        self.kpifile.write("id:" + k + "  '" + v + "' found, Time: " +
                                                           str(datetime.strptime(self.get_year() + '-' + v[-21:], "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1000) + "||")
                                    if (value != "put: repeat_count =0, omx_index="):
                                        tmp_key_dict.clear()
                                if key != "1":
                                    if self.id_min_found is True:
                                        self.count += 1
                                        self.save_txt(key, value, readline_time)
                                        if "tcp connect" in self.id_dict.values():
                                            value = f"poppy-{value}"
                                        self.id_dict2[key] = value
                                    # else:
                                    #     pass

        def analyze_for_p(out):
            str_out = _bytes_to_escaped_unicode(out)
            if (self.count == len(self.id_dict2.keys())) and (self.id_min_found is True):
                self.count = 0
                self.id_dict2 = deepcopy(self.id_dict)
                self.id_min_found = False
                seek_switch_tmp_dict.clear()
                logging.info("All value found")
            self.id_found = False
            if self.id_dict2 != {} and self.res_dict != {}:
                #  当id和result数据均找到后，开始分析
                for key, value in self.id_dict2.items():
                    if value in str_out and (self.id_found is False):
                        self.id_found = True
                        readline_time = datetime.strptime(self.get_year() + '-' + str_out[0:18], "%Y-%m-%d %H:%M:%S.%f")
                        # 如果该log的内容中存在需要抓取的信息，将信息存入分析文件中
                        if key == self.id_list_key_max and len(self.id_dict.keys()) > 2:
                            if self.id_min_found is True and f"poppy-{value}" not in self.id_dict2.values():
                                self.count += 1
                                self.id_max_found = True
                                print(f'max_key:{key}, max_value:{value}')
                                self.save_txt(key, value, readline_time)
                            tmp_key_dict.clear()
                            seek_switch_tmp_dict.clear()
                        else:
                            # for android P start kpi, get last time
                            if (((key == "1" and value == "interceptKeyTi keyCode=23 down=true") or (
                                    value == "interceptKeyTi keyCode=23 down=false") or
                                 (key == "1" and value == "interceptKeyTq keycode=") or (key == "1")) and (
                                    "_s_" not in self.kpi_name)):
                                self.id_max_found = False
                                tmp_key_dict[key] = value + "," + str(readline_time)
                                print(f'id_min_found:{tmp_key_dict}')
                            # for android P switch channel kpi,get first time
                            elif (key == "2" and value == "AmlogicPlayer: stop") and (
                                    ("p_switch_channel" in self.kpi_name) or ("p_replay" in self.kpi_name)) and (
                                    self.id_max_found is False):
                                if key not in seek_switch_tmp_dict.keys():
                                    seek_switch_tmp_dict[key] = value + "," + str(readline_time)
                                    print(f"same value :{seek_switch_tmp_dict}")
                            else:
                                if ("_s_" not in self.kpi_name) and (key == "2" or key == "3"):
                                    if len(tmp_key_dict) != 0:
                                        self.count += 1
                                        self.id_min_found = True
                                        self.kpifile.write("\n")
                                        for k, v in tmp_key_dict.items():
                                            if not re.findall(".*\.(.*)", v):
                                                v = v + "," + str(readline_time)
                                                logging.info(f"fail2:{v}")
                                            self.kpifile.write("id:" + k + "  '" + v + "' found, Time: " +
                                                               str(datetime.strptime(self.get_year() + '-' + v[-21:],
                                                                                     "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1000) + "||")
                                        if len(seek_switch_tmp_dict) != 0:
                                            self.count += 1
                                            for k, v in seek_switch_tmp_dict.items():
                                                if not re.findall(".*\.(.*)", v):
                                                    v = v + "," + str(readline_time)
                                                    logging.info(f"fail2:{v}")
                                                self.kpifile.write("id:" + k + "  '" + v + "' found, Time: " +
                                                                   str(datetime.strptime(self.get_year() + '-' + v[-21:],
                                                                                         "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1000) + "||")
                                        logging.info("temp key dict write over")
                                        tmp_key_dict.clear()
                                if key != "1":
                                    if self.id_min_found is True:
                                        self.count += 1
                                        print(f'sign_key:{key}', f'sign_value:{value}')
                                        self.save_txt(key, value, readline_time)
                                        if "] seekTo(" in self.id_dict.values():
                                            value = f"Need replace-{value}"
                                        self.id_dict2[key] = value
        seek_switch_tmp_dict = {}
        tmp_key_dict = {}
        if self.uboot_case:
            logfile = "boottotal.log"
        else:
            if self.for_framework:
                self.stop_catch_logcat()
            logfile = self.logcat_file.name
        with open(logfile, 'rb') as f:
            logcat_info = f.readlines()
        for out in logcat_info:
            if "_p_" in self.kpi_name:
                analyze_for_p(out)
            else:
                analyze(out)
        self.kpifile.close()

    def kpi_calculate(self):
        kpi_list = []
        self.kpi_index_list_before = []
        self.kpi_index_list = []
        with open(file=self.kpifile.name, mode="r+", encoding="utf-8") as f:
            kpi_items_list = f.readlines()
            # print("281", kpi_items_list)
            for kpi_items in kpi_items_list:
                kpi_item = kpi_items.split("\n\n")
                # print("kpi_item", kpi_item)
                for item in kpi_item:
                    # print("259", item)
                    item_list = item.split("||")
                    # print("item_list", item_list)
                    # print(len(item_list))
                    # if len(item_list) != len(self.id_list_keys):
                    #     print("288")
                    #     # raise Exception("config can't matched all log")
                    #     break
                    # else:
                    # print(item_list)
                    # if len(item_list)-1 == len(self.id_list_keys):
                    kpi_list.append(item_list)
        # print("kpi_list", kpi_list)
        for kpi_key_logtimes in kpi_list:
            log = " ".join(list(kpi_key_logtimes))
            kpi_key_logtime_before = re.findall(r":(\d+).*?,(\d+-\d+-\d+ \d+:\d+:\d+.\d+).*? Time: (\d+.\d+)", log)
            self.kpi_index_list_before.append(kpi_key_logtime_before)
            kpi_key_logtime = re.findall(r":(\d+).*?, Time: (\d+.\d+)", log)
            self.kpi_index_list.append(dict(kpi_key_logtime))
        # print("kpi_index_list", self.kpi_index_list)
        # print("kpi_key_logtime", self.kpi_index_list_before)
        if len(self.kpi_index_list) == 0:
            raise Exception("config can't matched all log, please check config.yaml")
        if "_p_" in self.kpi_name:
            kpi_index_list = self.kpi_index_list[1:]
        else:
            kpi_index_list = self.kpi_index_list
        for kpi_index in kpi_index_list:
            for key in self.res_dict.keys():
                # if len(kpi_index) != len(self.id_list_keys):
                #     break
                # start = key.split(",")[0]  # end id
                # end = key.split(",")[1]  # start id
                fill_playback = False
                if "-" in key:
                    start = key.split("-")[0]  # end id
                    end = key.split("-")[1]  # start id
                    fill_playback = True
                else:
                    start = key.split(",")[0]  # end id
                    end = key.split(",")[1]  # start id
                with open(file=self.kpifile.name, mode="a+", encoding="utf-8") as f:
                    if fill_playback is True:
                        is_write = False
                        for i in range(int(start), int(end) + 1, 1):
                            if str(i) in list(kpi_index.keys()):
                                is_write = True
                                break
                        if is_write is True:
                            self.offset_list.append("Y")
                        else:
                            self.offset_list.append("N")
                    else:
                        if end in list(kpi_index.keys()) and start in list(kpi_index.keys()):
                            # 若起始log的id与终止log的id都已被找到，则开始进行计算，否则写入not found信息
                            if abs(float(kpi_index[start])) > abs(float((kpi_index[end]))):
                                # if float(kpi_index[start]) < float((kpi_index[end])):
                                # 如果起始log的出现时间晚于终止log的时间，则将结果从负数转为正数，并进行警告
                                f.write(str(self.res_dict[key]) + "= related logtime is wrong\n")
                                # self.offset_list.append("N/A")
                                self.offset_list.append("N/A")
                                # print("offset: related logtime is wrong", self.offset)
                            else:
                                self.offset = float(kpi_index[end]) - float(kpi_index[start])
                                print("offset:   ", self.offset, kpi_index[start], kpi_index[end])
                                # self.offset = int(str(self.offset).split(".")[0])
                                self.offset = self.offset.__round__()
                                # print(self.offset)
                                f.write(self.res_dict[key] + " = " + str(float(self.offset)) + "\n")
                                if self.res_dict[key] in self.kpi_dict.keys():
                                    self.kpi_dict[self.res_dict[key]].append(self.offset)
                                else:
                                    self.kpi_dict[self.res_dict[key]] = [self.offset]
                                self.offset_list.append(self.offset)
                        else:
                            f.write(str(start) + " " + str(end) + self.res_dict[key] + " = related log not found\n")
                            # self.offset_list.append("notfound")
                            self.offset_list.append("N/A")
                            # print("offset: related log not found", self.offset)
        print("kpi calculated...")

    def save_to_excel(self):
        print("offset_list", self.offset_list)
        # self.kpi_mean_list = ["mean"]
        # self.kpi_min_list = ["min"]
        # self.kpi_max_list = ["max"]
        final = []
        final_new = []
        offset_list = []
        offset_list_new = []
        res_list = list(self.res_dict.values())
        columns = res_list
        kpi_logtime = [self.offset_list[i:i + len(list(self.res_dict.keys()))]
                       for i in range(0, len(self.offset_list), len(list(self.res_dict.keys())))]
        # all data save to excel
        # for once_kpi_logtime in kpi_logtime[1:]:
        for once_kpi_logtime in kpi_logtime:
            if once_kpi_logtime[0] != "N/A":
                offset_list.append(once_kpi_logtime)

        # filter out "N/A" to calculate kpi average
        for once_kpi_logtime in kpi_logtime:
            if "N/A" not in once_kpi_logtime:
                offset_list_new.append(once_kpi_logtime)

        if self.uboot_case:
            res_list.insert(0, "uboot")
            columns = res_list
            offset_list = [[float(time)] + sublist if time != "N/A" else ["N/A"] + sublist for time, sublist in zip(self.uboot_time, offset_list)]
            offset_list_new = [[float(time)] + sublist if time != "N/A" else ["N/A"] + sublist for time, sublist in zip(self.uboot_time, offset_list_new)]

        # print("offset_list_new", offset_list_new)
        for one in offset_list:
            final.append(one)
        for one in offset_list_new:
            final_new.append(one)

        kpi_data_mean = pd.DataFrame(final_new, columns=columns)
        # print("kpi_data_mean", kpi_data_mean)
        kpi_data = pd.DataFrame(final, columns=columns)
        # print("kpi_data_mean", kpi_data_mean)
        kpi_data_mean = kpi_data_mean[:]
        if not kpi_data_mean.empty:
            for index, ele in enumerate(columns):
                try:
                    column_value_list = kpi_data_mean[ele].tolist()
                    max_value = max(column_value_list)
                    min_value = min(column_value_list)
                    column_value_list.remove(max_value)
                    column_value_list.remove(min_value)
                    # print(column_value_list)
                    min_value = min(column_value_list)
                    max_value = max(column_value_list)
                    mean_value = sum(column_value_list)/len(column_value_list)
                    self.kpi_mean_list.append(mean_value)
                    self.kpi_min_list.append(min_value)
                    self.kpi_max_list.append(max_value)
                except Exception as e:
                    logging.info(f"{e}")
        # print(self.kpi_mean_list)
        kpi_data.to_excel(f'{self.kpifileobj_xlsx}', sheet_name="kpi", index=True, startrow=3, startcol=0)
        kpi_data_mean = pd.DataFrame([self.kpi_mean_list])
        kpi_data_min = pd.DataFrame([self.kpi_min_list])
        kpi_data_max = pd.DataFrame([self.kpi_max_list])
        kpi_data_old = pd.DataFrame(pd.read_excel(f'{self.kpifileobj_xlsx}', sheet_name="kpi"))
        book = load_workbook(f'{self.kpifileobj_xlsx}')
        writer = pd.ExcelWriter(f'{self.kpifileobj_xlsx}', engine='openpyxl', mode="a")
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        df_rows = kpi_data_old.shape[0]  # 获取原数据的行数
        # 将数据写入excel表,从第一个空行开始写
        kpi_data_mean.to_excel(writer, sheet_name='kpi', startrow=0, startcol=0, index=False, header=False)
        kpi_data_min.to_excel(writer, sheet_name='kpi', startrow=1, startcol=0, index=False, header=False)
        kpi_data_max.to_excel(writer, sheet_name='kpi', startrow=2, startcol=0, index=False, header=False)
        writer.save()  # 保存

    def save_to_db(self, name, flag):
        if name:
            self.kpi_name = name
        kpi_table_name = self.kpi_name.upper() + '_RESULTS'
        logging.info(f'kpi table name: {kpi_table_name}')
        calculate_table_name = self.kpi_name.upper() + '_CALCULATE_RESULTS'
        logging.info(f'calculate table name: {calculate_table_name}')
        kpi_logtime = [self.offset_list[i:i + len(list(self.res_dict.keys()))]
                       for i in range(0, len(self.offset_list), len(list(self.res_dict.keys())))]
        logging.info(f'kpi_logtime: {kpi_logtime}')
        calculate_result = self.kpi_mean_list[1:]
        logging.info(f'self.mean list: {self.kpi_mean_list}')
        logging.info(f'calculate result: {calculate_result}')
        from tools.DB import DB
        with DB() as db:
            for group in kpi_logtime:
                if group[0] != "N/A":
                    logging.info(f'group: {group}')
                    # db.insert_data("DVB_SCAN_KPI_RESULTS", *group)
                    db.insert_kpi_data(kpi_table_name, flag, *group)
            db.insert_kpi_data(calculate_table_name, flag, *calculate_result)

    def filter_abnormal_value(self, p_conf_reference_value, **kwargs):
        res = True
        if not self.for_framework:
            if not reference_value:
                return
            else:
                p_conf_reference_value = reference_value
        p_conf_reference_percentage = self.kpi_config.get("kpi_debug").get("reference_percentage")
        wb = xlrd.open_workbook(self.kpifileobj_xlsx)
        rb = wb.sheets()[0]
        # print(rb)
        wp = copy(wb)
        sheet_name = wb.sheet_by_name("kpi")
        # print(sheet_name)
        ws = wp.get_sheet(0)
        # print(ws)
        rowAmount = sheet_name.nrows
        colAmount = sheet_name.ncols
        for rowIndex in range(4, rowAmount):
            for colIndex in range(1, colAmount):
                if sheet_name.cell_value(rowIndex, colIndex) != "N/A":
                    # cell_value = sheet_name.cell_value(1, colIndex)
                    # for key, value in kwargs.items():
                    #     if key == cell_value:
                    #         if sheet_name.cell_value(rowIndex, colIndex) > float(value * p_conf_reference_percentage):
                    #             style = xlwt.easyxf('font: bold 1, color red')
                    #             ws.write(rowIndex, colIndex, sheet_name.cell_value(rowIndex, colIndex), style)
                    #             res = False
                    #         else:
                    #             style = xlwt.easyxf('font: bold 1, color blue')
                    #             ws.write(rowIndex, colIndex, sheet_name.cell_value(rowIndex, colIndex), style)
                    #     else:
                    #         style = xlwt.easyxf('font: bold 1, color blue')
                    #         ws.write(rowIndex, colIndex, sheet_name.cell_value(rowIndex, colIndex), style)
                    if "N/A" not in sheet_name.row_values(rowIndex):
                        style = xlwt.easyxf('font: bold 1, color blue')
                        ws.write(rowIndex, colIndex, sheet_name.cell_value(rowIndex, colIndex), style)
                    if float(sheet_name.cell_value(rowIndex, colIndex)) > (float(p_conf_reference_value) * float(p_conf_reference_percentage)):
                        style = xlwt.easyxf('font: bold 1, color red')
                        ws.write(rowIndex, colIndex, sheet_name.cell_value(rowIndex, colIndex), style)
                        res = False
        wp.save(self.kpifileobj_xlsx)
        return res

    def results_detect(self, excel_name, preset_expected_value, preset_manual_value):
        logging.info(f'preset expected value is : {preset_expected_value}')
        logging.info(f'preset manual value is : {preset_manual_value}')
        df = pd.read_excel(excel_name)
        # Check if 'total' is in the column names
        if 'total' in df.columns:
            start_row = 1
        else:
            start_row = 4
        df = pd.read_excel(excel_name, header=None, skiprows=start_row)
        header = pd.read_excel(excel_name, header=None, nrows=start_row)
        if start_row == 1:
            df.columns = header.iloc[0]
        else:
            df.columns = header.iloc[-1]
        # Preset value
        excepted_column_name = f'Expected Results: {preset_expected_value}'
        manual_column_name = f'Manual Results: {preset_manual_value}'
        df[excepted_column_name] = df['total'].apply(lambda x: 'Y' if x <= preset_expected_value else 'N')
        df[manual_column_name] = df['total'].apply(lambda x: 'Y' if x <= preset_manual_value else 'N')
        # df['Expected Results'] = df['total'].apply(lambda x: 'Y' if x <= preset_expected_value else 'N')
        # df['Manual Results'] = df['total'].apply(lambda x: 'Y' if x <= preset_manual_value else 'N')
        # Save the modified results
        with pd.ExcelWriter(excel_name) as writer:
            header.to_excel(writer, index=False, header=False)
            df.to_excel(writer, index=False, startrow=start_row - 1)


if __name__ == '__main__':
    args = sys.argv
    if args[-1] == "--help":
        introduction = """
        command: python3 KpiAnalyze.py <config.yaml> <kpi_name> <log> <output_txt> <output_xlsx> <reference_value>
                eg. python3 KpiAnalyze.py ../config/config.yaml vod_p_kpi d5-1\ aml-点播.log d5.txt d5.xlsx 800
                    or python3 KpiAnalyze.py ../config/config.yaml vod_p_kpi d5-1\ aml-点播.log d5.txt d5.xlsx
                    or python3 KpiAnalyze.py vod_p_kpi d5-1\ aml-点播.log
        args[1]: config file, default: ../config/config.yaml
        args[2]: kpi name, for example: vod_p_kpi
        args[3]: target log file need analyze
        args[4]: output kpi result, txt format, default: kpi.txt
        args[5]: output kpi result, xlsx format, default: kpi.xlsx
        args[6]: reference kpi value, optional params; if add it, output xlsx would filter abnormal value and mark as red
                 for example: add reference_value=800, then the other values which more than 800 would mark as red.
        """
        print(introduction)
    if len(args) <= 2:
        print("No action specified")
        sys.exit()
    print(args)
    if len(args) <= 3:
        kpi_name = args[1]
        targetfile = args[2]
        config = "../config/config.yaml"
        kpifileobj = "kpi.txt"
        kpifileobj_xlsx = "kpi.xlsx"
        reference_value = None
    elif len(args) == 4:
        kpi_name = args[1]
        targetfile = args[2]
        config = "../config/config.yaml"
        kpifileobj = "kpi.txt"
        kpifileobj_xlsx = "kpi.xlsx"
        if args[-1] == "":
            reference_value = None
        else:
            reference_value = args[-1]
    else:
        kpi_name = args[2]
        targetfile = args[3]
        config = args[1]
        kpifileobj = args[4]
        kpifileobj_xlsx = args[5]
        reference_value = None
        # if args[6] == "":
        if len(args) > 6:
            reference_value = args[len(args)-1]
        # else:
        #     reference_value = args[6]
    # kpi = KpiAnalyze('1234567890', 'kpi_analyze.txt', sys.argv[1] if len(args) > 1 else None)
    kpi = KpiAnalyze(for_framework=False, adb='1234567890', config=config, kpi_name=kpi_name, targetfile=targetfile, kpifileobj=kpifileobj,
                     kpifileobj_xlsx=kpifileobj_xlsx, reference_value=reference_value)
    # time.sleep(20)
    kpi.kpi_analysis()
    kpi.kpi_calculate()
    kpi.save_to_excel()
    kpi.filter_abnormal_value(reference_value)
