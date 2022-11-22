#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/28
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_Channel_Avsync.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import pytest
import random

from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.checkpoint.PlayerCheck import PlayerCheck

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
player_check = PlayerCheck()


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
    switch_channel = random.choice(channel_id)
    dvb.switch_channel(switch_channel)
    logging.info(f'switch channel id : {switch_channel}')
    assert dvb_check.check_switch_channel(), f'switch channel failed.'
    dvb_check.check_play_status_main_thread()
