#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/4
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_To_Player_Black_Screen_Mode.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import pytest
import random

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.playback.Youtube import YoutubeFunc
from lib.common.playback.Netflix import Netflix
from lib.common.checkpoint.PlayerCheck import PlayerCheck

dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
youtube = YoutubeFunc()
netflix = Netflix()
player_check = PlayerCheck()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('gr1')
    dvb.change_switch_mode('0')
    netflix.netflix_setup()
    dvb.start_livetv_apk()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    youtube.stop_youtube()
    netflix.stop_netflix()


@pytest.mark.skip
def test_check_program_playback():
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_id : {channel_id}')
    dvb_check.get_pid_before_switch()
    switch_channel_id = random.choice(channel_id)
    dvb.switch_channel(switch_channel_id)
    logging.info(f'switch channel id : {switch_channel_id}')
    assert dvb_check.check_switch_channel(), f'switch failed.'
    youtube.start_youtube()
    dvb_check.check_play_status_main_thread()
    dvb.start_livetv_apk()
    dvb.switch_channel(switch_channel_id)
    assert dvb_check.check_switch_channel(), f'switch failed.'
    netflix.start_play()
    dvb_check.check_play_status_main_thread()
