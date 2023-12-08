#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/11 20:18
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func16_DVB-C_recording_switch_channel.py
# @Software: PyCharm
import logging
import time
from lib.common.tools.Subtitle import Subtitle
from ..PVR import pytest, dvb_stream, dvb, dvb_check

subtitle = Subtitle()
video_name = 'BBC_MUX_UH'


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(2)
    # dvb.auto_search()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_recording_switch_channel():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.start_pvr_recording()
    # subtitle.check_subtitle_thread('Dvb', 'LiveTv')
    for i in range(5):
        time.sleep(10)
        dvb.keyevent(19)
    time.sleep(10)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(10)
    dvb.pvr_stop()
    assert dvb_check.check_pvr_stop()
