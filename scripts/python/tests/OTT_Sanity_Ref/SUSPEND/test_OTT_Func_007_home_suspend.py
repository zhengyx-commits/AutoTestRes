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


@allure.step("multi_teardown")
@pytest.fixture(scope="function", autouse=True)
def multi_teardown_module():
    connect_network()
    adb.disable_cec()
    adb.home()
    display_mode_before = get_display_mode()
    assert get_launcher()
    assert check_network(), "network disconnect before test"
    yield
    adb.home()
    assert connect_network()
    display_mode_after = get_display_mode()
    assert display_mode_after == display_mode_before
    assert check_network(), "network disconnect after test"


@allure.step("Start suspend at home page and wakeup, check wifi connect time")
def test_007_home_suspend_and_check_wifi():
    obs.start_recording()
    time.sleep(2)
    logging.info("start suspend")
    adb.keyevent("KEYCODE_POWER")
    time.sleep(2)
    obs.stop_recording()
    assert check_suspend(suspend=True)

    obs.start_recording()
    logging.info("start wakeup")
    adb.keyevent("KEYCODE_POWER")
    time.sleep(5)
    obs.stop_recording()
    assert check_network_connect_time()
    assert get_launcher()


@allure.step("Start suspend at home page and wakeup, check ethernet connect time")
def test_007_home_suspend_and_check_ethernet():
    adb.forget_wifi()
    adb.set_wifi_disabled()
    time.sleep(2)
    obs.start_recording()
    time.sleep(2)
    logging.info("start suspend")
    adb.keyevent("KEYCODE_POWER")
    time.sleep(2)
    obs.stop_recording()
    assert check_suspend(suspend=True)

    obs.start_recording()
    logging.info("start wakeup")
    adb.keyevent("KEYCODE_POWER")
    time.sleep(5)
    obs.stop_recording()
    assert check_network_connect_time(network="ethernet")
    assert get_launcher()

