#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/20
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVB-S_Unicable_Satellite_Search.py
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
lnb_type = ['0', '2', 'customize']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbs_stream(video_name=video_name)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_dvb_scan():
    dvb.start_livetv_apk()
    dvb.set_up_dvbs_parameter()
    dvb.set_test_satellite(1)
    assert dvb_check.check_set_test_satellite()
    for lnb in lnb_type:
        for band in range(8):
            dvb.set_lnb_type(lnb)
            assert dvb_check.check_set_lnb_type(lnb)
            dvb.set_unicable(unicable_switch=1, user_band=band, position=1)
            dvb.dvbs_scan()
            assert dvb_check.check_dvbs_scan()
            dvb_check.check_play_status_sub_thread()
            channel_id = dvb_check.get_channel_id()
            logging.info(f'channel_id : {channel_id}')
            dvb_check.get_pid_before_switch()
            length = len(channel_id)
            for i in range(length):
                dvb.switch_channel(channel_id[i])
                logging.info(f'switch channel id : {channel_id[i]}')
                assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i]} failed.'
                dvb_check.check_play_status_main_thread(5)
