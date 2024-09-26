#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/12/23 16:11
# @Author  : chao.li
# @Site    :
# @File    : test_OTT-Sanity_Program_Switch.py
# @Software: PyCharm


import logging
import time

import pytest

from lib.OTT.S905Y4.HybridDTV import HybirdDtv
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base

dtv = HybirdDtv()
playerCheck = PlayerCheck_Base()
sign_status = False


def check_signal():
    global sign_status
    dtv.start_activity(*dtv.DTV_ACTIVITY_TUPLE)
    time.sleep(5)
    dtv.uiautomator_dump()
    if 'No Channel' in dtv.get_dump_info() or 'Weak signal' in dtv.get_dump_info():
        sign_status = False
    else:
        sign_status = True


check_signal()


@pytest.fixture(autouse=True)
def setup_teardown():
    dtv.start_activity(*dtv.DTV_ACTIVITY_TUPLE)
    yield
    dtv.home()


@pytest.mark.skipif(condition=(1 - sign_status), reason='No channel')
def test_channel_switch():
    for i in range(5):
        assert playerCheck.run_check_main_thread(10), 'playback error'
        dtv.keyevent(20)
