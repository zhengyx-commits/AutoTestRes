#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/18 下午5:01
# @Author  : yongbo.shao
# @File    : test_DVB_Sanity_Func_159_Stress_Playback.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm

import logging
import time

import pytest

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from .. import config_yaml

dvb_stream = DVBStreamProvider()
dvb = DVB()
dvb_check = DvbCheck()
player_check = PlayerCheck()
p_conf_stress = config_yaml.get_note("conf_stress")
p_conf_stress_time = p_conf_stress.get("stress_time")

video_name = "gr1"


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.skip
@pytest.mark.stress_test
def test_4k_stress_playback():
    # test playback 4K channel
    dvb_check.check_play_status_main_thread(timeout=p_conf_stress_time)
    # get all channel id
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_ids : {channel_id}')
    length = len(channel_id)
    for i in range(length):
        dvb.switch_channel(channel_id[i])
        logging.info(f'switch channel id : {channel_id[i]}')
        assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i]} failed.'
        dvb_check.check_play_status_main_thread()
