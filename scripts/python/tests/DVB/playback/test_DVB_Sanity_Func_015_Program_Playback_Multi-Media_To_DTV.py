#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/1
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Program_Playback_Multi-Media_To_DTV.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import time
import pytest

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.system.ADB import ADB
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.playback.MultiMediaPlayer import MultiPlayer
from lib.common.checkpoint.PlayerCheck import PlayerCheck


g_conf_device_id = pytest.config['device_id']

multi = MultiPlayer(g_conf_device_id)
adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
player_check = PlayerCheck()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('gr1')
    multi.multi_setup()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    multi.stop_multiPlayer_apk()


# @pytest.mark.flaky(reruns=3)
def test_check_program_playback():
    adb.clear_logcat()
    dvb.start_livetv_apk()
    dvb_check.check_play_status_sub_thread()
    time.sleep(10)
    start_cmd = multi.start_play_cmd(1, 'http_TS_H264_4K')
    multi.send_cmd(start_cmd)
    assert dvb_check.check_startPlay()
    time.sleep(20)
    dvb.start_livetv_apk()
    time.sleep(10)
