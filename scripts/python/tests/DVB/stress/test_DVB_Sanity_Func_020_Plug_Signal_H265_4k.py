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
from lib.common.tools.Subtitle import Subtitle
from . import *

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
subtitle = Subtitle()

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_plug_count = p_conf_dvb['plug_count']

# video_name = 'MPTS1'
video_name = 'TRT_4K'


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    adb.clear_logcat()
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.stress_test
def test_check_plug_signal():
    for i in range(p_conf_plug_count):
        dvb_stream.pause_dvb()
        dvb_stream.resume_dvbc_stream(video_name)
        # time.sleep(5)
        # # subtitle check
        # dvb.switch_subtitle_type(subtitle_type=0)
        # subtitle.start_subtitle_datathread('Dvb', 'LiveTV')
        # assert subtitle.subtitleThread.is_alive()
        # time.sleep(60)
        # logging.debug(
        #     f'subtitle.got_spu : {subtitle.got_spu}; subtitle.show_spu : {subtitle.show_spu} ; subtitle.subtitle_window: {subtitle.subtitle_window}')
        # assert (subtitle.got_spu != '') & (subtitle.show_spu != '') & (
        #         subtitle.subtitle_window != ''), \
        #     'There are some problems with the subtitle shows'
        dvb_check.check_play_status_main_thread(10)
