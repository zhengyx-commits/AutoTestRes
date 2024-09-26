#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/13 14:32
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func36_DVB-C_timeshift_playback.py
# @Software: PyCharm

import time
import logging
from tests.DVB.PVR import *

from tests.DVB.PVR import pytest, dvb_stream, dvb, dvb_check

video_name = 'gr1'

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_playback_count = p_conf_dvb['timeshift_playback_count']


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(1)
    # dvb.auto_search()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.skip
def test_timeshift_playback():
    for i in range(p_conf_playback_count):
        logging.info(f'------The {i + 1} times------')
        dvb.timeshift_start()
        time.sleep(10)
        logging.info('start play')
        dvb.keyevent(23)
        time.sleep(3)
        assert dvb_check.check_timeshift_start()
        dvb_check.check_play_status_main_thread(15)
        dvb.timeshift_pause()
        assert dvb_check.check_timeshift_pause()
        time.sleep(3)
        dvb.timeshift_resume()
        time.sleep(3)
        dvb.timeshift_seek()
        assert dvb_check.check_timeshift_seek()
        dvb.timeshift_stop()
        assert dvb_check.check_timeshift_stop()
        time.sleep(10)
