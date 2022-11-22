#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/13
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Video_Decode_H265.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time
import pytest
import random

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.system.ADB import ADB
from lib.common.checkpoint.PlayerCheck import PlayerCheck

dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
player_check = PlayerCheck()
adb = ADB()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('worldcup2014_8bit')
    adb.clear_logcat()
    dvb.start_livetv_apk()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_check_video_decode():
    # dvb.set_channel_mode()
    # dvb.auto_search()
    # assert dvb_check.check_search_ex()
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_id : {channel_id}')
    dvb_check.get_pid_before_switch()
    length = len(channel_id)
    for i in range(length):
        dvb.switch_channel(channel_id[i])
        logging.info(f'switch channel id : {channel_id[i]}')
        assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i]} failed.'
        dvb_check.check_play_status_main_thread(5)
