#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/13 15:03
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Stab17_DVB-C_recording_and_playback.py
# @Software: PyCharm


import time
import logging
from . import *

from ..PVR import pytest, dvb_stream, dvb, dvb_check, playerCheck

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_repeat_count = p_conf_dvb['pvr_playback_every_two_hours_count']


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb.start_livetv_apk()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.stress_test
@pytest.mark.repeat(p_conf_repeat_count)
# @pytest.mark.flaky(reruns=3)
def test_recording_and_playback():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.pvr_select_play(record_duration=28800)
    time.sleep(3)
    assert dvb_check.check_pvr_start_play()
    for i in range(4):
        time.sleep(2 * 3500)
        dvb.pvr_ff()
        assert dvb_check.check_pvr_ff()
        time.sleep(5)
        dvb.pvr_fb()
        assert dvb_check.check_pvr_fb()
        dvb.pvr_pause()
        assert dvb_check.check_pvr_pause()
        time.sleep(3)
        dvb.pvr_resume()
        assert dvb_check.check_pvr_resume()
        time.sleep(3)
        dvb.pvr_current_seek(seek_time=5)
        assert dvb_check.check_pvr_current_seek(5)
        dvb.pvr_current_seek(seek_time=-5)
        assert dvb_check.check_pvr_current_seek(-5)
        dvb_check.check_play_status_main_thread(timeout=30)
    dvb.pvr_stop()
    assert dvb_check.check_pvr_stop()
