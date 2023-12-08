#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/18
# @Author  : jianhua.huang
# @File    : test_DVB_Sanity_Func_Switch_Subtitle_DVB_TEXT.py
# @Email   : jianhua.huang@amlogic.com
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
p_config_channel_name = config_yaml.get_note('conf_channel_name')['dvb']
p_config_channel_dif = config_yaml.get_note('conf_channel_dif_id')['dvb']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('BBC_MUX_UH')
    # p_subtitle_mode = dvb_check.get_subtitle_mode('dvb.ts')
    # assert p_subtitle_mode == 'Dvb'
    adb.clear_logcat()
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
# @pytest.mark.flaky(reruns=3)
def test_check_switch_subtitle_dvb_text():
    dvb.switch_subtitle_type(subtitle_type=0)
    # subtitle.check_subtitle_thread('Dvb', 'LiveTv')
    time.sleep(60)
    dvb_check.check_play_status_main_thread()
