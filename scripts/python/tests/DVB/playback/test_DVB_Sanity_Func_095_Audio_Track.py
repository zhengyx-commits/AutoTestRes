#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/25
# @Author  : jianhua.huang
# @File    : test_DVB_Sanity_Func_95_Audio_Track.py
# @Email   : jianhua.huang@amlogic.com
# @Ide: PyCharm
import logging
import time

import pytest

from lib.common.system.ADB import ADB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.tools.DVB import DVB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.checkpoint.PlayerCheck import PlayerCheck

adb = ADB()
dvb = DVB()
dvb_check = DvbCheck()
dvb_stream = DVBStreamProvider()
player_check = PlayerCheck()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('4_audio')
    adb.clear_logcat()
    dvb.start_livetv_apk()
    time.sleep(2)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
# @pytest.mark.flaky(reruns=3)
def test_check_switch_audio_track():
    dvb_check.check_play_status_main_thread()
    audio_track_number = dvb.get_number_of_audio_track()
    if audio_track_number == 0 or audio_track_number == 1:
        logging.info('No extra tracks to switch')
        assert False
    else:
        logging.info('Start switching tracks ...')
        for i in range(audio_track_number - 1):
            dvb.switch_audio_track(audio_track_number=i+1)
            dvb_check.check_audio_track_switch()
            dvb_check.check_play_status_main_thread(5)
        dvb.switch_audio_track(audio_track_number=0)
        dvb_check.check_audio_track_switch()
        dvb_check.check_play_status_main_thread(5)
