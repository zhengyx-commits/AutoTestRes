#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/3/10 下午14:00
# @Author  : jun.yang
# @File    : PlayerCheck_Youtube.py
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


class PlayerCheck_Youtube(PlayerCheck_Base):
    '''
    player checkpoint, support OTT hybrid S IPTV
    '''
    def __init__(self, playerNum=1):
        super().__init__(playerNum=playerNum)
        self.home_play_able = False

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
            while time.time() - start_time < timeout:
                if self.get_abnormal_observer():
                    # logging.info("get abnormal observer")
                    flag_common_threadpool = False
                    self.home_play_able = False
                    self.reset()
                    return flag_common_threadpool, self.checked_log_dict
        self.home_play_able = False
        self.reset()
        return self.flag_check_logcat_output_keywords, self.checked_log_dict

    def check_seek(self, keywords="", logFilter=""):
        """
        check seek: include PIP way
        params are the same as check_stopPlay
        """
        self.randomSeekEnable = True
        if not keywords:
            keywords = self.youtubecheck_keywords.SEEK_KEYWORDS
        if not logFilter:
            logFilter = self.youtubecheck_keywords.SEEK_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_seek.__name__)

    def check_home_play(self, keywords="", logFilter=""):
        """
        check seek: include PIP way
        params are the same as check_stopPlay
        """
        self.home_play_able = True
        if not keywords:
            keywords = self.youtubecheck_keywords.HOME_PLAY_KEYWORDS
        if not logFilter:
            logFilter = self.youtubecheck_keywords.HOME_PLAY_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_home_play.__name__)

    def start_check_keywords(self, keywords, log, timeout, name, getDuration=False):
        count = 0
        start_time = time.time()
        pause_value = None
        playing_value = None
        seek_count = 0
        while time.time() - start_time < 50:
            if len(self.abnormal_observer_list) != 0:
                print("if check abnormal in thread, should exit")
                self.flag_check_logcat_output_keywords = False
                return self.flag_check_logcat_output_keywords, self.checked_log_dict
            outputValue = pytest.device._adblogcat_reader._read_buffer.get()
            tmp = ""
            for keyword in keywords:
                if keyword in outputValue and (tmp != outputValue):
                    tmp = outputValue
                    if name == "check_seek":
                        if keyword == "MediaSession setPlaybackState: PAUSED, position:" and seek_count == 0:
                            pause_value = re.findall(r".*MediaSession setPlaybackState: PAUSED, position: (.*) ms, speed: 0.*", outputValue)[0]
                            pause_value = int(pause_value)
                            self.checked_log_dict[pause_value] = outputValue
                            seek_count = seek_count + 1
                            logging.info(f"outputValue: {outputValue}")
                            logging.info(f"keyword: {keyword}")
                        elif keyword == "MediaSession setPlaybackState: PLAYING, position:" and seek_count == 1:
                            playing_value = re.findall(r".*MediaSession setPlaybackState: PLAYING, position: (.*) ms, speed: 1.*", outputValue)[0]
                            playing_value = int(playing_value)
                            self.checked_log_dict[playing_value] = outputValue
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

            if name == "check_seek" and seek_count == 2 and playing_value > pause_value:
                self.flag_check_logcat_output_keywords = True
                break
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