#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/28
# @Author  : jianhua.huang
# @File    : test_DVB_Sanity_Func_Switch_Teletext_INTERRUPT_SIGNAL.py
# @Email   : jianhua.huang@amlogic.com
# @Ide: PyCharm
import logging
import threading
import time

import pytest

from lib.common.system.ADB import ADB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.tools.DVB import DVB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.Subtitle import Subtitle

adb = ADB()
dvb = DVB()
dvb_check = DvbCheck()
dvb_stream = DVBStreamProvider()
subtitle = Subtitle()


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    # dvb.check_display_mode()
    dvb_stream.start_dvbc_stream('14_TMC')
    adb.clear_logcat()
    dvb.start_livetv_apk()
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
# @pytest.mark.flaky(reruns=3)
def test_check_switch_teletext_interrupt_signal():
    dvb.switch_teletext()
    subtitle.start_subtitle_datathread('Teletext', 'LiveTV')
    assert subtitle.subtitleThread.is_alive()
    time.sleep(15)
    logging.debug(
        f'subtitle.got_spu : {subtitle.got_spu}; subtitle.show_spu : {subtitle.show_spu} ; subtitle.subtitle_window: {subtitle.subtitle_window}')
    assert (subtitle.got_spu != '') & (subtitle.show_spu != '') & (
            subtitle.subtitle_window != ''), \
        'There are some problems with the subtitle shows'
    dvb_check.check_play_status_main_thread()
    logging.info('DVB interrupt signal ...')
    dvb_stream.stop_dvb()
    time.sleep(10)
    dvb_stream.start_dvbc_stream('14_TMC')
    dvb.clear_logcat()
    # subtitle.start_subtitle_datathread('Teletext', 'LiveTV')
    # assert subtitle.subtitleThread.is_alive()
    # time.sleep(15)
    # logging.debug(
    #     f'subtitle.got_spu : {subtitle.got_spu}; subtitle.show_spu : {subtitle.show_spu} ; subtitle.subtitle_window: {subtitle.subtitle_window}')
    # assert (subtitle.got_spu != '') & (subtitle.show_spu != ''), \
    #     'There are some problems with the subtitle shows'
    dvb_check.check_play_status_main_thread()
