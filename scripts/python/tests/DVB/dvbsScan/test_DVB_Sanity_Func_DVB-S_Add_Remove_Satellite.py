#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/27
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVB-S_Add_Remove_Satellite.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time

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
    dvb.remove_dvbs_TP(sate_name='Thor 5/6', tp_name='4000H27488')
    dvb.reset_dvbs_param('all')


def test_dvb_scan():
    dvb.start_livetv_apk()
    dvb.set_channel_mode_dvbs()
    dvb.set_up_dvbs_parameter()
    dvb.set_lnb_type(lnb_type='0')
    logging.info('add test satellite')
    dvb.add_satellite(name='test', direction=True, longitude=88)
    assert dvb_check.check_add_satellite()
    dvb.select_satellite('0')
    assert dvb_check.check_select_satellite()
    dvb.set_test_satellite(0)
    assert dvb_check.check_set_test_satellite()
    dvb.add_transponder(sate_name='Thor 5/6', freq=4000, polarity='H', symbol=27488, is_dvbs2=False,
                        modulation='auto', fec='auto')
    assert dvb_check.check_add_transponder()
    dvb.set_test_transponder(67)
    dvb.dvbs_scan()
    assert dvb_check.check_dvbs_scan()
    dvb_check.check_play_status_main_thread()
    logging.info('remove test satellite')
    dvb.set_channel_mode_dvbs()
    dvb.set_up_dvbs_parameter()
    dvb.remove_satellite('test')
    assert dvb_check.check_remove_satellite()
    time.sleep(3)
    adb.keyevent(4)
    time.sleep(1)
    adb.keyevent(4)
    time.sleep(1)
