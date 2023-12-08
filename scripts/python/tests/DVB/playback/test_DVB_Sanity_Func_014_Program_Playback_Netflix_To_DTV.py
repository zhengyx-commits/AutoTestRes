#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/1
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Program_Playback_Netflix_To_DTV.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import os
import time
import pytest

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.playback.Netflix import Netflix
from lib.common.system.ADB import ADB
from tools.yamlTool import yamlTool

dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
netflix = Netflix()
adb = ADB()

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_repeat_count = p_conf_dvb['switch_player_count']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb.connect_external_wifi()
    dvb_stream.start_dvbc_stream('BBC_MUX_UH')
    netflix.netflix_setup_with_files(target='dvb_trunk')
    dvb.start_livetv_apk_and_manual_scan()
    dvb_check.check_play_status_main_thread(10)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    netflix.stop_netflix()


# @pytest.mark.flaky(reruns=3)
def test_check_program_playback():
    for i in range(p_conf_repeat_count):
        logging.info(f'------The {i + 1} times------')
        netflix.start_play()
        dvb_check.check_play_status_main_thread(10)
        dvb.start_livetv_apk()
        dvb_check.check_play_status_main_thread(10)
