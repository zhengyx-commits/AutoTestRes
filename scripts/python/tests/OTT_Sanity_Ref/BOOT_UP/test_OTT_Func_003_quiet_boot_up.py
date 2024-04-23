#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/20 下午3:44
# @Author  : yongbo.shao
# @File    : test_ott_quiet_boot_up.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import time
from tests.OTT_Sanity_Ref.BOOT_UP import *
from datetime import datetime
import os
import pytest
import subprocess
import allure

config_yaml = yamlTool(os.getcwd() + '/config/config.yaml')
p_conf_obs_websocket_ip = config_yaml.get_note('ip').get('device_ip')


adb = ADB()


@pytest.fixture(scope="module", autouse=True)
@allure.step("Check the network before and after boot up")
def setup_teardown():
    before_bootup = check_network()
    yield
    after_bootup = check_network()
    if before_bootup and after_bootup:
        assert True


# @pytest.mark.skip
@allure.step("Start boot up, confirm boot log will not display")
def test_003_quiet_boot_up():
    value = adb.getprop("ro.boot.quiescent")
    logging.info(f"ro.boot.quiescent property value is: {value}")
    if value == "1":
        adb.shell("svc power reboot quiescent")
        obs.start_recording()
        time.sleep(40)
        obs.stop_recording()
        adb.keyevent("KEYCODE_POWER")
    result = get_boot_logo(first_logo=True, second_logo=True)
    assert not result
    assert get_launcher()

