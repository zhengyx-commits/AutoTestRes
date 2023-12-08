#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/7
# @Author  : Kejun.chen
# @File    : test_DVB_Sanity_Func_Quick_Scan.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm

import pytest

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from . import *

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
video_name = 'Netherlands_DVBC_250'


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_quick_scan_stream(video_name, para='64QAM')
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    dvb_check.clear_multi_frq_program_information()


# @pytest.mark.skip
def test_check_switch_channel():
    dvb.start_livetv_apk_and_quick_scan(searchtype='quick')
    dvb_check.check_play_status_main_thread(10)
