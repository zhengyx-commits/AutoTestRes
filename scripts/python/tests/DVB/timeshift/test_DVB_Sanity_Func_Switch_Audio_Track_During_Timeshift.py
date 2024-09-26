#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/8
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_Audio_Track_During_Timeshift.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import time
from tests.DVB.PVR import pytest, dvb_stream, dvb, dvb_check

video_name = 'Multiple_Languages'


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name, 'trp')
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(1)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_switch_audio_track_during_timeshift():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.timeshift_start()
    assert dvb_check.check_timeshift_start()
    time.sleep(5)
    dvb.keyevent(23)
    dvb_check.check_play_status_main_thread(10)
    for i in range(5):
        dvb.switch_audio_track(audio_track_number=(i+1))
        assert dvb_check.check_audio_track_switch()
        dvb_check.check_play_status_main_thread(10)
    dvb.timeshift_stop()
    assert dvb_check.check_timeshift_stop()
