#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/13
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Plug_Signal_H265_4k.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time
import pytest

from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from . import *

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
player_check = PlayerCheck()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('subt_doctor')
    adb.clear_logcat()
    dvb.start_livetv_apk()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.skip
def test_check_test():
    # dvb.set_channel_mode()
    # dvb.auto_search()
    # dvb.auto_search()  # 当前apk存在第一次搜索不生效的情况
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
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    time.sleep(10)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    time.sleep(10)
    dvb.pvr_stop()
    assert dvb_check.check_pvr_stop()
