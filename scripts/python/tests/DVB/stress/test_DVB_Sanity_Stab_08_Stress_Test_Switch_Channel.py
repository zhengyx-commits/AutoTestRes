#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/18
# @Author  : jianhua.huang
# @File    : test_DVB_Sanity_Func_Stress_Test_Switch_Channel.py
# @Email   : jianhua.huang@amlogic.com
# @Ide: PyCharm

import logging
import time
import pytest
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.tools.DVB import DVB
from tools.DVBStreamProvider import DVBStreamProvider
from tests.DVB import *
from lib.common.tools.Subtitle import Subtitle

dvb = DVB()
dvb_check = DvbCheck()
dvb_stream = DVBStreamProvider()
p_conf_dvb = config_yaml.get_note('conf_stress')
subtitle = Subtitle()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_multi_stream_diff_frq(0, 'ts', 'BBC_MUX_UH', 'MPTS1')
    dvb.start_livetv_apk_and_manual_scan(fre_count=2)
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
@pytest.mark.stress_test
def test_check_switch_channel():
    dvb.switch_subtitle_type(subtitle_type=0)
    # subtitle.check_subtitle_thread('Dvb', 'LiveTv')
    time.sleep(15)
    dvb_check.check_play_status_main_thread(timeout=20)
    p_start_time = time.time()
    switch_duration = float(p_conf_dvb['stress_switch_time']) * 3600
    logging.info(f'check time is {switch_duration}')
    dvb_check.check_play_status_sub_thread()
    while time.time() - p_start_time <= switch_duration:
        logging.info('switch channel ...')
        dvb.keyevent(20)
        time.sleep(2)
