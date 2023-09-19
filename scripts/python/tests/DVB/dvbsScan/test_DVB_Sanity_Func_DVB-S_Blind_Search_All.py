#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/20
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVB-S_Blind_Search_All.py
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
from . import install_suspend_apk
from .. import config_yaml

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()
p_conf_suspend = config_yaml.get_note("conf_suspend_time")
p_conf_suspend_time = p_conf_suspend.get("suspend_time")

# video_name = 'Liverpool'
video_name = 'gr1'


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    install_suspend_apk()
    dvb_stream.start_dvbs_stream(video_name=video_name)
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
    dvb.select_satellite('all')
    time.sleep(10)
    assert dvb_check.check_select_satellite()
    # dvb.set_up_dvbs_parameter()
    dvb.dvbs_scan(search_mode='blind')
    assert dvb_check.check_dvbs_scan(timeout=43200)
    # suspend
    logging.info("start suspend")
    dvb.run_shell_cmd("am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command suspend")
    time.sleep(p_conf_suspend_time)
    # wake up
    logging.info("start wakeup")
    dvb.run_shell_cmd("am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command wakeup")
    dvb_check.check_play_status_main_thread()
    # dvb.set_up_dvbs_parameter()
    # dvb.reset_satellite_selection('all')
    # assert dvb_check.check_reset_satellite_selection()
