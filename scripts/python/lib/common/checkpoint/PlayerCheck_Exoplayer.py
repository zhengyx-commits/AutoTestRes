#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/3/10 下午14:00
# @Author  : jun.yang
# @File    : PlayerCheck_Exoplayer.py
# @Email   : jun.yang1@amlogic.com
# @Ide: PyCharm

import logging
import os
import re
import threadpool
import threading
import time
import pytest
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from lib import get_read_buffer


class PlayerCheck_Exoplayer(PlayerCheck_Base):
    '''
    player checkpoint, support OTT hybrid S IPTV
    '''
    def __init__(self, playerNum=1):
        super().__init__(playerNum=playerNum)
        self.home_play_able = False
        self.seek_advance_able = False
        self.seek_back_able = False

    def get_check_api_result(self, keywords, logFilter, name, getDuration=False, **kwargs):
        timeout = 0
        if len(kwargs) != 0:
            for k, v in kwargs.items():
                if timeout != k:
                    timeout = v
        else:
            timeout = self.get_checkavsync_stuck_time()
        start_time = time.time()
        self.start_check_keywords_thread(keywords, logFilter, self.get_checktime(), name, getDuration)
        if self.flag_check_logcat_output_keywords:
            self.common_threadpool()
            while time.time() - start_time < 50:
                if self.get_abnormal_observer():
                    # logging.info("get abnormal observer")
                    flag_common_threadpool = False
                    self.home_play_able = False
                    self.reset()
                    return flag_common_threadpool, self.checked_log_dict
        self.home_play_able = False
        self.reset()
        return self.flag_check_logcat_output_keywords, self.checked_log_dict

    def check_seek(self, keywords="", logFilter="", seek_advance_able=False, seek_back_able=False):
        """
        check seek: include PIP way
        params are the same as check_stopPlay
        """
        self.seek_advance_able = seek_advance_able
        self.seek_back_able = seek_back_able
        if not keywords:
            keywords = self.exoplayercheck_keywords.SEEK_KEYWORDS
        if not logFilter:
            logFilter = self.exoplayercheck_keywords.SEEK_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_seek.__name__)

    def check_home_play(self, keywords="", logFilter=""):
        """
        check seek: include PIP way
        params are the same as check_stopPlay
        """
        self.home_play_able = True
        if not keywords:
            keywords = self.exoplayercheck_keywords.HOME_PLAY_KEYWORDS
        if not logFilter:
            logFilter = self.exoplayercheck_keywords.HOME_PLAY_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_home_play.__name__)

    def start_check_keywords(self, keywords, log, timeout, name, getDuration=False):
        count = 0
        start_time = time.time()
        primary_pos = None
        current_pos = None
        seek_count = 0
        while time.time() - start_time < 50:
            if len(self.abnormal_observer_list) != 0:
                print("if check abnormal in thread, should exit")
                self.flag_check_logcat_output_keywords = False
                return self.flag_check_logcat_output_keywords, self.checked_log_dict
            outputValue_list = get_read_buffer()
            tmp = ""
            for outputValue in outputValue_list:
                for keyword in keywords:
                    if keyword in outputValue and (tmp != outputValue):
                        tmp = outputValue
                        if name == "check_seek":
                            if keyword == "seekStarted" and "period" in outputValue and seek_count == 0:
                                primary_pos = re.findall(r".*EventLogger: seekStarted \[eventTime=.*mediaPos=(.*), window.*", outputValue)[0]
                                primary_pos = float(primary_pos)
                                self.checked_log_dict[primary_pos] = outputValue
                                seek_count = seek_count + 1
                                logging.info(f"outputValue: {outputValue}")
                                logging.info(f"keyword: {keyword}")
                            elif keyword == "isPlaying" and seek_count == 1:
                                current_pos = re.findall(r".*EventLogger: isPlaying \[eventTime=.*mediaPos=(.*), window.*period=0, false.*", outputValue)[0]
                                current_pos = float(current_pos)
                                self.checked_log_dict[current_pos] = outputValue
                                seek_count = seek_count + 1
                                logging.info(f"outputValue: {outputValue}")
                                logging.info(f"keyword: {keyword}")
                            else:
                                pass
                        elif name == "check_home_play":
                            if keyword == "LauncherX to foreground. The context is com.google.android.apps.tv.launcherx.home.HomeActivity" and count == 0:
                                self.checked_log_dict[keyword] = outputValue
                                count = count + 1
                                logging.info(f"outputValue: {outputValue}")
                                logging.info(f"keyword: {keyword}")
                            else:
                                pass
                        else:
                            pass

            if name == "check_seek" and seek_count == 2:
                if self.seek_advance_able and current_pos > primary_pos:
                    self.flag_check_logcat_output_keywords = True
                    logging.info("seek advance success")
                    break
                elif self.seek_back_able and current_pos < primary_pos:
                    self.flag_check_logcat_output_keywords = True
                    logging.info("seek back success")
                    break
                else:
                    pass
            elif name == "check_home_play" and count == 1:
                self.flag_check_logcat_output_keywords = True
                logging.info("check home play success")
                break
            else:
                pass

        logging.info(f"{name} keywords found:{self.flag_check_logcat_output_keywords}")
        logging.info(f"checked_log_dict: {self.checked_log_dict}")
        return self.flag_check_logcat_output_keywords, self.checked_log_dict

    def common_threadpool(self):
        common_func_list = ["self.checkFrame()",
                            "self.checkHWDecodePlayback()"]
        common_task_pool = threadpool.ThreadPool(6)
        requests = threadpool.makeRequests(self.check_common_status, common_func_list)
        [common_task_pool.putRequest(req) for req in requests]
        common_task_pool.wait()