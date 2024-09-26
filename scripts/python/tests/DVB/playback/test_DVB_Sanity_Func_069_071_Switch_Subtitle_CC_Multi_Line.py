#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/18
# @Author  : jianhua.huang
# @File    : test_DVB_Sanity_Func_Switch_Subtitle_CC_Multi_Line.py
# @Email   : jianhua.huang@amlogic.com
# @Ide: PyCharm
import logging
import time

import pytest

from lib.common.system.ADB import ADB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.tools.DVB import DVB
from lib.common.tools.Subtitle import Subtitle
from tools.DVBStreamProvider import DVBStreamProvider

adb = ADB()
dvb = DVB()
dvb_check = DvbCheck()
subtitle = Subtitle()
dvb_stream = DVBStreamProvider()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    adb.clear_logcat()
    dvb_stream.start_dvbc_stream('CC-subtitle')
    p_subtitle_mode = dvb_check.get_subtitle_mode('CC-subtitle_150_ems.ts')
    assert p_subtitle_mode == 'cc'
    yield
    dvb.stop_livetv_apk()
    dvb.home()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
# @pytest.mark.flaky(reruns=3)
def test_check_switch_channel():
    dvb.setprop(key='persist.vendor.tif.subtitleflg', value='0xFF', timeout=10)
    # logging.info('dut reboot ....')
    # dvb.reboot()
    # start_time = time.time()
    # logging.debug("Waiting for bootcomplete")
    # while time.time() - start_time < 30:
    #     reboot_check = dvb.run_shell_cmd('getprop sys.boot_completed')[0]
    #     if reboot_check == '1':
    #         logging.info("Device booted up !!!!")
    #         break
    #     else:
    #         time.sleep(5)
    # check_time = time.time()
    # while time.time() - check_time < 60:
    #     if dvb.find_element('Add account', 'text') or dvb.find_element('Search', 'text'):
    #         break
    #     else:
    #         time.sleep(5)
    # dvb.root()
    # dvb.dvb_environment_detection()
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(5)
    # subtitle.check_subtitle_thread('CC', 'LiveTv')
    time.sleep(15)
    dvb_check.check_play_status_main_thread()
