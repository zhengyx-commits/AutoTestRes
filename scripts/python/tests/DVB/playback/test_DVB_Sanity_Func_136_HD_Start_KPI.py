#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/4 上午11:17
# @Author  : yongbo.shao
# @File    : test_DVB_Sanity_Func_136_HD_Start_KPI.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import pytest
import logging
import time

from numpy import mean

from tools.DVBStreamProvider import DVBStreamProvider

from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.system.Reboot import Reboot
from lib import get_device
from .. import config_yaml


logdir = pytest.result_dir
for g_conf_device_id in get_device():
    adb_cmd = ["/usr/bin/adb", "-s", g_conf_device_id, "shell", "logcat -s ActivityManager"]
    reboot = Reboot(adb_cmd=adb_cmd, device_id=g_conf_device_id, logdir=logdir)
p_conf_repeat_time = config_yaml.get_note("conf_start_kpi").get("time")



dvb_stream = DVBStreamProvider()
dvb = DVB()
dvb_check = DvbCheck()

video_name = "gr1"  # HD
start_time_list = []


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


# @pytest.mark.repeat(p_conf_repeat_time)
def test_hd_start_kpi():
    start_play_time = 0
    for i in range(p_conf_repeat_time):
        # reboot
        logging.info("start reboot")
        reboot_time = reboot.reboot_once()
        # send stream
        dvb_stream.start_dvbc_stream(video_name)
        # start play
        start_play_time = time.time()
        dvb.start_livetv_apk_and_manual_scan()
        # test HD start KPI
        # flag, log = player_check.check_startPlay()
        # if flag:
            # start_play_time = player_check.get_startkpi_time()
        if dvb_check.check_start_play():
            end_kpi_time = time.time()
            start_time_list.append((end_kpi_time - start_play_time))
            logging.info(f"The start playback time list of the {i+1} times are: {start_time_list}")
        # test playback
        dvb_check.check_play_status_main_thread(10)
    # Average start kpi
    start_kpi = mean(start_time_list)
    logging.info(f'The average time is {start_kpi}')
    assert start_kpi < 30, 'The average start kpi is greater than 30 seconds!'
