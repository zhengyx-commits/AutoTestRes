#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/30
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_Channel_Time_Cross_Frequency_HD_To_HD.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import time
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

p_conf_dvb = config_yaml.get_note('conf_switch_channel_kpi')
p_conf_switch_channel_time = p_conf_dvb['cross_fre_hd_to_jd_time']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_multi_stream_diff_frq(0, 'ts', '4KH265', 'TRT_4K')
    dvb.start_livetv_apk_and_manual_scan(fre_count=2)
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    dvb_check.clear_multi_frq_program_information()


def test_check_switch_channel_time():
    assert dvb_check.check_switch_channel_time(p_conf_switch_channel_time)
