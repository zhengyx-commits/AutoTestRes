#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/16
# @Author  : kejun.chen
# @Site    :
# @File    : DvbCheck.py
# @Email   : kejun.chen@amlogic.com
# @Software: PyCharm
import fcntl
import logging
import os
import re
import signal
import subprocess
import time
import numpy as np
import threading
import random

import pytest
import threadpool

from lib.common import config_yaml
from lib.common.checkpoint.DvbCheckKeywords import DvbCheckKeywords
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from lib.common.system.Reboot import Reboot
from lib.common.system.ADB import ADB
# from lib.common.tools.DVB import DVB
from tools.yamlTool import yamlTool
from tools.resManager import ResManager

adb = ADB()
# dvb = DVB()
playerCheck = PlayerCheck()
threadLock = threading.Lock()

p_conf_check_time = config_yaml.get_note("conf_dvb_check_time").get("check_time")
p_conf_cmd_time = config_yaml.get_note("conf_dvb_check_time").get("cmd_time")
p_conf_check_play_time = config_yaml.get_note("conf_dvb_check_time").get("check_play_time")
config_yaml_dvb = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_check_is_need_search_time = config_yaml_dvb.get_note("conf_dvb_check_time").get("check_is_need_search_time")
g_conf_device_id = pytest.config['device_id']
logdir = pytest.result_dir
print(g_conf_device_id)
adb_cmd = ["/usr/bin/adb", "-s", g_conf_device_id, "shell", "logcat -s ActivityManager"]

reboot = Reboot(adb_cmd=adb_cmd, device_id=g_conf_device_id, logdir=logdir)


