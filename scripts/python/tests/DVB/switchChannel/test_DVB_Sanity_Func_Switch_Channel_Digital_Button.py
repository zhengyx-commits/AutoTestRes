#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/8
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_Channel_Digital_Button.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import pytest
import random

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
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    dvb_check.clear_multi_frq_program_information()


def test_check_switch_channel():
    dvb.start_livetv_apk_and_auto_scan()
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_id : {channel_id}')
    dvb_check.get_pid_before_switch()
    length = len(channel_id)
    digital_button_list = []
    for i in range(length):
        digital_button_list.append(i+8)
    logging.info(f'digital button list: {digital_button_list}')
    for i in range(length):
        switch_digital = random.choice(digital_button_list)
        adb.keyevent(switch_digital)
        assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i]} failed.'
        dvb_check.check_play_status_main_thread(5)
