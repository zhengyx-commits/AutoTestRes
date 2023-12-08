#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/29
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_Channel_Time_Same_Frequency_SD_To_SD.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import pytest
from . import *

from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

p_conf_dvb = config_yaml.get_note('conf_switch_channel_kpi')
p_conf_switch_channel_time = p_conf_dvb['same_fre_sd_to_sd_time']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('gr1')
    dvb.start_livetv_apk_and_manual_scan()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
def test_check_switch_channel_time():
    assert dvb_check.check_switch_channel_time(p_conf_switch_channel_time)
