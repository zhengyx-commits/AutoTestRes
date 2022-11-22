#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/8
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Video_Decode_AD.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import time
import pytest

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
    dvb_stream.start_dvbc_stream('Dual_4PID_Multi-Lang_HEAAC_AC4', 'trp')
    adb.clear_logcat()
    dvb.start_livetv_apk()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_check_video_decode():
    dvb_check.check_play_status_main_thread(10)
