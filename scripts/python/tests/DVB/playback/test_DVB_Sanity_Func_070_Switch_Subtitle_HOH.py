#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/30
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_Subtitle_H.O.H.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time
import pytest
from lib.common.system.ADB import ADB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.tools.DVB import DVB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.Subtitle import Subtitle
from tests.DVB import *

adb = ADB()
dvb = DVB()
dvb_check = DvbCheck()
dvb_stream = DVBStreamProvider()
subtitle = Subtitle()
# p_config_channel_name = config_yaml.get_note('conf_channel_name')['dvb']
# p_config_channel_dif = config_yaml.get_note('conf_channel_dif_id')['dvb']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('14_TMC')
    adb.clear_logcat()
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
def test_check_switch_subtitle_dvb_text():
    # switch to channel 3
    # adb.keyevent(10)
    # time.sleep(5)
    dvb.switch_subtitle_type(subtitle_type=1)
    subtitle.check_subtitle_thread('HOH', 'LiveTv')
    time.sleep(60)
    dvb_check.check_play_status_main_thread()
