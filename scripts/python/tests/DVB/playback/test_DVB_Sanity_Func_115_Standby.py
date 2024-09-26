#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/4 上午11:17
# @Author  : yongbo.shao
# @File    : test_DVB_Sanity_Func_115_Standby.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm

import pytest
import logging
import time

from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from . import install_suspend_apk
from .. import config_yaml
from lib.common.tools.Subtitle import Subtitle

dvb_stream = DVBStreamProvider()
dvb = DVB()
dvb_check = DvbCheck()
subtitle = Subtitle()
p_conf_suspend = config_yaml.get_note("conf_suspend_time")
p_conf_suspend_time = p_conf_suspend.get("suspend_time")
p_conf_play_time_after_wakeup = p_conf_suspend.get("play_time_after_wakeup")
p_conf_standby_repeat_time = config_yaml.get_note("conf_stress").get("115_standby_count")

video_name = "BBC_MUX_UH"


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    install_suspend_apk()
    # start send stream
    dvb_stream.start_dvbc_stream(video_name)
    dvb.start_livetv_apk_and_manual_scan()
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


def test_standby():
    for i in range(p_conf_standby_repeat_time):
        channel_id_before = dvb.get_current_channel_info()[1]
        logging.info(f'channel_id : {channel_id_before}')

        # test playback
        dvb_check.check_play_status_main_thread()

        # suspend
        logging.info(f'------The {i + 1} times------')
        logging.info("start suspend")
        dvb.run_shell_cmd("am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command suspend")
        time.sleep(p_conf_suspend_time)

        # wake up
        logging.info("start wakeup")
        dvb.run_shell_cmd("am broadcast -n com.droidlogic.suspend/.SuspendReceiver -a suspend.test --es command wakeup")

        # check channel id after wake up
        channel_id_after = dvb.get_current_channel_info()[1]
        logging.info(f'channel_id : {channel_id_after}')
        assert channel_id_after == channel_id_before
        # subtitle check
        # dvb.switch_subtitle_type(subtitle_type=0)
        # subtitle.check_subtitle_thread('Dvb', 'LiveTv')
        time.sleep(15)
        dvb_check.check_play_status_main_thread()
