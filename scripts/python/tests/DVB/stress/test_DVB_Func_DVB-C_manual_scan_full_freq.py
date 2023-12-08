#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/1/11
# @Author  : kejun.chen
# @File    : test_DVB_Func_DVB-C_manual_scan_full_freq.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
from . import *
from ..PVR import pytest, dvb_stream, dvb, dvb_check

video_name = 'gr1'

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_scan_count = p_conf_dvb['full_freq_manual_scan_count']
p_conf_freq = config_yaml.get_note('conf_freq')


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb.remove_full_scan_log()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.stress_test
@pytest.mark.repeat(p_conf_scan_count)
def test_hotplug_rf():
    logging.info(f'test list get : {p_conf_freq}')
    for i in range(len(p_conf_freq)):
        dvb_stream.start_dvbc_stream_with_given_freq(given_freq=p_conf_freq[i], video_name=video_name)
        dvb.start_livetv_apk_and_manual_scan_full_freq(freq=p_conf_freq[i])
        dvb_check.check_play_status_main_thread(timeout=10)
        dvb_stream.stop_dvb()
