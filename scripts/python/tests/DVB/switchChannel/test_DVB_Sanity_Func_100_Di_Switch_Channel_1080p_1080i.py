#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/13
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Di_Switch_Channel_1080p_1080i.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time

import pytest

from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from . import *

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_switch_count = p_conf_dvb['1080p_1080i_switch_count']

video_name_1080p = 'H264_1080P_50_4Audiotrack'
# video_name_1080i = '20160725_153124'
video_name_1080i = 'MPEG2-1080I'


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_multi_stream_diff_frq('1', 'ts', video_name_1080i, video_name_1080p)
    # adb.clear_logcat()
    # dvb.start_livetv_apk_and_manual_scan(fre_count=2)
    # time.sleep(5)
    dvb.start_livetv_apk_and_manual_scan(fre_count=2)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    dvb_check.clear_multi_frq_program_information()


# @pytest.mark.repeat(p_conf_switch_count)
def test_check_di():
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_id : {channel_id}')
    # length = len(channel_id)
    # for i in range(length-2):
    #     dvb_check.get_pid_before_switch()
    #     dvb.switch_channel(channel_id[-1])
    #     logging.info(f'switch channel id : {channel_id[-1]}')
    #     assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i-1]} failed.'
    #     dvb_check.check_play_status_main_thread(5)
    #     dvb.switch_channel(channel_id[i+1])
    #     logging.info(f'switch channel id : {channel_id[i+1]}')
    #     assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i+1]} failed.'
    #     dvb_check.check_play_status_main_thread(5)
    for i in range(p_conf_switch_count):
        dvb.keyevent(20)
        assert dvb_check.check_switch_channel()
        dvb_check.check_play_status_main_thread(5)
        dvb.keyevent(20)
        assert dvb_check.check_switch_channel()
        dvb_check.check_play_status_main_thread(5)
