#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/11 14:26
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func15_DVB-C_program_recording.py
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
    time.sleep(1)
    # dvb.auto_search()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_program_recording():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.add_timer_recording(start_time=65, end_time=125)
    assert dvb_check.check_start_pvr_recording(65), "Pvr start recording time is not 65 seconds"
    # subtitle.check_subtitle_thread('Dvb', 'LiveTv')
    time.sleep(65)
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(timeout=10)
    # dvb.pvr_stop()
    # assert dvb_check.check_pvr_stop()
