#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/28
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_Channel_Free_To_Encryption.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import pytest
import time

from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from . import *

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_multi_stream_diff_frq(0, 'ts', 'iptv_test', 'gr1')
    dvb.start_livetv_apk_and_manual_scan(fre_count=2)
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_check_switch_channel():
    # dvb.set_channel_mode()
    # dvb.auto_search()
    # assert dvb_check.check_search_ex()
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_id : {channel_id}')
    dvb_check.get_pid_before_switch()
    length = len(channel_id)
    for i in range(length):
        dvb.switch_channel(channel_id[i])
        logging.info(f'switch channel id : {channel_id[i]}')
        assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i]} failed.'
