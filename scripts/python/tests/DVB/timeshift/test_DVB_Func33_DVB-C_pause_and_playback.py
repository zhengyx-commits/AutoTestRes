#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/13 10:52
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func33_DVB-C_pause_and_playback.py
# @Software: PyCharm


import time
import logging
from tests.DVB.PVR import *

from tests.DVB.PVR import pytest, dvb_stream, dvb, dvb_check, playerCheck

video_name = 'gr1'

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_pause_count = p_conf_dvb['timeshift_pause_resume_count']


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
    dvb.start_livetv_apk()
    time.sleep(1)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_pause_and_playback():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.timeshift_start()
    time.sleep(10)
    logging.info('start play')
    dvb.keyevent(23)
    time.sleep(3)
    assert dvb_check.check_timeshift_start()
    logging.info('finish check start')
    for i in range(p_conf_pause_count):
        logging.info(f'------The {i + 1} times------')
        time.sleep(5)
        logging.info('timeshift pause')
        dvb.timeshift_pause()
        assert dvb_check.check_timeshift_pause()
        time.sleep(5)
        logging.info('timeshift resume')
        dvb.timeshift_resume()
    dvb_check.check_play_status_main_thread(timeout=15)
    dvb.timeshift_stop()
    assert dvb_check.check_timeshift_stop()
