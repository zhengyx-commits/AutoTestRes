#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/1
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Program_Playback_Multi-Media_To_DTV.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time
import pytest
import os

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.system.ADB import ADB
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.playback.MultiMediaPlayer import MultiPlayer
from lib import get_device
from tools.yamlTool import yamlTool

for g_conf_device_id in get_device():
    multi = MultiPlayer()
adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_repeat_count = p_conf_dvb['switch_player_count']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('BBC_MUX_UH')
    multi.multi_setup()
    dvb.start_livetv_apk_and_manual_scan()
    dvb_check.check_play_status_sub_thread()
    time.sleep(10)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    multi.stop_multiPlayer_apk()


# @pytest.mark.flaky(reruns=3)
def test_check_program_playback():
    for i in range(p_conf_repeat_count):
        logging.info(f'------The {i + 1} times------')
        start_cmd = multi.start_play_cmd(1, 'http_TS_H264_4K')
        multi.send_cmd(start_cmd)
        dvb_check.check_play_status_main_thread(10)
        dvb.start_livetv_apk()
        time.sleep(10)
