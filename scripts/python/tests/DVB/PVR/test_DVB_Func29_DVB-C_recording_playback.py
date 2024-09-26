#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/13 10:17
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func29_DVB-C_recording_playback.py
# @Software: PyCharm


import time
import logging
from . import *

from ..PVR import pytest, dvb_stream, dvb, dvb_check

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_repeat_count = p_conf_dvb['pvr_use_three_hours_recording_goto_count']


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream('gr1')
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(3)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.skip
@pytest.mark.repeat(p_conf_repeat_count)
def test_recording_playback():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.pvr_select_play(record_duration=10800)
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(timeout=30)
    dvb.pvr_seek(seek_time=10740)
    assert dvb_check.check_pvr_seek(pos=10740)
    time.sleep(30)
    dvb.pvr_seek(seek_time=0)
    assert dvb_check.check_pvr_seek(pos=0)
    time.sleep(30)
    dvb.pvr_stop()
    assert dvb_check.check_pvr_stop()
