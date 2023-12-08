#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/30
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Switch_Subtitle_During_Timeshift_HOH.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import time
import logging

from tests.DVB.PVR import pytest, dvb_stream, dvb, dvb_check
from lib.common.tools.Subtitle import Subtitle

video_name = '14_TMC'
subtitle = Subtitle()


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    dvb_stream.start_dvbc_stream(video_name)
    # dvb.check_display_mode()
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(3)
    for i in range(20):
        number = dvb.get_subtitle_list()
        logging.info(f'number {number}')
        if number != 0:
            break
        # switch to channel 3
        dvb.keyevent(10)
        time.sleep(5)
    else:
        raise EnvironmentError('Not subtitle found!')
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
def test_play_multi_language_program():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    dvb.timeshift_start()
    assert dvb_check.check_timeshift_start()
    time.sleep(5)
    dvb.keyevent(23)
    dvb_check.check_play_status_main_thread(10)
    dvb.switch_subtitle_type(subtitle_type=1)
    # assert dvb_check.check_subtitle_current_language(switch_type=0)
    subtitle.check_subtitle_thread('HOH', 'LiveTv')
    time.sleep(15)
    dvb_check.check_play_status_main_thread(10)
    dvb.timeshift_stop()
    assert dvb_check.check_timeshift_stop()
