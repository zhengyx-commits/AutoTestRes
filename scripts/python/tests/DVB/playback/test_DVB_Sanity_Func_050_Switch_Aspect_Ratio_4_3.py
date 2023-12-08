#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/18
# @Author  : jianhua.huang
# @File    : test_DVB_Sanity_Func_Switch_Aspect_Ratio_4:3.py
# @Email   : jianhua.huang@amlogic.com
# @Ide: PyCharm
import logging
import time

import pytest

from lib.common.system.ADB import ADB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.tools.DVB import DVB
from tools.DVBStreamProvider import DVBStreamProvider

adb = ADB()
dvb = DVB(set_channel_mode="cable")
dvb_check = DvbCheck()
dvb_stream = DVBStreamProvider()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('gr1')
    adb.clear_logcat()
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
# @pytest.mark.flaky(reruns=3)
def test_check_switch_channel():
    dvb.switch_aspect_ratio(display_mode=1)
    assert dvb_check.check_aspect_ratio(dispaly_mode=1)
    dvb_check.check_play_status_main_thread()
