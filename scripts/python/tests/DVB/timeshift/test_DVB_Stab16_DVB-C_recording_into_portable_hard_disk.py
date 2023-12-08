#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/7/13 14:46
# @Author  : chao.li
# @Site    :
# @File    : test_DVB_Stab16_DVB-C_recording_into_portable_hard_disk.py
# @Software: PyCharm

import time
import logging

from tests.DVB.PVR import pytest, dvb_stream, dvb, dvb_check

video_name = 'gr1'


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk_and_manual_scan()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.stress_test
# @pytest.mark.flaky(reruns=3)
def test_recording_into_hard_disk():
    if dvb.getUUIDAvailSize() > 500:
        logging.info('Pls plug in hard disk.')
    elif dvb.getUUIDAvailSize() < 10:
        assert False, 'The disk is full.'
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    logging.info(f'hard disk avail size {dvb.getUUIDAvailSize()}M.')
    while dvb.getUUIDAvailSize() >= 1:
        time.sleep(60)
    # dvb.stop_pvr_recording()
    # assert dvb_check.check_stop_pvr_recording()
    assert dvb_check.check_pvr_auto_stop_recording()
