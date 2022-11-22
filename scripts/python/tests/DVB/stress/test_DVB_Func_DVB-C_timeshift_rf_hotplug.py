#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/2
# @Author  : kejun.chen
# @File    : test_DVB_Func_DVB-C_timeshift_rf_hotplug.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import time
import logging
from . import *

from ..PVR import pytest, dvb_stream, dvb, dvb_check, playerCheck

video_name = 'gr1'

p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_rf_hotplug_count = p_conf_dvb['timeshift_rf_hotplug_count']


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.flaky(reruns=3)
def test_hotplug_rf():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    for i in range(p_conf_rf_hotplug_count):
        logging.info(f'------The {i+1} times------')
        dvb.timeshift_start()
        assert dvb_check.check_timeshift_start()
        time.sleep(10)
        dvb_stream.stop_dvb()
        dvb_stream.start_dvbc_stream(video_name)
        time.sleep(10)
        dvb.timeshift_stop()
        assert dvb_check.check_timeshift_stop()
