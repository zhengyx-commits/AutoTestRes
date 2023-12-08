#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/3/29
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVBC_Stress_Scan.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import os
import subprocess
import time
import pytest
from lib.common.system.ADB import ADB
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from . import *
from tests.DVB import PreOperation

preOperation = PreOperation()
adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

video_name = 'gr1'
p_conf_dvb = config_yaml.get_note('conf_stress')
p_conf_scan_count = p_conf_dvb['dvbc_stress_scan_count']


@pytest.fixture(scope='session', autouse=True)
def setup_teardown():
    preOperation.disable_wifi()
    dvb_stream.start_dvbc_stream(video_name, list_index=2)
    logging.info('start dump log')
    dvb.get_target('debug/dump_kernel.sh')
    adb.push('res/debug/dump_kernel.sh', '/data/')
    adb.run_shell_cmd("nohup sh /data/dump_kernel.sh /data/kernel_scan.log > /dev/null 2>&1 &")
    # os.system(
    #     f"adb -s {adb.serialnumber} shell \"nohup sh /data/dump_kernel.sh /data/kernel_scan.log > /dev/null 2>&1 &\"")
    logging.info('end dump log')
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb(list_index=2)


# @pytest.mark.repeat(p_conf_scan_count)
def test_stress_scan():
    for i in range(p_conf_scan_count):
        logging.info(f'start the {i + 1} times test.')
        dvb.start_livetv_apk_and_manual_scan(list_index=2)
        time.sleep(3)
