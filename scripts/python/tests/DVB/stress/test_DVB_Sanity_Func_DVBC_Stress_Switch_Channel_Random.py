#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: test_DVB_Sanity_Func_DVBC_Stress_Switch_Channel_Random.py
# Author: KeJun.Chen
# Create Date: 2023/11/30
import logging
import pytest
import random

from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from . import *

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_channel_switch_count = p_conf_dvb['dvbc_stress_channel_switch_count']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('gr1')
    dvb.start_livetv_apk_and_manual_scan()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_check_switch_channel():
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_id : {channel_id}')
    dvb_check.get_pid_before_switch()
    get_random_value_generator = dvb_check.get_random_value(channel_id)
    for i in range(p_conf_channel_switch_count):
        logging.info(f'start the {i + 1} times test.')
        switch_channel = next(get_random_value_generator)
        dvb.switch_channel(switch_channel)
        logging.info(f'switch channel id : {switch_channel}')
        assert dvb_check.check_switch_channel(), f'switch channel failed.'
        dvb_check.check_play_status_main_thread()
