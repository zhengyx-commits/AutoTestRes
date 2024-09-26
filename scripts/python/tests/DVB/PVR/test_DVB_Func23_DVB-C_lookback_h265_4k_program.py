#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/12 16:21
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func23_DVB-C_lookback_h265_4k_program.py
# @Software: PyCharm

import time
import logging

from ..PVR import pytest, dvb_stream, dvb, dvb_check
from lib.common.checkpoint.HdmiCheck import HdmiCheck

video_name = 'worldcup2014_8bit'


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
def test_lookback_h265_4k_program():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    time.sleep(30)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    time.sleep(2)
    # resolution = dvb_check.get_current_playback_resolution()
    # logging.info(f'resolution {resolution}')
    # assert int(resolution[0]) >= 3840 and int(resolution[1]) >= 2160, "Resolution not 4K"
    dvb_check.check_play_status_main_thread(timeout=20)
    # dvb.pvr_stop()
    # assert dvb_check.check_pvr_stop()
