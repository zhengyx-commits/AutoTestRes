#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/8/5 10:57
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func27_DVB-C_display_the_default_subtitle_during_playback.py
# @Software: PyCharm


import time
import logging

from ..PVR import pytest, dvb_stream, dvb, dvb_check
from lib.common.tools.Subtitle import Subtitle

video_name = 'MBT_muxA'
subtitle = Subtitle()


# @pytest.mark.skip
@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name, 'trp')
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(3)
    for i in range(20):
        number = dvb.get_subtitle_list()
        logging.info(f'number {number}')
        if number != 0:
            break
        dvb.keyevent(19)
        time.sleep(3)
    else:
        raise EnvironmentError('Not subtitle found!')
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
# @pytest.mark.flaky(reruns=3)
def test_play_multi_language_program():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    # subtitle_type = dvb_check.get_subtitle_mode('ts')
    dvb.switch_subtitle_type(subtitle_type=1)
    assert dvb_check.check_subtitle_current_language(switch_type=1)
    # subtitle.check_subtitle_thread('Teletext', 'LiveTV')
    time.sleep(15)
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    time.sleep(60)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    assert dvb_check.check_pvr_start_play()
    time.sleep(10)
    dvb.switch_subtitle_during_pvr(track=1)
    dvb_check.check_play_status_main_thread(timeout=50)
    # dvb.pvr_stop()
    # assert dvb_check.check_pvr_stop()
