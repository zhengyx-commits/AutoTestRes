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
    dvb_stream.start_dvbc_stream('BBC_MUX_UH')
    dvb.clear_logcat()
    dvb.start_livetv_apk()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
@pytest.mark.stress_test
def test_check_switch_channel():
    dvb.switch_subtitle_type(subtitle_type=0)
    subtitle.start_subtitle_datathread('Dvb', 'LiveTV')
    assert subtitle.subtitleThread.is_alive()
    time.sleep(15)
    logging.info(f'{subtitle.error} , {subtitle.got_spu}, {subtitle.show_spu} ,{subtitle.subtitle_window}')
    assert (subtitle.error == 0) & (subtitle.got_spu != '') & (subtitle.show_spu != '') & (
            subtitle.subtitle_window != ''), \
        'There are some problems with the subtitle shows'
    dvb_check.check_play_status_main_thread(timeout=20)
    p_start_time = time.time()
    switch_duration = float(p_conf_dvb['stress_switch_time']) * 3600
    logging.info(f'check time is {switch_duration}')
    while time.time() - p_start_time <= switch_duration:
        logging.info('switch channel ...')
        dvb.keyevent(20)
        dvb_check.check_play_status_main_thread(timeout=20)
