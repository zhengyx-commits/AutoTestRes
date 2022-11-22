#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/8
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Auto_Scan.py
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


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('gr1')
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_check_switch_channel():
    dvb.start_livetv_apk_and_auto_scan()
    dvb_check.check_play_status_main_thread(10)
