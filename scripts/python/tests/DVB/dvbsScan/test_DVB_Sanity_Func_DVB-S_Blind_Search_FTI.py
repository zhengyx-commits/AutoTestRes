#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/28
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVB-S_Blind_Search_FTI.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import pytest

from lib.common.system.ADB import ADB
# from tools.DVBStreamProvider import DVBStreamProvider
from tools.DVBStreamProvider_Linux import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

video_name = 'gr1'


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbs_stream(video_name)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    dvb.reset_dvbs_param('all')


def test_dvb_scan():
    dvb.start_livetv_apk()
    dvb.set_channel_mode_dvbs()
    dvb.set_up_dvbs_parameter()
    dvb.set_lnb_type(lnb_type='0')
    # assert dvb_check.check_set_lnb_type(1)
    dvb.select_satellite(0)
    assert dvb_check.check_select_satellite()
    dvb.set_test_satellite(0)
    assert dvb_check.check_set_test_satellite()
    # dvb.set_up_dvbs_parameter()
    dvb.dvbs_scan(search_mode='blind')
    assert dvb_check.check_dvbs_scan(timeout=7200)
    dvb_check.check_play_status_main_thread()
    # channel_id = dvb_check.get_channel_id()
    # logging.info(f'channel_id : {channel_id}')
    # dvb_check.get_pid_before_switch()
    # length = len(channel_id)
    for i in range(6):
        # dvb.switch_channel(channel_id[i])
        # logging.info(f'switch channel id : {channel_id[i]}')
        dvb.keyevent(20)
        assert dvb_check.check_switch_channel(), f'switch channel failed.'
        dvb_check.check_play_status_main_thread(5)
