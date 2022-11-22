#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/13 10:06
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func26_DVB-C_display_the_default_audio_track_during_playback.py
# @Software: PyCharm
import threading
import time
import logging

from ..PVR import pytest, dvb_stream, dvb, dvb_check, playerCheck

# video_name = 'BBC_MUX_UH'
video_name = '14_TMC_France'


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk()
    time.sleep(1)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_display_default_audio_track_during_playback():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.switch_audio_track(audio_track_number=1)
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    time.sleep(60)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(10)
    dvb.pvr_stop()
    assert dvb_check.check_pvr_stop()
