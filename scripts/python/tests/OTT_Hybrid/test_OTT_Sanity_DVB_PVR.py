#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/12/28 14:42
# @Author  : chao.li
# @Site    :
# @File    : test_OTT_Sanity_DVB_PVR.py
# @Software: PyCharm
import logging

from lib.OTT.S905Y4.HybridDTV import HybirdDtv
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from . import *
import time
import pytest

dtv = HybirdDtv()
playerCheck = PlayerCheck_Base()
sign_status = False

p_conf_dvb = config_yaml.get_note('conf_dvb')
p_conf_uuid = p_conf_dvb['uuid']


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
    dtv.checkoutput_term(f'rm -rf /storage/{p_conf_uuid}/PVR_DIR')
    yield
    dtv.home()


@pytest.mark.skipif(condition=(1 - sign_status), reason='No channel')
def test_channel_switch():
    time.sleep(3)
    # pause
    dtv.keyevent(85)
    assert dtv.checkoutput(f'[ /storage/{p_conf_uuid}/PVR_DIR/ ] && echo yes || echo no').strip() == 'yes'
    time.sleep(3)
    dtv.keyevent(85)
    # playerCheck.run_check_main_thread(30)
    time.sleep(5)
    log, logfile = dtv.save_logcat('seeklogcat', tag=dtv.FRAGMENT_TAG)
    dtv.keyevent(22)
    dtv.keyevent(22)
    time.sleep(5)
    dtv.stop_save_logcat(log, logfile)
    logresult = ''
    with open(logfile.name, 'r') as f:
        logresult = f.read()
    assert 'isSeeking : true' in logresult
