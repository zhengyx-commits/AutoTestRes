#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/12/22 14:42
# @Author  : chao.li
# @Site    :
# @File    : test_OTT-Sanity_Program_Scan_C.py
# @Software: PyCharm

import logging
import time
import pytest
from lib.OTT.S905Y4.HybridDTV import HybirdDtv
from . import *

dtv = HybirdDtv()

p_conf_dvb = config_yaml.get_note('conf_dvb')
p_conf_channel_count = p_conf_dvb['DVB-C']['channel_count']
p_conf_frequency_point = p_conf_dvb['DVB-C']['frequency_point']
# logging.info(f'scan_c p_conf_channel_count:{p_conf_channel_count}, p_conf_frequency_point:{p_conf_frequency_point}')


@pytest.fixture(autouse=True)
def setup_teardown():
    dtv.select_type('DVB-C')
    time.sleep(1)
    yield
    dtv.home()
    dtv.run_shell_cmd('am force-stop com.droidlogic.android.tv')
    time.sleep(3)



def test_channel_scan():
    log, logfile = dtv.save_logcat('channel_result.log', 'ChannelTuner')
    dtv.find_and_tap('SCAN MENU', 'text')
    time.sleep(1)
    dtv.find_and_tap('com.droidlogic.dtvkit.inputsource:id/public_search_mode_spinner', 'resource-id')
    dtv.find_and_tap('Auto', 'text')
    dtv.find_and_tap('AUTO SEARCH', 'text')
    dtv.uiautomator_dump()
    start = time.time()
    while 'DVB SEARCH' in dtv.get_dump_info() and time.time() - start < 300:
        logging.debug('Still searching ')
        time.sleep(3)
        dtv.uiautomator_dump()
    time.sleep(10)
    dtv.stop_save_logcat(log, logfile)

    result = dtv.checkoutput_term(f'cat {logfile.name}')
    assert 'updateBrowsableChannelsLocked mBrowsableChannels.size(): ' + str(p_conf_channel_count) in result



def test_channel_manual_scan():
    log, logfile = dtv.save_logcat('channel_result.log', 'ChannelTuner')
    dtv.find_and_tap('SCAN MENU', 'text')
    time.sleep(1)
    dtv.find_and_tap('com.droidlogic.dtvkit.inputsource:id/public_search_mode_spinner', 'resource-id')
    dtv.find_and_tap('Manual', 'text')
    dtv.find_and_tap('MHz', 'text')
    dtv.text(p_conf_frequency_point)
    dtv.keyevent(4)
    dtv.find_and_tap('MANUAL SEARCH', 'text')
    start = time.time()
    while 'DVB SEARCH' in dtv.get_dump_info() and time.time() - start < 300:
        logging.debug('Still searching ')
        time.sleep(3)
        dtv.uiautomator_dump()
    time.sleep(10)
    dtv.stop_save_logcat(log, logfile)

    result = dtv.checkoutput_term(f'cat {logfile.name}')
    assert 'updateBrowsableChannelsLocked mBrowsableChannels.size(): ' + str(p_conf_channel_count) in result
