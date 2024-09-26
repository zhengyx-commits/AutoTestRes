#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/12 13:38
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func18_DVB-C_play_multi_language_program.py.py
# @Software: PyCharm


import time
import logging

from ..PVR import pytest, dvb_stream, dvb, dvb_check

# Todo @chao.li english audio
# video_name = 'BBC_MUX_UH'
video_name = '14_TMC_France'


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(1)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_play_multi_language_program():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.get_number_of_audio_track()
    dvb.switch_audio_track(audio_track_number=1)
    assert dvb_check.check_audio_track_switch()
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    time.sleep(60)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(60)
    # dvb.pvr_stop()
    # assert dvb_check.check_pvr_stop()
