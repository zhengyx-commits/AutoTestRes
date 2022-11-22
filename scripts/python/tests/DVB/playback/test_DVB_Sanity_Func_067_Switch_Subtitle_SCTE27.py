#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/18
# @Author  : jianhua.huang
# @File    : test_DVB_Sanity_Func_Switch_Subtitle_SCTE27.py
# @Email   : jianhua.huang@amlogic.com
# @Ide: PyCharm
import logging
import time
import pytest
from lib.common.system.ADB import ADB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.tools.DVB import DVB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.Subtitle import Subtitle
from tests.DVB import *

adb = ADB()
dvb = DVB()
dvb_check = DvbCheck()
dvb_stream = DVBStreamProvider()
subtitle = Subtitle()
p_config_channel_name = config_yaml.get_note('conf_channel_name')['scte27']
p_config_channel_dif = config_yaml.get_note('conf_channel_dif_id')['scte27']


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    dvb_stream.start_dvbc_stream('subtitle_scte20_scte27')
    adb.clear_logcat()
    dvb.start_livetv_apk()
    q_channel_id_list = dvb_check.get_channel_id()
    q_channel_id = q_channel_id_list[p_config_channel_dif]
    dvb.switch_channel(q_channel_id)
    logging.info(f'target channel id : {q_channel_id}')
    assert dvb_check.check_switch_channel(), f'switch channel to {q_channel_id} failed.'
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.skip
# @pytest.mark.flaky(reruns=3)
def test_check_switch_channel():
    dvb.switch_subtitle_type(subtitle_type=0)
    subtitle.start_subtitle_datathread('scte27', 'LiveTV')
    assert subtitle.subtitleThread.is_alive()
    time.sleep(15)
    logging.info(f'{subtitle.error} , {subtitle.got_spu}, {subtitle.show_spu} ,{subtitle.subtitle_window}')
    assert (subtitle.error == 0) & (subtitle.got_spu != '') & (subtitle.show_spu != '') & (
            subtitle.subtitle_window != ''), \
        'There are some problems with the subtitle shows'
    dvb_check.check_play_status_main_thread()
