#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/12 16:31
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func24_DVB-C_switch_channel.py
# @Software: PyCharm

import time
import logging

from ..PVR import pytest, dvb_stream, dvb, dvb_check, playerCheck

video_name = 'gr1'


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk()
    time.sleep(2)
    # dvb.auto_search()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_switch_channel():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    time.sleep(30)
    dvb.keyevent(19)
    time.sleep(30)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(timeout=30)
    dvb.pvr_stop()
    assert dvb_check.check_pvr_stop()
