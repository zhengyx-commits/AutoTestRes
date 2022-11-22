#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/13 11:17
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Func35_DVB-C_playback_and_seek.py
# @Software: PyCharm

import time
import logging
import random
from tests.DVB.PVR import *

from tests.DVB.PVR import pytest, dvb_stream, dvb, dvb_check, playerCheck

video_name = 'gr1'

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_seek_count = p_conf_dvb['timeshift_seek_count']


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
def test_playback_and_seek():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.timeshift_start()
    time.sleep(10)
    logging.info('start play')
    dvb.keyevent(23)
    time.sleep(3)
    assert dvb_check.check_timeshift_start()
    logging.info('finish check start')
    # dvb.timeshift_ff()
    # assert dvb_check.check_timeshift_ff()
    for i in range(p_conf_seek_count):
        logging.info(f'------The {i + 1} times------')
        seek_time = random.choice(range(10))
        dvb.timeshift_seek(seek_time=seek_time*1000)
        assert dvb_check.check_timeshift_seek()
        dvb_check.check_play_status_main_thread(timeout=10)
    dvb.timeshift_stop()
    assert dvb_check.check_timeshift_stop()
