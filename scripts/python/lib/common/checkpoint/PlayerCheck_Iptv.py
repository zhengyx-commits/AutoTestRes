#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/1/28 下午4:17
# @Author  : yongbo.shao
# @File    : PlayerCheck_Iptv.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm

import logging
import os
import re
import threading
import time
import pytest
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from lib import get_read_buffer


class PlayerCheck_Iptv(PlayerCheck_Base):
    '''
    player checkpoint, support OTT hybrid S IPTV
    '''
    def __init__(self, playerNum=1):
        super().__init__(playerNum=playerNum)

    def start_check_keywords(self, keywords, log, timeout, name, getDuration=False):
        checked_log_dict = {}
        checked_log_list = []
        counter = 0
        start_time = time.time()
        while time.time() - start_time < timeout:
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
                        if (getDuration is True) or (name == "check_startPlay"):
                            player_num = \
                            re.findall(r".*AmlTsPlayer_(.*) \[evt\] AM_TSPLAYER_EVENT_TYPE_FIRST_FRAME.*", outputValue)[0]
                            self.checked_log_dict[
                                player_num] = outputValue
                        else:
                            checked_log_dict[keyword] = outputValue
                            self.checked_log_dict = checked_log_dict
                        logging.info(f"outputValue: {outputValue}")
                        logging.info(f"keyword: {keyword}")
                        counter += 1
                        # break
                if name == "check_startPlay" and counter != len(keywords):
                    self.flag_check_logcat_output_keywords = True
                else:
                    if counter == len(keywords):
                        flag_check_logcat_output_keywords = True
                        self.flag_check_logcat_output_keywords = flag_check_logcat_output_keywords
                        break

        # check KPI
        # if flag_check_logcat_output_keywords:
        #     self.checked_log_dict = checked_log_dict
        #     # logging.info("check kpi true")
        #     flag_kpi = self.check_kpi(keywords, start_time)
        #     if not flag_kpi:
        #         # flag_check_logcat_output_keywords = False
        #         return flag_check_logcat_output_keywords
        logging.info(f"{name} keywords found:{self.flag_check_logcat_output_keywords}")
        logging.info(f"checked_log_dict: {self.checked_log_dict}")
        return self.flag_check_logcat_output_keywords, self.checked_log_dict

