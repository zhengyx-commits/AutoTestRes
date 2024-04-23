#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/25 上午10:53
# @Author  : yongbo.shao
# @File    : test_suspend_to_wakeup.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import time
import allure
from tests.OTT_Sanity_Ref.SUSPEND import *

devices = get_device()


@pytest.fixture(scope='module', autouse=True)
@allure.step("multi_teardown")
def multi_teardown():
    assert get_launcher()
    yield


@allure.step("Start suspend at home page and wakeup, check wifi connect time")
@pytest.mark.parametrize("value", [5, 10, 60, 120, 300])
def test_010_suspend_random_seconds_and_check_wifi(value):
    obs.start_recording()
    time.sleep(2)
    logging.info("start suspend")
    adb.keyevent("KEYCODE_POWER")
    time.sleep(2)
    obs.stop_recording()
    assert check_suspend(suspend=True)
    time.sleep(value)
    obs.start_recording()
    logging.info("start wakeup")
    adb.keyevent("KEYCODE_POWER")
    time.sleep(5)
    obs.stop_recording()
    assert check_network_connect_time()
    assert get_launcher()


