#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/1
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Program_Playback_Netflix_To_DTV.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time
import pytest

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.playback.Netflix import Netflix
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from lib.common.system.ADB import ADB

dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
netflix = Netflix()
player_check = PlayerCheck()
adb = ADB()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('gr1')
    netflix.netflix_setup()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    netflix.stop_netflix()


# @pytest.mark.flaky(reruns=3)
def test_check_program_playback():
    adb.clear_logcat()
    dvb.start_livetv_apk()
    dvb_check.check_play_status_main_thread(10)
    netflix.start_play()
    time.sleep(20)
    dvb.start_livetv_apk()
    dvb_check.check_play_status_main_thread(10)
