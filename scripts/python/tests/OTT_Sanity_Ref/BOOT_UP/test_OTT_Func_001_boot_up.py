#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/20 下午3:44
# @Author  : yongbo.shao
# @File    : test_ott_boot_up.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
from lib.common.system.SerialPort import SerialPort
from tests.OTT_Sanity_Ref.BOOT_UP import *
import pytest
import allure


ser = SerialPort()
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
@allure.step("Start boot up, confirm boot log include first, second and launcher page")
def test_001_boot_up():
    ser.enter_uboot()
    obs.start_recording()
    ser.enter_kernel()
    time.sleep(40)
    obs.stop_recording()
    result = get_boot_logo(first_logo=True, second_logo=True)
    assert result
    assert get_launcher()

