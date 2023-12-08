#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/6
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVBC_Stress_Player_Switch.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import os
import subprocess

import pytest

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.playback.Netflix import Netflix
from lib.common.playback.Youtube import YoutubeFunc
from lib.common.playback.MultiMediaPlayer import MultiPlayer
from lib.common.system.ADB import ADB
from lib import get_device
from tools.yamlTool import yamlTool



multi = MultiPlayer()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
netflix = Netflix()
youtube = YoutubeFunc()
adb = ADB()

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_repeat_count = p_conf_dvb['dvbc_stress_player_switch_time']
video_name = 'gr1'


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb.connect_external_wifi()
    multi.multi_setup()
    netflix.netflix_setup_with_files('dvb_stress_player_switch')
    dvb_stream.start_dvbc_stream(video_name, list_index=4)
    dvb.start_livetv_apk_and_manual_scan(list_index=4)
    logging.info('start dump log')
    dvb.get_target('debug/dump_kernel.sh')
    adb.push('res/debug/dump_kernel.sh', '/data/')
    adb.run_shell_cmd("nohup sh /data/dump_kernel.sh /data/kernel_player_switch.log > /dev/null 2>&1 &")
    logging.info('end dump log')
    dvb_check.check_play_status_main_thread(10)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb(list_index=4)
    multi.stop_multiPlayer_apk()
    netflix.stop_netflix()
    youtube.stop_youtube()


# @pytest.mark.flaky(reruns=3)
def test_check_program_playback():
    start_cmd = multi.start_play_cmd(1, 'http_TS_H264_4K')
    for i in range(p_conf_repeat_count):
        logging.info(f'------The {i + 1} times------')
        multi.send_cmd(start_cmd)
        dvb_check.check_play_status_main_thread(10)
        dvb.start_livetv_apk()
        dvb_check.check_play_status_main_thread(10)
        netflix.start_play()
        dvb_check.check_play_status_main_thread(10)
        dvb.start_livetv_apk()
        dvb_check.check_play_status_main_thread(10)
        youtube.start_play()
        dvb_check.check_play_status_main_thread(10)
        dvb.start_livetv_apk()
        dvb_check.check_play_status_main_thread(10)
