#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/1
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Program_Playback_YouTube_To_DTV.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import pytest
import os
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.playback.Youtube import YoutubeFunc
from lib.common.system.ADB import ADB
from tools.yamlTool import yamlTool

dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
youtube = YoutubeFunc()
adb = ADB()

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_repeat_count = p_conf_dvb['switch_player_count']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb.connect_external_wifi()
    dvb_stream.start_dvbc_stream('BBC_MUX_UH')
    dvb.start_livetv_apk_and_manual_scan()
    dvb_check.check_play_status_main_thread(10)
    # omx 打印
    if youtube.getprop("ro.build.version.sdk") == "34":
        youtube.open_media_codec_info()
    else:
        youtube.open_omx_info()
    yield
    if youtube.getprop("ro.build.version.sdk") == "34":
        youtube.close_media_codec_info()
    else:
        youtube.close_omx_info()
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    youtube.stop_youtube()


# @pytest.mark.flaky(reruns=3)
def test_check_program_playback():
    for i in range(p_conf_repeat_count):
        logging.info(f'------The {i + 1} times------')
        youtube.start_play()
        dvb_check.check_play_status_main_thread(10)
        dvb.start_livetv_apk()
        dvb_check.check_play_status_main_thread(10)
