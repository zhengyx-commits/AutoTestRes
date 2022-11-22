#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/13
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Plug_Signal_H265_4k.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
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
p_conf_plug_count = p_conf_dvb['plug_count']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('worldcup2014_8bit')
    adb.clear_logcat()
    dvb.start_livetv_apk()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.stress_test
def test_check_plug_signal():
    for i in range(p_conf_plug_count):
        dvb_stream.stop_dvb()
        dvb_stream.start_dvbc_stream('worldcup2014_8bit')
        dvb_check.check_play_status_main_thread(10)