class DvbCheck(PlayerCheck, threading.Thread, ResManager):
    """
    Base player checkpoint, now support OTT/OTT hybrid S DVB
    """

    # switch channel pid
    VIDEO_PID_BEFORE = ''
    AUDIO_PID_BEFORE = ''

    def __init__(self):
        threading.Thread.__init__(self)
        PlayerCheck.__init__(self)
        self.threads = []
        self.flag = False
        self.checked_log_dict = {}
        self.dvbCheck_keywords = DvbCheckKeywords()
        self.thread_exit_flag = 0
        self.reset()

    def __check_thread(self, target, name):
        """

        Start a check thread.

        Args:
            target: Threads to be developed
            name: Thread name

        Returns:
            boolean: True if check in thread passed, otherwise　false

        """
        # logging.info(f"The target thread is {name}")
        __check_thread = threading.Thread(target=target, name=name)
        threadLock.acquire()
        __check_thread.start()
        self.threads.append(__check_thread)
        __check_thread.join()
        threadLock.release()
        logging.info(f'Exit {name} thread .')
        return self.flag

    def check_search_ex(self):
        """

        Check whether the automatic search is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        # self.__check_search_thread()
        if self.__check_thread(self.__search_ex_checkpoint(), 'check_search_ex'):
            if self.check_search_result():
                if self.check_whether_search_missing():
                    flag = True
        return flag

    def __search_ex_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.SEARCH_EX_FILTER
        keywords = self.dvbCheck_keywords.SEARCH_EX_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time, self.__search_ex_checkpoint.__name__)

    def check_manual_search_by_freq(self):
        """

        Check whether the manual channel search through the frequency is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__manual_search_by_freq_checkpoint(), 'check_manual_search_by_freq'):
            if self.check_search_result():
                # if self.check_whether_search_missing():
                flag = True
        return flag

    def __manual_search_by_freq_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.MANUAL_SEARCH_BY_FREQ_FILTER
        keywords = self.dvbCheck_keywords.MANUAL_SEARCH_BY_FREQ_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__manual_search_by_freq_checkpoint.__name__)

    def check_manual_search_by_id(self):
        """

        Check whether the manual channel search through the built-in frequency table is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__manual_search_by_id_checkpoint(), 'check_manual_search_by_id'):
            if self.check_search_result():
                if self.check_whether_search_missing():
                    flag = True
        return flag

    def __manual_search_by_id_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.MANUAL_SEARCH_BY_FREQ_FILTER
        keywords = self.dvbCheck_keywords.MANUAL_SEARCH_BY_FREQ_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__manual_search_by_id_checkpoint.__name__)

    def check_quick_scan(self):
        """

        Check whether the quick scan is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__quick_scan_checkpoint(), 'check_quick_scan'):
            if self.check_search_result():
                if self.check_whether_search_missing():
                    flag = True
        return flag

    def __quick_scan_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.QUICK_SCAN_FILTER
        keywords = self.dvbCheck_keywords.QUICK_SCAN_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__quick_scan_checkpoint.__name__)

    def check_search_process(self):
        """

        Check whether the search is in progress.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__search_process_checkpoint(), 'check_search_process'):
            flag = True
        return flag

    def __search_process_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.SEARCH_PROCESS_FILTER
        keywords = self.dvbCheck_keywords.SEARCH_PROCESS_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__search_process_checkpoint.__name__)
        log_filter_driver = self.dvbCheck_keywords.SEARCH_PROCESS_FILTER_DRIVER
        keywords_driver = self.dvbCheck_keywords.SEARCH_PROCESS_KEYWORDS_DRIVER
        # self.check_driver_output(log_filter_driver, keywords_driver, self.__search_process_checkpoint.__name__)
        self.check_logcat_output(log_filter_driver, keywords_driver, p_conf_check_time,
                                 self.__search_process_checkpoint.__name__)

    def check_search_result(self):
        """

        Check whether the search is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__search_result_checkpoint(), 'check_search_result'):
            flag = True
        return flag

    def __search_result_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter_driver = self.dvbCheck_keywords.SEARCH_RESULT_FILTER_DRIVER
        keywords_driver = self.dvbCheck_keywords.SEARCH_RESULT_KEYWORDS_DRIVER
        # self.check_driver_output(log_filter_driver, keywords_driver, self.__search_result_checkpoint.__name__)
        self.check_logcat_output(log_filter_driver, keywords_driver, p_conf_check_time,
                                 self.__search_result_checkpoint.__name__)
        log_filter = self.dvbCheck_keywords.SEARCH_RESULT_FILTER
        keywords = self.dvbCheck_keywords.SEARCH_RESULT_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__search_result_checkpoint.__name__)

    def check_whether_search_missing(self):
        """

        Check whether the search channel is missing.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        flag = False
        self.reset()
        if self.__check_thread(self.__whether_search_missing_checkpoint(), 'check_whether_search_missing'):
            flag = True
        return flag

    def __whether_search_missing_checkpoint(self):
        """

        Set the keywords and check whether it is found in the log.

        Args:
            video_name: video source to play

        Returns:
            None

        """
        search_log_filter = self.dvbCheck_keywords.SEARCH_CHANNEL_NUMBER_FILTER
        popen = subprocess.Popen(f'adb -s {self.serialnumber} shell {search_log_filter}'.split(), stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
        catch_log = popen.stdout.readline()
        search_channel_number = re.findall(r'size=(\d+)', str(catch_log))[0]
        logging.info(f'searched channel number is :{search_channel_number}')
        video_channel_number = str(self.get_channel_number_ffprobe())
        logging.info(f'video channel number is :{video_channel_number}')
        db_channel_number = self.__get_db_channel()
        logging.info(f'tv.db channel number is :{db_channel_number}')
        if search_channel_number == video_channel_number and video_channel_number == db_channel_number:
            logging.info('channel is searched all.')
            self.flag = True
        else:
            logging.info('channel is missing.')
            self.flag = False

    def __check_search_thread(self):
        """

        Call search channel check interface:
            check_search_process()
            check_search_result()
            check_whether_search_missing()

        Returns:
            None

        """
        logging.info("start search check thread")
        self.check_search_thread_pool()
        return self.flag

    def __check_search(self, func):
        eval(func)

    def check_search_thread_pool(self):
        common_func_list = ["self.check_search_process()", "self.check_search_result()",
                            "self.check_whether_search_missing()"]
        common_task_pool = threadpool.ThreadPool(4)
        requests = threadpool.makeRequests(self.__check_search, common_func_list)
        [common_task_pool.putRequest(req) for req in requests]

    def check_switch_channel(self):
        """

        Check whether the switch channel is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__switch_channel_checkpoint(), 'check_switch_channel'):
            if self.check_av_match():
                flag = True
        return flag

    def __switch_channel_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.SWITCH_CHANNEL_FILTER
        keywords = self.dvbCheck_keywords.SWITCH_CHANNEL_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__switch_channel_checkpoint.__name__)

    def check_av_match(self):
        """

        Check whether audio and video is sync after switch channel.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__av_match_checkpoint(), 'check_av_match'):
            flag = True
        return flag

    def get_pid_before_switch(self):
        """

        Get the pid of video before switch channel.

        Returns:
            String: video　pid
            String: audio pid

        """
        log_filter = self.dvbCheck_keywords.AV_MATCH_FILTER
        self.VIDEO_PID_BEFORE = \
            re.findall(r'pid:(\S+)', os.popen(f'adb -s {self.serialnumber} shell {log_filter}').read())[0]
        self.AUDIO_PID_BEFORE = \
            re.findall(r'pid:(\S+)', os.popen(f'adb -s {self.serialnumber} shell {log_filter}').read())[1]
        logging.info(f'current av pid before switch channel is :{self.VIDEO_PID_BEFORE} {self.AUDIO_PID_BEFORE}')
        return self.VIDEO_PID_BEFORE, self.AUDIO_PID_BEFORE

    def __av_match_checkpoint(self, timeout=100):
        """
        Get the video pid after switch channel and check whether it is same as the pid before switching.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.AV_MATCH_FILTER
        start_time = time.time()
        while time.time() - start_time < timeout:
            pid = re.findall(r'pid:(\S+)', os.popen(f'adb -s {self.serialnumber} shell {log_filter}').read())
            if len(pid) == 2:
                video_pid_after = pid[0]
                audio_pid_after = pid[1]
                logging.info(f'current av pid after switch channel is :{video_pid_after} {audio_pid_after}')
                if ((self.VIDEO_PID_BEFORE != video_pid_after and self.AUDIO_PID_BEFORE != audio_pid_after) or
                        (self.VIDEO_PID_BEFORE == video_pid_after and self.AUDIO_PID_BEFORE == audio_pid_after)):
                    self.flag = True
                    logging.info('av is match after switch channel')
                    break
                else:
                    self.flag = False
                    logging.info('av is not match after switch channel')

    def check_start_pvr_recording(self, timed_sleep_time=0):
        """

        Check whether start pvr timely recording is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        start_time = time.time()
        if self.check_udisk():
            if self.__check_thread(self.__start_pvr_recording_checkpoint(), 'check_start_pvr_recording'):
                end_time = time.time()
                sleep_time = int(end_time - start_time)
                if timed_sleep_time:
                    if sleep_time - timed_sleep_time < 5:
                        flag = True
                    else:
                        flag = False
                else:
                    flag = True
        return flag

    def __start_pvr_recording_checkpoint(self):
        """

        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.START_PVR_FILTER
        keywords = self.dvbCheck_keywords.START_PVR_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__start_pvr_recording_checkpoint.__name__)
        log_filter_driver = self.dvbCheck_keywords.START_PVR_FILTER_DRIVER
        dvr_output = re.findall(r'dvr(\w+)PES',
                                os.popen(f'adb -s {self.serialnumber} shell {log_filter_driver}').read())
        if not dvr_output:
            self.flag = True
        else:
            self.flag = False

    def check_stop_pvr_recording(self):
        """

        Check whether stop pvr recording is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__stop_pvr_recording_checkpoint(), 'check_stop_pvr_recording'):
            flag = True
        return flag

    def __stop_pvr_recording_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.STOP_PVR_FILTER
        keywords = self.dvbCheck_keywords.STOP_PVR_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__stop_pvr_recording_checkpoint.__name__)

    def check_pvr_auto_stop_recording(self):
        """

        Check whether the pvr recording will stop automatically when the disk is full.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__pvr_auto_stop_recording_checkpoint(), 'check_pvr_auto_stop_recording'):
            flag = True
        return flag

    def __pvr_auto_stop_recording_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.PVR_AUTO_STOP_FILTER
        keywords = self.dvbCheck_keywords.PVR_AUTO_STOP_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__pvr_auto_stop_recording_checkpoint.__name__)

    def check_timed_recording(self):
        """

        Check whether add pvr timed recording is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__timed_recording_checkpoint(), 'check_timed_recording'):
            flag = True
        return flag

    def __timed_recording_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.TIMED_RECORDING_FILTER
        keywords = self.dvbCheck_keywords.TIMED_RECORDING_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__timed_recording_checkpoint.__name__)

    def check_delete_recording_timer(self):
        """

        Check whether delete pvr recording timer is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__delete_recording_checkpoint(), 'check_delete_recording_timer'):
            flag = True
        return flag

    def __delete_recording_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.DELETE_TIMED_RECORDING_FILTER
        keywords = self.dvbCheck_keywords.DELETE_TIMED_RECORDING_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__delete_recording_checkpoint.__name__)

    def check_pvr_start_play(self):
        """

        Check whether start pvr play is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__pvr_start_play_checkpoint(), 'check_pvr_start_play'):
            if self.__check_thread(self.__video_track_compare_checkpoint(), 'check_pvr_start_play'):
                flag = True
        return flag

    def __pvr_start_play_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.PVR_START_PALY_FILTER
        keywords = self.dvbCheck_keywords.PVR_START_PALY_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__pvr_start_play_checkpoint.__name__)
        if self.flag:
            log_filter_driver = self.dvbCheck_keywords.START_PVR_FILTER_DRIVER
            dvr_output = re.findall(r'dvr(\w+)section',
                                    os.popen(f'adb -s {self.serialnumber} shell {log_filter_driver}').read())
            if not dvr_output:
                self.flag = True
            else:
                self.flag = False
        else:
            return

    def check_pvr_ff(self):
        """

        Check whether pvr fast forward is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__pvr_ff_checkpoint(), 'check_pvr_ff'):
            flag = True
        return flag

    def __pvr_ff_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.PVR_FF_FILTER
        keywords = self.dvbCheck_keywords.PVR_FF_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__pvr_ff_checkpoint.__name__)

    def check_pvr_fb(self):
        """

        Check whether pvr rewind is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__pvr_fb_checkpoint(), 'check_pvr_fb'):
            flag = True
        return flag

    def __pvr_fb_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.PVR_FB_FILTER
        keywords = self.dvbCheck_keywords.PVR_FB_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__pvr_fb_checkpoint.__name__)

    def check_pvr_seek(self, pos):
        """

        Check whether pvr seek is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__pvr_seek_checkpoint(), 'check_pvr_seek'):
            # if self.__check_thread(self.__pvr_seek_pos_checkpoint(pos), 'check_pvr_seek_pos'):
            flag = True
        return flag

    def __pvr_seek_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.PVR_SEEK_FILTER
        keywords = self.dvbCheck_keywords.PVR_SEEK_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__pvr_seek_checkpoint.__name__)

    def __pvr_seek_pos_checkpoint(self, pos, timeout=60):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.PVR_SEEK_POS_FILTER
        keywords = self.dvbCheck_keywords.PVR_SEEK_POS_KEYWORDS
        start_time = time.time()
        self.root()
        self.flag = False
        logfilter = f'adb -s {self.serialnumber} shell ' + log_filter
        logging.info(f'log filter cmd is : {logfilter}')
        popen = subprocess.Popen(logfilter.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        logging.info(f"keywords: {keywords}")
        while time.time() - start_time < timeout:
            if popen:
                check_log = popen.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                match_result = re.findall(keywords[0], check_log)
                if match_result:
                    logging.info(f"check output keyword: {match_result}")
                    seek_pos = int(re.findall(r'time--(\d+)', str(match_result))[0])
                    logging.info(f'seek position is :{seek_pos}')
                    if seek_pos == pos * 1000:
                        logging.info('seek position is correct.')
                        self.flag = True
                    else:
                        logging.info('seek position is not meet expectations.')
                        self.flag = False
                    break
        if popen.poll() is None:
            os.kill(popen.pid, signal.SIGTERM)
        return self.flag

    def check_pvr_current_seek(self, pos):
        """

        Check whether pvr seek based on current position is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__pvr_seek_checkpoint(), 'check_pvr_seek'):
            # if self.__check_thread(self.__pvr_current_seek_pos_checkpoint(pos), 'check_pvr_current_seek_pos'):
            flag = True
        return flag

    def __pvr_current_seek_pos_checkpoint(self, pos, timeout=60):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        counter = 0
        seek_pos = 0
        current_pos = {}
        log_filter = self.dvbCheck_keywords.PVR_CURRENT_SEEK_POS_FILTER
        keywords = self.dvbCheck_keywords.PVR_CURRENT_SEEK_POS_KEYWORDS
        start_time = time.time()
        self.root()
        logfilter = f'adb -s {self.serialnumber} shell ' + log_filter
        logging.info(f'log filter cmd is : {logfilter}')
        popen = subprocess.Popen(logfilter.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        logging.info(f"keywords: {keywords}")
        while time.time() - start_time < timeout:
            if popen:
                with open('seek.log', 'a', encoding='utf-8') as f:
                    check_log = popen.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                        .encode('unicode_escape') \
                        .decode('utf-8', errors='ignore') \
                        .replace('\\r', '\r') \
                        .replace('\\n', '\n') \
                        .replace('\\t', '\t')
                    f.write(check_log)
                    f.close()
                seek_match_result = re.findall(keywords[0], check_log)
                if seek_match_result:
                    logging.info(f"check output keyword: {seek_match_result}")
                    seek_pos = int(re.findall(r'seeked\(off:(\d+)', str(seek_match_result))[0])
                    logging.info(f'seek position is :{seek_pos}')
                    break
        with open('seek.log', 'r') as f:
            for check_log in f:
                current_match_result = re.findall(keywords[1], check_log)
                if current_match_result:
                    logging.info(f"check output keyword: {current_match_result}")
                    current_pos_match = int(re.findall(r'cur\[(\d+)', str(current_match_result))[0])
                    current_pos[counter] = current_pos_match
                    counter += 1
            logging.info(f'current position is :{current_pos}')
            f.close()
        if abs(pos * 1000) - abs(seek_pos - current_pos[(len(current_pos)-1)]) < 1000:
            logging.info('seek position is correct.')
            self.flag = True
        else:
            logging.info('seek position is not meet expectations.')
            self.flag = False
        if popen.poll() is None:
            os.kill(popen.pid, signal.SIGTERM)
        return self.flag

    def remove_tmp_log(self):
        if os.path.isfile('./seek.log'):
            try:
                os.remove('./seek.log')
            except BaseException as e:
                print(e)
        else:
            logging.info('The dvb tmp log is not exit.')

    def check_pvr_pause(self):
        """

        Check whether pvr pause is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__pvr_pause_checkpoint(), 'check_pvr_pause'):
            flag = True
        return flag

    def __pvr_pause_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.PVR_PAUSE_FILTER
        keywords = self.dvbCheck_keywords.PVR_PAUSE_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__pvr_pause_checkpoint.__name__)

    def check_pvr_resume(self):
        """

        Check whether pvr resume is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__pvr_resume_checkpoint(), 'check_pvr_resume'):
            flag = True
        return flag

    def __pvr_resume_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.PVR_RESUME_FILTER
        keywords = self.dvbCheck_keywords.PVR_RESUME_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__pvr_resume_checkpoint.__name__)

    def check_pvr_stop(self):
        """

        Check whether exit pvr playback is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__pvr_stop_checkpoint(), 'check_pvr_stop'):
            flag = True
        return flag

    def __pvr_stop_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.PVR_STOP_FILTER
        keywords = self.dvbCheck_keywords.PVR_STOP_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__pvr_stop_checkpoint.__name__)

    def check_timeshift_start(self):
        """

        Check whether start time shift is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__timeshift_start_checkpoint(), 'check_timeshift_start'):
            flag = True
        return flag

    def __timeshift_start_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.TIMESHIFT_START_FILTER
        keywords = self.dvbCheck_keywords.TIMESHIFT_START_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__timeshift_start_checkpoint.__name__)

    def check_timeshift_ff(self):
        """

        Check whether time shift fast forward is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__timeshift_ff_checkpoint(), 'check_timeshift_ff'):
            flag = True
        return flag

    def __timeshift_ff_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.TIMESHIFT_FF_FILTER
        keywords = self.dvbCheck_keywords.TIMESHIFT_FF_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__timeshift_ff_checkpoint.__name__)

    def check_timeshift_fb(self):
        """

        Check whether time shift rewind is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__timeshift_fb_checkpoint(), 'check_timeshift_fb'):
            flag = True
        return flag

    def __timeshift_fb_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.TIMESHIFT_FB_FILTER
        keywords = self.dvbCheck_keywords.TIMESHIFT_FB_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__timeshift_fb_checkpoint.__name__)

    def check_timeshift_seek(self):
        """

        Check whether time shift seek is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__timeshift_seek_checkpoint(), 'check_timeshift_seek'):
            flag = True
        return flag

    def __timeshift_seek_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.TIMESHIFT_SEEK_FILTER
        keywords = self.dvbCheck_keywords.TIMESHIFT_SEEK_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__timeshift_seek_checkpoint.__name__)

    def check_timeshift_pause(self):
        """

        Check whether time shift pause is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__timeshift_pause_checkpoint(), 'check_timeshift_pause'):
            flag = True
        return flag

    def __timeshift_pause_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.TIMESHIFT_PAUSE_FILTER
        keywords = self.dvbCheck_keywords.TIMESHIFT_PAUSE_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__timeshift_pause_checkpoint.__name__)

    def check_timeshift_stop(self):
        """

        Check whether exit time shift is successful.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.reset()
        flag = False
        if self.__check_thread(self.__timeshift_stop_checkpoint(), 'check_timeshift_stop'):
            flag = True
        return flag

    def __timeshift_stop_checkpoint(self):
        """
        Set the keywords and check whether it is found in the log.

        Returns:
            None

        """
        log_filter = self.dvbCheck_keywords.TIMESHIFT_STOP_FILTER
        keywords = self.dvbCheck_keywords.TIMESHIFT_STOP_KEYWORDS
        self.check_logcat_output(log_filter, keywords, p_conf_check_time,
                                 self.__timeshift_stop_checkpoint.__name__)

    def check_play_status_main_thread(self, timeout=10):
        """

        Check whether the playback is normal and system is normal in main thread.
        The next action cannot be performed until the execution is completed.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        if not timeout:
            timeout = p_conf_check_play_time
        self.check_common_thread()
        self.check_abnormal_thread()
        time.sleep(timeout)
        self.thread_exit_flag = 1
        logging.info('check play status thread is finished.')

    def check_play_status_sub_thread(self):
        """

        Check whether the playback is normal and system is normal in child thread.
        After starting,it will continue to run until the end of the case or the check fails.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        self.check_common_thread()
        self.check_abnormal_thread()

    def check_abnormal_thread(self):
        thread_list = []
        abnormal_func_list = [self.check_abnormal]
        abnormal_func_name_list = ["self.check_abnormal()"]
        for i in range(len(abnormal_func_list)):
            check_thread = threading.Thread(target=abnormal_func_list[i], name=abnormal_func_name_list[i])
            check_thread.daemon = 1
            thread_list.append(check_thread)
        for i in thread_list:
            i.start()

    def check_common_thread(self):
        self.flag = True
        thread_list = []
        common_func_list = [self.checkAudio, self.checkavsync, self.check_stuck, self.checkFrame, self.checkHWDecodePlayback]
        common_func_name_list = ["self.checkAudio()", "self.checkavsync()", "self.check_stuck()", "self.checkFrame()", "self.checkHWDecodePlayback()"]
        for i in range(len(common_func_list)):
            check_thread = threading.Thread(target=common_func_list[i], name=common_func_name_list[i])
            check_thread.daemon = 1
            thread_list.append(check_thread)
        for i in thread_list:
            i.start()

    def checkavsync(self):
        self.flag = True
        while 1:
            if self.thread_exit_flag:
                break
            logging.info('check av sync')
            assert playerCheck.checkavsync()

    def check_stuck(self):
        self.flag = True
        while 1:
            if self.thread_exit_flag:
                break
            logging.info('check stuck')
            assert playerCheck.check_stuck()

    def checkFrame(self):
        self.flag = True
        while 1:
            if self.thread_exit_flag:
                break
            logging.info('check Frame')
            assert playerCheck.checkFrame()

    def checkHWDecodePlayback(self):
        self.flag = True
        while 1:
            if self.thread_exit_flag:
                break
            logging.info('check HWDecode Playback')
            assert playerCheck.checkHWDecodePlayback()

    def checkAudio(self):
        self.flag = True
        while 1:
            if self.thread_exit_flag:
                break
            logging.info('check Audio')
            assert playerCheck.checkAudio()

    def check_abnormal(self):
        self.flag = True
        while 1:
            if self.thread_exit_flag:
                break
            logging.info('check abnormal')
            assert playerCheck.check_abnormal()

    def check_logcat_output(self, log_filter, keywords, timeout, name='', getDuration=False):
        """

        Check whether it can find keywords in the log.

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        logging.info(f"name is :{name}")
        counter = 0
        checked_log_dict = {}
        checked_log_list = []
        logging.info("check output: logcat")
        start_time = time.time()
        self.root()
        logfilter = f'adb -s {self.serialnumber} shell ' + log_filter
        logging.info(f'log filter cmd is : {logfilter}')
        self.abnormal_threadpool()
        # dvb_check_log = open('dvb_check.log', 'w')
        popen = subprocess.Popen(logfilter.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        flags = fcntl.fcntl(popen.stdout, fcntl.F_GETFL)
        flags |= os.O_NONBLOCK
        fcntl.fcntl(popen.stdout, fcntl.F_SETFL, flags)
        logging.info(f"keywords: {keywords}")
        while time.time() - start_time < timeout:
            if popen:
                check_log = popen.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                # for keyword in keywords:
                #     if keyword in check_log:
                for i in range(len(keywords)):
                    match_result = re.findall(keywords[i], check_log)
                    if match_result:
                        logging.info(f"check output keyword: {match_result}")
                        if match_result[0] not in checked_log_list:
                            checked_log_list.append(match_result[0])
                            checked_log_dict[i] = check_log
                            counter += 1
                        else:
                            break
            if counter == len(keywords):
                self.flag = True
                self.checked_log_dict = checked_log_dict
                logging.debug(f"{name} keywords found:{self.flag}")
                logging.debug(f"self.checked_log_dict: {self.checked_log_dict}")
                break
            else:
                self.flag = False
        if popen.poll() is None:
            os.kill(popen.pid, signal.SIGTERM)
        # os.kill(popen.pid, signal.SIGTERM)
        # self.clear_logcat()
        return self.flag

    def __get_db_channel(self):
        """

        Get the number of channels in the video.

        Returns:
            String: the number of channel

        """
        channel_number = self.run_shell_cmd(self.dvbCheck_keywords.SELECT_SQL)[1]
        return channel_number

    def get_channel_id(self, timeout=30):
        """

        Get the id of channels in the video.

        Returns:
            list: the id of channel

        """
        for i in range(timeout):
            if self.check_is_playing():
                channel_id_tuple = self.run_shell_cmd(self.dvbCheck_keywords.GET_CHANNEL_ID)
                channel_id = ''.join(channel_id_tuple[1]).split()
                print(channel_id)
                return channel_id
            else:
                time.sleep(3)

    def check_is_playing(self):
        frame_start = self.run_shell_cmd(self.dvbCheck_keywords.FRAME_COUNT)[1]
        logging.info(f'frame count start is :{frame_start}')
        time.sleep(1)
        frame_end = self.run_shell_cmd(self.dvbCheck_keywords.FRAME_COUNT)[1]
        frame_during = int(frame_end) - int(frame_start)
        logging.info(f'frame count during 2 seconds is :{frame_during}')
        if frame_during > 0:
            flag = True
        else:
            flag = False
        return flag

    def check_aspect_ratio(self, dispaly_mode=1):
        flag = False
        log_filter = self.dvbCheck_keywords.ASPECT_RATIO_FILTER
        keywords = ""
        if dispaly_mode == 0:
            keywords = self.dvbCheck_keywords.CHECK_ASPECT_RATIO_AUTO
        elif dispaly_mode == 1:
            keywords = self.dvbCheck_keywords.CHECK_ASPECT_RATIO_4_3
        elif dispaly_mode == 2:
            keywords = self.dvbCheck_keywords.CHECK_ASPECT_RATIO_PANORAMA
        elif dispaly_mode == 3:
            keywords = self.dvbCheck_keywords.CHECK_ASPECT_RATIO_16_9
        elif dispaly_mode == 4:
            keywords = self.dvbCheck_keywords.CHECK_ASPECT_RATIO_DOT_BY_DOT
        if self.check_logcat_output(log_filter, keywords, p_conf_check_time):
            flag = True
        return flag

    def check_audio_track_switch(self):
        flag = False
        if self.__check_thread(self.__audio_track_switch_checkpoint(), 'check_audio_track_switch'):
            flag = True
        return flag

    def __audio_track_switch_checkpoint(self):
        self.flag = False
        log_filter = self.dvbCheck_keywords.AUDIO_TRACK_SWITCH_FILTER
        keywords = self.dvbCheck_keywords.AUDIO_TRACK_SWITCH_KEYWORDS
        if self.check_logcat_output(log_filter, keywords, p_conf_check_time):
            self.flag = True
        return self.flag

    def __video_track_compare_checkpoint(self):
        """
        获取录制文件回放时的pid相关信息，计算其中audio和subtitle track数量，与片源对应pid的信息进行对比

        Returns:

        """
        logging.info('start video track compare checkpoint')
        self.flag = False
        video_source_track_number = self.get_video_source_track_number()
        record_video_track_number = self.get_record_video_track_number()
        if record_video_track_number == video_source_track_number:
            self.flag = True
            logging.info('The tracks of recording file match the video source.')
        else:
            logging.info('The tracks of recording file is not match the video source.')
        return self.flag

    def get_record_pid(self, timeout=5):
        pvr_recorded_pid_list = []
        log_filter = self.dvbCheck_keywords.VIDEO_TRACK_COMPARE_FILTER
        keywords = self.dvbCheck_keywords.VIDEO_TRACK_COMPARE_KEYWORDS
        start_time = time.time()
        self.root()
        logfilter = f'adb -s {self.serialnumber} shell ' + log_filter
        logging.info(f'log filter cmd is : {logfilter}')
        popen = subprocess.Popen(logfilter.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        logging.info(f"keywords: {keywords}")
        logging.info(f'timeout is : {timeout}')
        while time.time() - start_time < timeout:
            if popen:
                check_log = popen.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                match_result = re.findall(keywords[0], check_log)
                if match_result:
                    logging.info(f'match result : {match_result}')
                    record_video_pid = re.findall(r'pid: (.*)', match_result[0])[0]
                    if record_video_pid not in pvr_recorded_pid_list:
                        pvr_recorded_pid_list.append(record_video_pid)
        if popen.poll() is None:
            os.kill(popen.pid, signal.SIGTERM)
        logging.info(f'video pcr pid list is: {pvr_recorded_pid_list}')
        return pvr_recorded_pid_list

    def get_record_video_track_number(self, timeout=5):
        logging.info(f"name is : get video track number")
        counter = 0
        checked_log_dict = {}
        checked_log_list = []
        log_filter = self.dvbCheck_keywords.VIDEO_TRACK_NUMBER_FILTER
        keywords = self.dvbCheck_keywords.VIDEO_TRACK_NUMBER_KEYWORDS
        start_time = time.time()
        self.root()
        logfilter = f'adb -s {self.serialnumber} shell ' + log_filter
        logging.info(f'log filter cmd is : {logfilter}')
        popen = subprocess.Popen(logfilter.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        logging.info(f"keywords: {keywords}")
        while time.time() - start_time < timeout:
            if popen:
                check_log = popen.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                for i in range(len(keywords)):
                    match_result = re.findall(keywords[i], check_log)
                    if match_result:
                        logging.info(f"check output keyword: {match_result}")
                        if match_result[0] not in checked_log_list:
                            checked_log_list.append(match_result[0])
                            checked_log_dict[i] = check_log
                            counter += 1
            self.checked_log_dict = checked_log_dict
            # logging.debug(f"self.checked_log_dict: {self.checked_log_dict}")
        if popen.poll() is None:
            os.kill(popen.pid, signal.SIGTERM)
        record_video_track_number = counter
        logging.info(f'record video track number is : {record_video_track_number}')
        return record_video_track_number

    def get_video_source_track_number(self):
        video_pid_list = []
        pvr_recorded_pid_list = self.get_record_pid()
        pvr_current_recording_pid = ''
        video_pid = ''
        video_pid_next = ''
        count = 0
        start_line = 0
        end_line = 0
        line_num = 0
        try:
            if os.path.isfile('./dvb.log'):
                logging.info('dvb.log is found')
            else:
                logging.info('dvb.log is not found')
            with open('./dvb.log', 'r', encoding='utf-8') as f:
                for line in f:
                    if 'pvr_current_recording_pid' in line:
                        pvr_current_recording_pid = re.findall(r'pvr_current_recording_pid : (.*)', line)[0]
                        logging.info(f'pvr current recording pid is : {pvr_current_recording_pid}')
                f.close()
            if pvr_current_recording_pid in pvr_recorded_pid_list:
                video_pid = pvr_current_recording_pid
                logging.info('the program that pvr start recording with the recorded program is match.')
            else:
                logging.info('the program that pvr start recording with the recorded program is not match.')
            with open('./dvb.log', 'r', encoding='utf-8') as f:
                check_log = f.readlines()
                for i in range(len(check_log)):
                    get_video_pid = re.findall(r'\[(.*?)\]: Video', check_log[i])
                    if get_video_pid:
                        video_pid_list.append(get_video_pid[0])
                logging.info(f'video pid list : {video_pid_list}')
                for i in range(len(video_pid_list)):
                    if video_pid_list[i] == video_pid and i+1 in range(len(video_pid_list)):
                        video_pid_next = video_pid_list[i+1]
                        logging.info(f'video pid next is : {video_pid_next}')
                        break
                    else:
                        logging.info('The current pid is the only one or the last.')
            with open('./dvb.log', 'r', encoding='utf-8') as f:
                line_num = len(f.readlines())
                logging.info(f'line number is : {line_num}')
                f.close()
            with open('./dvb.log', 'r', encoding='utf-8') as f:
                for num, element in enumerate(f):
                    if video_pid_next:
                        if f'[{video_pid}]: Video' in element:
                            logging.info(f'start line num is: {num} content: {element}')
                            start_line = num
                        if f'[{video_pid_next}]: Video' in element:
                            logging.info(f'end line num is: {num} content: {element}')
                            end_line = num
                            break
                    else:
                        if f'[{video_pid}]: Video' in element:
                            logging.info(f'start line num is: {num} content: {element}')
                            start_line = num
                            end_line = line_num - 1
                            # end_line = num + 20
                            logging.info(f'end line num is: {end_line}')
                            break
                f.close()
            with open('./dvb.log', 'r', encoding='utf-8') as f:
                track_list = f.readlines()
                for i in range(start_line, end_line-1):
                    if 'Audio' in track_list[i+1] or 'Subtitle' in track_list[i+1]:
                        count += 1
                        logging.info(f'line is : {i+1} content is :{track_list[i+1]}')
                f.close()
            video_track_number = count
            logging.info(f'video source track number is {video_track_number}')
            return video_track_number
        except FileNotFoundError:
            logging.info(f'dvb.log is not found.')

    def get_pvr_current_recording_pid(self, timeout=10):
        logging.info('get pvr current recording video pid.')
        pvr_current_recording_pid = ''
        log_filter = self.dvbCheck_keywords.VIDEO_TRACK_COMPARE_FILTER
        keywords = self.dvbCheck_keywords.VIDEO_TRACK_COMPARE_KEYWORDS
        start_time = time.time()
        self.root()
        logfilter = f'adb -s {self.serialnumber} shell ' + log_filter
        logging.info(f'log filter cmd is : {logfilter}')
        popen = subprocess.Popen(logfilter.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        logging.info(f"keywords: {keywords}")
        while time.time() - start_time < timeout:
            if popen:
                check_log = popen.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                match_result = re.findall(keywords[0], check_log)
                if match_result:
                    logging.info(f'match result : {match_result}')
                    pvr_current_recording_pid = re.findall(r'pid: (.*)', match_result[0])[0]
                    logging.info(f'video pid is: {pvr_current_recording_pid}')
                    break
        if popen.poll() is None:
            os.kill(popen.pid, signal.SIGTERM)
        with open('dvb.log', 'a', encoding='utf-8') as f:
            f.write(f'pvr_current_recording_pid : {pvr_current_recording_pid}')
            f.close()

    def get_video_channel_id(self):
        start_line = 0
        end_line = 0
        channel_id_list = []
        try:
            if os.path.isfile('./dvb.log'):
                logging.info('dvb.log is found')
            else:
                logging.info('dvb.log is not found')
            with open('./dvb.log', 'r', encoding='utf-8') as f:
                for num, element in enumerate(f):
                    if f'Duration:' in element:
                        logging.info(f'start line num is: {num} content: {element}')
                        start_line = num
                    if 'Unsupported' in element:
                        logging.info(f'end line num is: {num} content: {element}')
                        end_line = num
                        break
                f.close()
            with open('./dvb.log', 'r', encoding='utf-8') as f:
                track_list = f.readlines()
                for i in range(start_line, end_line):
                    channel_id = re.findall(r'Program (\d+)', track_list[i])
                    if channel_id:
                        channel_id_list.append(channel_id[0])
                f.close()
            logging.info(f'channel id is : {channel_id_list}')
            return channel_id_list
        except FileNotFoundError:
            logging.info(f'dvb.log is not found.')

    def get_subtitle_mode(self, video_name):
        """
            To get the subtitle type, need to download the test stream
            to the test running environment and analyze it through mediainfo.

            Due to the special symbol problem, change the following part of
            the test stream to a simpler name:
                1. [瑞典码流].Teletext.Sweden. sub&teletext.ts --> dvb.ts
                2. subtitle_scte20_scte27.ts
                3. CC-subtitle_150_ems.ts
                4. [1080pH265_60.000fps_9070Kbps]Wetek-Astra-2m.ts --> Wetek-Astra-2m.ts
                5. [EU_DVB-T](Audio Language)Audio_cat_vol_ac3_ad.ts --> Audio_cat_vol_ac3_ad.ts
                6. France 554MHZ-EPG8day now next -rating4+-1 now next time different.ts -->now_next_time_different.ts
                7. BBC MUX UH.ts --> BBC_MUX_UH.ts
                8. [4KH265_16.7Mbps_30.000fps_8bit]worldcup2014_8bit_15m_30p.ts --> worldcup2014_8bit_15m_30p.ts

            For example, to analyze "[瑞典码流].Teletext.Sweden. sub&teletext.ts",
            the usage is: dvb_check.get_subtitle_mode('dvb.ts')
        """
        p_subtitle_mode = ''
        self.get_target(f'video/dvb/subtitle/{video_name}')
        p_video_path = f'./res/video/dvb/subtitle/{video_name}'
        logging.debug(f'p_video_path :{p_video_path}')
        p_subtitle_info = os.popen(f'mediainfo {p_video_path} | grep -E "Format|Muxing mode"').read()
        logging.info(f'p_subtitle_info : {p_subtitle_info}')
        if 'SCTE 20' in p_subtitle_info:
            p_subtitle_mode = 'scte27'
        elif 'DTVCC Transport' in p_subtitle_info:
            p_subtitle_mode = 'cc'
        elif 'DVB Subtitle' in p_subtitle_info:
            p_subtitle_mode = 'Dvb'
        logging.info(f'subtitle mode is : {p_subtitle_mode}')
        self.run_terminal_cmd(f"rm {p_video_path}")
        return p_subtitle_mode

    def check_subtitle_current_language(self, switch_type=1):
        flag = False
        if self.__check_thread(self.__subtitle_current_language_checkpoint(switch_type), 'check_subtitle_current_language'):
            flag = True
        return flag

    def __subtitle_current_language_checkpoint(self, switch_type=1):
        self.flag = False
        subtitle_current_language = self.get_subtitle_current_language()
        logging.info(f'subtitle current language : {subtitle_current_language}')
        subtitle_switch_language = self.get_subtitle_switch_language(switch_type)
        logging.info(f'subtitle switch language : {subtitle_switch_language}')
        if subtitle_current_language == subtitle_switch_language:
            self.flag = True

    def get_subtitle_current_language(self, timeout=10):
        logging.info('get subtitle current language.')
        subtitle_current_pid = ''
        subtitle_current_language = []
        log_filter = self.dvbCheck_keywords.SUBTITLE_CURRENT_LANGUAGE_FILTER
        keywords = self.dvbCheck_keywords.SUBTITLE_CURRENT_LANGUAGE_KEYWORDS
        start_time = time.time()
        self.root()
        logfilter = f'adb -s {self.serialnumber} shell ' + log_filter
        logging.info(f'log filter cmd is : {logfilter}')
        popen = subprocess.Popen(logfilter.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        logging.info(f"keywords: {keywords}")
        while time.time() - start_time < timeout:
            if popen:
                check_log = popen.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                match_result = re.findall(keywords[0], check_log)
                if match_result:
                    logging.info(f'match result : {match_result}')
                    subtitle_current_pid = hex(int(re.findall(r'pid=(.*)', match_result[0])[0]))
                    logging.info(f'subtitle pid is: {subtitle_current_pid}')
                    break
        if popen.poll() is None:
            os.kill(popen.pid, signal.SIGTERM)
        with open('./dvb.log', 'r', encoding='utf-8') as f:
            track_list = f.readlines()
            for i in range(len(track_list)):
                subtitle_current_language = re.findall(rf'\[{subtitle_current_pid}\]\((\S+)\): Subtitle:', track_list[i])
                if len(subtitle_current_language) != 0:
                    break
            f.close()
        return subtitle_current_language[0]

    def get_subtitle_switch_language(self, switch_type=1, timeout=5):
        logging.info('get subtitle switch language.')
        count = 0
        subtitle_language_id_list = []
        subtitle_switch_language = []
        log_filter = self.dvbCheck_keywords.SUBTITLE_SWITCH_LANGUAGE_FILTER
        keywords = self.dvbCheck_keywords.SUBTITLE_SWITCH_LANGUAGE_KEYWORDS
        start_time = time.time()
        subtitle_track_number = self.get_subtitle_track_number()
        self.root()
        logfilter = f'adb -s {self.serialnumber} shell ' + log_filter
        logging.info(f'log filter cmd is : {logfilter}')
        popen = subprocess.Popen(logfilter.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        logging.info(f"keywords: {keywords}")
        while time.time() - start_time < timeout:
            if popen:
                check_log = popen.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                match_result = re.findall(keywords[0], check_log)
                if match_result:
                    logging.info(f"check output keyword: {match_result}")
                    # subtitle_track_number = re.findall(r'LiveTVTest: id=\d+&type=(\d+)', match_result[0])[0]
                    if match_result[0] not in subtitle_language_id_list:
                        subtitle_language_id_list.append(match_result[0])
                        count += 1
                        if count == subtitle_track_number:
                            break
        if popen.poll() is None:
            os.kill(popen.pid, signal.SIGTERM)
        logging.info(f'subtitle language id list is : {subtitle_language_id_list}')
        for i in range(len(subtitle_language_id_list)):
            subtitle_switch_language = re.findall(rf'id={switch_type}&type=.*\|\|\t+(\S+)\t+\|\|', subtitle_language_id_list[i])
            if len(subtitle_switch_language) != 0:
                logging.info(f'subtitle_switch_language: {subtitle_switch_language}')
                break
        if subtitle_switch_language[0] == 'fra':
            subtitle_switch_language[0] = 'fre'
        return subtitle_switch_language[0]

    def get_subtitle_track_number(self):
        count = 0
        try:
            if os.path.isfile('./dvb.log'):
                logging.info('dvb.log is found')
            else:
                logging.info('dvb.log is not found')
            with open('./dvb.log', 'r', encoding='utf-8') as f:
                track_list = f.readlines()
                for i in range(len(track_list)):
                    if 'Subtitle' in track_list[i]:
                        count += 1
                        logging.info(f'line is : {i+1} content is :{track_list[i]}')
                f.close()
            subtitle_track_number = count
            logging.info(f'subtitle track number is {subtitle_track_number}')
            return subtitle_track_number
        except FileNotFoundError:
            logging.info(f'dvb.log is not found.')

    def check_switch_channel_time(self, avg):
        """

        Check whether the average time of switching channel ten times is less than {avg} seconds

        Args:
            avg: Used to compare with the average time

        Returns:
            boolean: True if check is passed, otherwise　false

        """
        switch_time = []
        flag = False
        channel_id = self.get_channel_id()
        logging.info(f'channel_id : {channel_id}')
        self.get_pid_before_switch()
        for i in range(10):
            switch_channel = random.choice(channel_id)
            self.clear_logcat()
            self.run_shell_cmd(
                f"am start -a android.intent.action.VIEW -d content://android.media.tv/channel/{switch_channel}")
            start_time = time.time()
            if self.check_switch_channel():
                end_time = time.time()
                switch_time.append(end_time - start_time)
                logging.info(f'switch channel {i+1} times : {switch_time[i]}')
            else:
                logging.info(f'switch channel is failed.')
                return flag
        avg_time = np.mean(switch_time)
        if avg_time <= avg:
            logging.info(f'switch average time: {avg_time} is less than {avg}s')
            flag = True
        else:
            logging.info(f'switch average time: {avg_time} is greater than {avg}s')
        return flag

    def get_video_path(self, video_format):
        with open('./dvb.log', 'r', encoding='utf-8') as f:
            for line in f:
                if video_format in line:
                    return line

    def get_channel_number_ffprobe(self):
        video_number_list = []
        with open('./dvb.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'nb_programs' in line:
                    video_number = re.findall(r"\d+", line)[0]
                    video_number_list.append(video_number)
                    logging.info(f'find video number : {video_number_list}')
        video_channel_number = sum(list(map(int, video_number_list)))
        return video_channel_number
        # count = 0
        # try:
        #     if os.path.isfile('./dvb.log'):
        #         logging.info('dvb.log is found')
        #     else:
        #         logging.info('dvb.log is not found')
        #     with open('./dvb.log', 'r', encoding='utf-8') as f:
        #         track_list = f.readlines()
        #         for i in track_list:
        #             if f']: Video: ' in i:
        #                 count += 1
        #                 logging.info(f'content is :{i}')
        #         f.close()
        #     video_channel_number = count
        #     return video_channel_number
        # except FileNotFoundError:
        #     logging.info(f'dvb.log is not found.')

    def check_udisk(self):
        if adb.getUUID() != 'emulated':
            logging.info('The u disk is inserted.')
            return True
        else:
            logging.info('Please insert the u disk.')
            return False

    def delete_udisk_recorded(self):
        udisk_id = self.getUUID()
        udisk_path = f'/storage/{udisk_id}/PVR_DIR/'
        try:
            os.popen(f'adb -s {self.serialnumber} shell rm -rf {udisk_path}')
        except Exception as e:
            raise Exception("Can't find the udisk path.")

    def check_is_need_search(self, timeout=p_conf_check_is_need_search_time):
        """

        Judge whether it is necessary to search the channel after pushing the stream.

        Returns:
            bool: True need to search and False don't need.

        """
        flag = True
        if not timeout:
            return flag
        else:
            for i in range(timeout):
                if self.check_is_playing():
                    break
                else:
                    time.sleep(2)
            if self.check_is_playing():
                flag = False
                logging.info('Stream switched, it don\'t need to search')
            else:
                logging.info('Stream is not switched, it need to search')
            return flag

    def expand_logcat_capacity(self):
        self.run_shell_cmd("logcat -G 40m")
        self.run_shell_cmd("renice -n -50 `pidof logd`")

    def clear_multi_frq_program_information(self):
        self.root()
        self.run_shell_cmd('rm -rf /data/vendor/dtvkit/dtvkit.sqlite3')
        self.run_shell_cmd('rm -rf /data/data/com.android.providers.tv/databases/tv.db')
        reboot.reboot_once()
        logging.info('multi frequency program information is cleared successfully.')

    def reset(self):
        logging.info(f"[{self.__class__.__name__}][reset]")
        self.logcat = ""
        # self.remove_tmp_log()
        self.expand_logcat_capacity()

# dvb check demo
#
# dvb_check = DvbCheck()
# dvb = DVB()
# adb.run_shell_cmd(switch_channel) or dvb.switch_channel
# assert dvb_check.check_switch_channel(), 'switch channel failed.'
