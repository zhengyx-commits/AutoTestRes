#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/26
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVB-S_22KHZ_Search.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import pytest

from lib.common.system.ADB import ADB
# from tools.DVBStreamProvider import DVBStreamProvider
from tools.DVBStreamProvider_Linux import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

video_name = 'gr1'


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbs_stream(video_name=video_name, freq=9750)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_dvb_scan():
    dvb.start_livetv_apk()
    dvb.set_up_dvbs_parameter()
    dvb.set_test_satellite(2)
    assert dvb_check.check_set_test_satellite()
    dvb.set_lnb_type('2')
    assert dvb_check.check_set_lnb_type('2')
    dvb.set_test_transponder(21)
    assert dvb_check.check_set_test_transponder()
    dvb.dvbs_scan()
    assert dvb_check.check_dvbs_scan()
    dvb_check.check_play_status_main_thread()
    dvb_stream.stop_dvb()
    dvb_stream.start_dvbs_stream(video_name=video_name, freq=10600)
    dvb.set_up_dvbs_parameter()
    dvb.set_test_satellite(2)
    assert dvb_check.check_set_test_satellite()
    dvb.set_lnb_type('2')
    assert dvb_check.check_set_lnb_type('2')
    dvb.set_test_transponder(31)
    assert dvb_check.check_set_test_transponder()
    dvb.dvbs_scan()
    assert dvb_check.check_dvbs_scan()
    dvb_check.check_play_status_main_thread()
