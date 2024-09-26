#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/15
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVB-S_Blind_Search_TP.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time
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
TP_freq_list = [10950, 11800]
TP_polarity_list = ['H', 'V']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    # dvb_stream.start_dvbs_stream(video_name, freq=12000)
    # DTU315 does not support this frequency(12000)
    dvb_stream.start_dvbs_stream(video_name, freq=1150)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    logging.info('start remove TP.')
    dvb.start_livetv_apk()
    dvb.set_channel_mode_dvbs()
    dvb.set_up_dvbs_parameter()
    for i in range(len(TP_freq_list)):
        for j in range(len(TP_polarity_list)):
            dvb.remove_transponder(tp_name=f'{TP_freq_list[i]}{TP_polarity_list[i]}27500')
            assert dvb_check.check_remove_transponder()
            time.sleep(3)
    dvb.home()
    time.sleep(1)
    dvb.reset_dvbs_param('all')


def test_dvb_scan():
    dvb.start_livetv_apk()
    dvb.set_channel_mode_dvbs()
    dvb.set_up_dvbs_parameter()
    dvb.set_lnb_type(lnb_type='0')
    dvb.select_satellite(0)
    assert dvb_check.check_select_satellite()
    dvb.set_test_satellite(0)
    assert dvb_check.check_set_test_satellite()
    for i in range(len(TP_freq_list)):
        for j in range(len(TP_polarity_list)):
            logging.info('start add TP.')
            dvb.add_transponder(freq=TP_freq_list[i], polarity=TP_polarity_list[i])
            assert dvb_check.check_add_transponder()
    # dvb.set_up_dvbs_parameter()
    dvb.dvbs_scan(search_mode='blind')
    assert dvb_check.check_dvbs_scan(timeout=7200)
    dvb_check.check_play_status_main_thread()
