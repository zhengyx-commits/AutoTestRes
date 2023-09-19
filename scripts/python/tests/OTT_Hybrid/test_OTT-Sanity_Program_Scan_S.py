#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/12/22 14:27
# @Author  : chao.li
# @Site    :
# @File    : test_OTT-Sanity_Program_Scan_S.py
# @Software: PyCharm


import logging
import time
import pytest
from lib.OTT.S905Y4.HybridDTV import HybirdDtv

dtv = HybirdDtv()
config = pytest.config.get('dvb', {})
channel_count = config.get('DVB-S', {}).get('channel_count', 6)
frequency_point = config.get('DVB-S', {}).get('frequency_point', 578)


@pytest.fixture(autouse=True)
def setup_teardown():
    dtv.select_type('DVB-S')
    time.sleep(1)
    yield
    dtv.home()
    dtv.run_shell_cmd('am force-stop com.droidlogic.android.tv')
    time.sleep(3)
