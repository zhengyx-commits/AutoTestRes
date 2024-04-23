#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/9 下午1:39
# @Author  : yongbo.shao
# @File    : test_bluetooth.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import allure
from tests.OTT_Sanity_Ref import *

devices = get_device()


@pytest.fixture(scope='module', autouse=True)
def enable_bluetooth():
    adb.shell("svc bluetooth enable")
    yield
    adb.shell("svc bluetooth disable")


@pytest.fixture(scope='function', autouse=True)
def setup():
    adb.shell('am broadcast -p "android" --receiver-foreground -a android.intent.action.FACTORY_RESET')
    time.sleep(100)


@allure.step("Start blue pair")
def test_bluetooth_pair_time():
    check_bluetooth_pair()
    adb.reboot()
    time.sleep(120)
    ble.remote_home.write(b'\xA0\x01\x01\xA2')
    time.sleep(5)
    adb.back()
    time.sleep(3)
    ble.remote_home.write(b'\xA0\x01\x00\xA1')


def check_dut_start_up(ui_info):
    start_time = time.time()
    while time.time() - start_time <= 120:
        output = adb.run_shell_cmd("dumpsys |grep -i currentfocus")[1]
        if ui_info in output:
            time.sleep(5)  # wait startup process servers start done
            break
        else:
            continue




