#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/3/29
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVBC_Stress_Pvr.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import subprocess
import time
import pytest
from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from . import *
from lib.common.system.Reboot import Reboot
from lib import get_device
from tests.DVB import PreOperation

preOperation = PreOperation()
adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

video_name = 'gr1'
p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_pvr_count = p_conf_dvb['dvbc_stress_pvr_count']
logdir = pytest.result_dir
for g_conf_device_id in get_device():
    adb_cmd = ["/usr/bin/adb", "-s", g_conf_device_id, "shell", "logcat -s ActivityManager"]
    reboot = Reboot(adb_cmd=adb_cmd, device_id=g_conf_device_id, logdir=logdir)


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    preOperation.disable_wifi()
    preOperation.delete_udisk_recorded()
    reboot.reboot_once()
    dvb_stream.start_dvbc_stream(video_name, list_index=5)
    dvb.start_livetv_apk_and_manual_scan(list_index=5)
    logging.info('start dump log')
    dvb.get_target('debug/dump_kernel.sh')
    adb.push('res/debug/dump_kernel.sh', '/data/')
    adb.run_shell_cmd("nohup sh /data/dump_kernel.sh /data/kernel_pvr.log > /dev/null 2>&1 &")
    # os.system(
    #     f"adb -s {adb.serialnumber} shell \"nohup sh /data/dump_kernel.sh /data/kernel_pvr.log > /dev/null 2>&1 &\"")
    logging.info('end dump log')
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb(list_index=5)


# @pytest.mark.repeat(p_conf_pvr_count)
def test_stress_playback():
    assert dvb.getUUID() != 'emulated', "Doesn't get u-disk"
    for i in range(p_conf_pvr_count):
        logging.info(f'start the {i + 1} times test.')
        dvb.start_pvr_recording()
        # dvb.keyevent('KEYCODE_MEDIA_RECORD')
        assert dvb_check.check_start_pvr_recording()
        time.sleep(30)
        dvb.stop_pvr_recording()
        # dvb.keyevent('KEYCODE_MEDIA_RECORD')
        # time.sleep(1)
        # dvb.keyevent('23')
        assert dvb_check.check_stop_pvr_recording()
        dvb.pvr_start_play()
        assert dvb_check.check_pvr_start_play()
        dvb_check.check_play_status_main_thread(10)
        dvb.pvr_stop()
        assert dvb_check.check_pvr_stop()
        adb.keyevent(4)
        time.sleep(5)
