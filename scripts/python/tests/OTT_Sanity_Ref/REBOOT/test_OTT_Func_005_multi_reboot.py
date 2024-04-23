#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/20 下午3:44
# @Author  : yongbo.shao
# @File    : test_ott_multi_reboot.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
from tests.OTT_Sanity_Ref.REBOOT import *
import pytest
import allure

p_conf_reboot_count = config_ott_sanity_yaml.get_note("conf_reboot").get("reboot_count")


adb = ADB()


@pytest.fixture(scope="function", autouse=True)
def setup_teardown():
    before_bootup = check_network()
    display_mode_before = get_display_mode()
    yield
    after_bootup = check_network()
    if before_bootup and after_bootup:
        assert True
    display_mode_after = get_display_mode()
    assert display_mode_after == display_mode_before


# @pytest.mark.skip
@pytest.mark.repeat(p_conf_reboot_count)
@allure.step("Start multi reboot, confirm boot log will display")
def test_005_multi_reboot():
    adb.reboot()
    obs.start_recording()
    time.sleep(40)
    obs.stop_recording()
    result = get_boot_logo(first_logo=True, second_logo=True)
    assert result
    assert get_launcher()


def check_network():
    result = adb.ping()
    logging.info(f"result: {result}")
    return result


