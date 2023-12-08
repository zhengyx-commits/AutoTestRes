#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/30
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_Program_Playback_Encryption_To_Encryption.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import time

import pytest
from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from lib.common.system.Reboot import Reboot
from lib import get_device
from tests.DVB import PreOperation

preOperation = PreOperation()
adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

logdir = pytest.result_dir
for g_conf_device_id in get_device():
    adb_cmd = ["/usr/bin/adb", "-s", g_conf_device_id, "shell", "logcat -s ActivityManager"]
    reboot = Reboot(adb_cmd=adb_cmd, device_id=g_conf_device_id, logdir=logdir)


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    preOperation.delete_udisk_recorded()
    reboot.reboot_once()
    dvb_stream.start_dvbc_multi_stream_diff_frq(0, 'ts', 'iptv_test', 'gr1')
    dvb.start_livetv_apk_and_manual_scan(fre_count=2)
    time.sleep(5)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()
    dvb_check.clear_multi_frq_program_information()


@pytest.mark.skip
# @pytest.mark.flaky(reruns=3)
def test_check_program_playback():
    # dvb.set_channel_mode()
    # dvb.auto_search()
    # assert dvb_check.check_search_ex()
    channel_id = dvb_check.get_channel_id()
    logging.info(f'channel_id : {channel_id}')
    dvb_check.get_pid_before_switch()
    length = len(channel_id)
    for i in range(length):
        adb.keyevent(20)
        logging.info(f'switch channel id : {channel_id[i]}')
        assert dvb_check.check_switch_channel(), f'switch channel to {channel_id[i]} failed.'
        dvb_check.check_play_status_main_thread(5)

