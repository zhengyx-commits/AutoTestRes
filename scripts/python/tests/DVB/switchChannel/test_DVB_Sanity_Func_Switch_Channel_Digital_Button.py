#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/8
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_Channel_Digital_Button.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import pytest

from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('gr1')
    dvb.start_livetv_apk()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_check_switch_channel():
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_id : {channel_id}')
    dvb_check.get_pid_before_switch()
    length = len(channel_id)
    for i in range(length):
        adb.keyevent(i+8)
        assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i]} failed.'
        dvb_check.check_play_status_main_thread(5)
