#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/4 上午11:17
# @Author  : yongbo.shao
# @File    : test_DVB_Sanity_Func_136_HD_Start_KPI.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import re
import subprocess

import pytest
import logging


from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.system.Reboot import Reboot
from lib import *
from .. import config_yaml

logdir = pytest.result_dir
for g_conf_device_id in get_device():
    adb_cmd = ["/usr/bin/adb", "-s", g_conf_device_id, "shell", "logcat -s ActivityManager"]
    reboot = Reboot(adb_cmd=adb_cmd, device_id=g_conf_device_id, logdir=logdir)
p_conf_repeat_time = config_yaml.get_note("conf_start_kpi").get("time")


dvb_stream = DVBStreamProvider()
dvb = DVB()
dvb_check = DvbCheck()

video_name = "worldcup2014_8bit"  # UHD


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.repeat(p_conf_repeat_time)
def test_uhd_start_kpi():
    # reboot
    logging.info("start reboot")
    reboot_time = reboot.reboot_once()
    # send stream
    dvb_stream.start_dvbc_stream(video_name)
    # start play
    dvb.start_livetv_apk_and_manual_scan()
    # test HD start KPI
    flag, log = player_check.check_startPlay()
    if flag:
        startplay_time = player_check.get_startkpi_time()
        logging.info(f"startplay_time: {startplay_time}")
        assert startplay_time + reboot_time < 30
    else:
        assert False

    # test playback
    dvb_check.check_play_status_main_thread()



