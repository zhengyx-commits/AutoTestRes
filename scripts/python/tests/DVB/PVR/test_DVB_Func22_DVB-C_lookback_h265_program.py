#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/12 15:38
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func22_DVB-C_lookback_h265_program.py
# @Software: PyCharm

import time
import logging

from ..PVR import pytest, dvb_stream, dvb, dvb_check

video_name = 'TEN_BA2'


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    # dvb.start_livetv_apk()
    # time.sleep(1)
    # dvb.set_channel_mode()
    # time.sleep(1)
    # dvb.auto_search()
    # dvb_check.check_search_ex(video_name)
    # dvb.home()
    # time.sleep(3)
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(1)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_lookback_h265_program():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    time.sleep(30)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(timeout=30)
    # dvb.pvr_stop()
    # assert dvb_check.check_pvr_stop()
