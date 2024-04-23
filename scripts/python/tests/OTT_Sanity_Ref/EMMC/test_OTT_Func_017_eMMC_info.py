# !/usr/bin python3
# -*- coding: utf-8 -*-
# @author     : chao.li
# @software   : PyCharm
# @file       : test_OTT-Sanity_Func_40_42_43_eMMC&DDR4.py
# @Time       : 2021/7/5 下午2:08
import logging
import time

from lib.common.system.Emmc import Emmc
from lib.common.system.ADB import ADB
from lib import *
import pytest
import re

from lib.common.system.SerialPort import SerialPort

if isinstance(pytest.config, list):
    for device_config in pytest.config:
        g_conf_port = device_config.get('device', {}).get('serial_port', '')
        g_conf_baud = device_config.get('device', {}).get('baudrate', '')
        ser = SerialPort(g_conf_port, g_conf_baud)
else:
    g_conf_port = pytest.config.get('device', {}).get('serial_port', '')
    g_conf_baud = pytest.config.get('device', {}).get('baudrate', '')
    ser = SerialPort(g_conf_port, g_conf_baud)
REBOOT_KERNEL_LOG = ''
GETPROP_COMMAND = 'getprop |grep gmsversion'
emmc = Emmc()
adb = ADB()
CLOSE_UPDATE = 'setenv loglevel 8;saveenv;'
p_result_path = f'{pytest.result_dir}/../../ddr_emmc_info.log'


# @pytest.mark.skip()
def test_Func_017_emmc():
    test_data = adb.checkoutput("dmesg | grep 'new HS'")
    # HS_info = re.findall(r' new HS(\d+) MMC', res, re.S)
    HS_info = re.findall(r' new HS(\d+) MMC', test_data, re.S)
    logging.info(f'eemmc_hs_info : HS{HS_info[-1]}')
    if HS_info:
        assert True
        f = open(p_result_path, 'a')
        f.write(f'eemmc_hs_info: HS{HS_info[-1]}')
        f.write('\n')
        f.close()
        assert 'HS' + HS_info[-1] == emmc.TYPE_400.decode('utf-8'), 'HS info not match HS200'
    else:
        assert False, "Can't find HS info"


@pytest.mark.skip()
def test_Sanity_Func_017():
    test_data = adb.checkoutput("dmesg | grep '8-bit-bus-width'")
    CLOCK_info = re.findall(r'clock (\d+), 8-bit-bus-width', test_data, re.S)
    logging.info(f'emmc_clock_info : {CLOCK_info[-1]}')
    if CLOCK_info:
        f = open(p_result_path, 'a')
        f.write(f'emmc_clock_info: {CLOCK_info[-1]}')
        f.write('\n')
        f.close()
        assert CLOCK_info[0] == '196463867', 'clock info not match 196463867'
    else:
        assert False, "Can't find clock info"
