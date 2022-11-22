#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/13
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Di_Switch_Channel_1080p_1080i.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time

import pytest

from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from . import *

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
player_check = PlayerCheck()

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_switch_count = p_conf_dvb['switch_count']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_multi_stream_diff_frq('ts', 'PhilipsColorsofMiami', 'gr1')
    adb.clear_logcat()
    dvb.start_livetv_apk(fre_count=2)
    time.sleep(5)
    # dvb.set_channel_mode()
    # dvb.auto_search()
    # assert dvb_check.check_search_ex()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    dvb_check.clear_multi_frq_program_information()


# @pytest.mark.repeat(p_conf_switch_count)
def test_check_di():
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_id : {channel_id}')
    dvb_check.get_pid_before_switch()
    length = len(channel_id)
    for i in range(length):
        dvb.switch_channel(channel_id[i])
        logging.info(f'switch channel id : {channel_id[i]}')
        assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i]} failed.'
        dvb_check.check_play_status_main_thread(5)
