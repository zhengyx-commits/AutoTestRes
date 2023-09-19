#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/26
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVB-S_22KHz_ON_OFF_Search.py
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
    dvb_stream.start_dvbs_stream(video_name=video_name)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_dvb_scan():
    dvb.start_livetv_apk()
    dvb.set_up_dvbs_parameter()
    dvb.set_test_satellite(2)
    assert dvb_check.check_set_test_satellite()
    dvb.set_lnb_type('0')
    assert dvb_check.check_set_lnb_type('0')
    dvb.set_22khz()
    assert dvb_check.check_set_22khz()
    dvb.dvbs_scan()
    assert dvb_check.check_dvbs_scan()
    dvb_check.check_play_status_main_thread()
    dvb.set_up_dvbs_parameter()
    dvb.set_test_satellite(2)
    assert dvb_check.check_set_test_satellite()
    dvb.set_lnb_type('0')
    assert dvb_check.check_set_lnb_type('0')
    dvb.set_22khz(0)
    assert dvb_check.check_set_22khz(0)
    dvb.dvbs_scan()
    assert not dvb_check.check_dvbs_scan()
    dvb_check.check_play_status_main_thread()