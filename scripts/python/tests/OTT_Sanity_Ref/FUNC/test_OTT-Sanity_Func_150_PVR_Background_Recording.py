#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/3/14
# @Author  : kejun.chen
# @File    : test_OTT-Sanity_Func_150_PVR_Background_Recording.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import os
import time
import pytest
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from tools.DVBStreamProvider import DVBStreamProvider
from tools.yamlTool import yamlTool
from lib.common.playback.Youtube import YoutubeFunc
from lib.common.playback.Netflix import Netflix


dvb_stream = DVBStreamProvider()
dvb = DVB()
dvb_check = DvbCheck()
youtube = YoutubeFunc()
netflix = Netflix()

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_repeat_count = p_conf_dvb['30_pvr_basic_function_count']

video_name = 'BBC_MUX_UH'


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    netflix.netflix_setup()
    dvb.start_livetv_apk_and_manual_scan()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    youtube.stop_youtube()
    netflix.stop_netflix()


@pytest.mark.skip
def test_program_recording():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.start_pvr_recording()
    assert dvb_check.check_start_pvr_recording()
    youtube.start_youtube()
    dvb_check.check_play_status_main_thread(timeout=20)
    netflix.start_play()
    dvb_check.check_play_status_main_thread(timeout=20)
    # netflix.stop_netflix()
    dvb.start_livetv_apk()
    dvb_check.check_play_status_main_thread(timeout=10)
    dvb.stop_pvr_recording()
    assert dvb_check.check_stop_pvr_recording()
    dvb.pvr_start_play()
    logging.info('Pvr start')
    assert dvb_check.check_pvr_start_play()
    dvb_check.check_play_status_main_thread(timeout=20)
    dvb.pvr_stop()
    assert dvb_check.check_pvr_stop()

