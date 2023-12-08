#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/3/29
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVBC_Stress_Playback.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import pytest
from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from . import *

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

video_name = 'gr1'
p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_playback_time = p_conf_dvb['dvbc_stress_playback_time']


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name, list_index=4)
    dvb.start_livetv_apk_and_manual_scan(list_index=4)
    logging.info('start dump log')
    dvb.get_target('debug/dump_kernel.sh')
    adb.push('res/debug/dump_kernel.sh', '/data/')
    adb.run_shell_cmd("nohup sh /data/dump_kernel.sh /data/kernel_playback.log > /dev/null 2>&1 &")
    logging.info('end dump log')
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb(list_index=4)


def test_stress_playback():
    dvb_check.check_play_status_main_thread(p_conf_playback_time)
