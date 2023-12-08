#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/18
# @Author  : jianhua.huang
# @File    : test_DVB_Sanity_Func_Switch_Teletext_Switch_Page.py
# @Email   : jianhua.huang@amlogic.com
# @Ide: PyCharm
import logging
import threading
import time

import pytest

from lib.common.system.ADB import ADB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.tools.DVB import DVB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.Subtitle import Subtitle

adb = ADB()
dvb = DVB()
dvb_check = DvbCheck()
dvb_stream = DVBStreamProvider()
subtitle = Subtitle()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream(video_name='14_TMC')
    adb.clear_logcat()
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
# @pytest.mark.flaky(reruns=3)
def test_check_switch_teletext():
    dvb.switch_teletext()
    # subtitle.check_subtitle_thread('Teletext', 'LiveTv')
    time.sleep(30)
    dvb_check.check_play_status_main_thread()
    dvb.clear_logcat()
    subtitle.__init__()
    dvb.text(300)
    logging.info('switch page 300')
    time.sleep(5)
    # subtitle.check_subtitle_thread('Teletext', 'LiveTv')
    time.sleep(30)
    dvb_check.check_play_status_main_thread()
    dvb.clear_logcat()
    subtitle.__init__()
    dvb.text(899)
    logging.info('switch page 899')
    time.sleep(5)
    # subtitle.check_subtitle_thread('Teletext', 'LiveTv')
    time.sleep(30)
    dvb_check.check_play_status_main_thread()
