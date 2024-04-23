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
from lib.common.playback.Youtube import Youtube

devices = get_device()
youtube = Youtube()


@pytest.fixture(scope='function', autouse=True)
@allure.step("multi_teardown")
def multi_teardown():
    adb.disable_cec()
    display_mode_before = get_display_mode()
    assert get_launcher()
    assert check_network()

    youtube.checkoutput(f'monkey -p {youtube.GOOGLE_YOUTUBE_PACKAGENAME} 1')
    time.sleep(20)

    # judge whether apk start is not
    start_time = time.time()
    current_window = youtube.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
    if 'com.google.android.apps.youtube.tv.activity.MainActivity' not in current_window:
        while time.time() - start_time < 60:
            youtube.run_shell_cmd('input keyevent 3')
            time.sleep(5)
            youtube.checkoutput(f'monkey -p {youtube.GOOGLE_YOUTUBE_PACKAGENAME} 1')
            time.sleep(10)
            current_window = youtube.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
            if 'com.google.android.apps.youtube.tv.activity.MainActivity' not in current_window:
                logging.debug("continue")
            else:
                break
    else:
        logging.debug("APK OK")
    if 'com.google.android.apps.youtube.tv.activity.MainActivity' not in current_window:
        raise ValueError("apk hasn't exited yet")
    else:
        logging.debug("APK OK")

    yield
    obs.stop_recording()
    youtube.stop_youtube()
    off_ethernet()
    assert connect_network()
    assert check_network()
    display_mode_after = get_display_mode()
    assert display_mode_after == display_mode_before


def off_ethernet():
    network_interface = adb.create_network_auxiliary()
    adb.offline_network(network_interface)


def restore_ethernet():
    network_interface = adb.create_network_auxiliary()
    adb.restore_network(network_interface)


@allure.step("Start suspend at youtube and wakeup, check wifi connect time")
def test_009_youtube_suspend_and_check_wifi():
    off_ethernet()
    assert connect_network()
    time.sleep(5)
    youtube.youtube_playback("AV1")

    obs.start_recording()
    time.sleep(2)
    logging.info("start suspend")
    adb.keyevent("KEYCODE_POWER")
    time.sleep(5)
    obs.stop_recording()
    assert check_suspend(suspend=True)

    obs.start_recording()
    logging.info("start wakeup")
    adb.keyevent("KEYCODE_POWER")
    assert check_network_connect_time(page="youtube")
    time.sleep(5)
    obs.stop_recording()
    youtube.stop_youtube()
    assert get_launcher()


# @pytest.mark.skip
@allure.step("Start suspend at youtube and wakeup, check ethernet connect time")
def test_009_youtube_suspend_and_check_ethernet():
    adb.forget_wifi()
    time.sleep(3)
    restore_ethernet()
    time.sleep(2)
    youtube.youtube_playback("AV1")

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
    assert check_network_connect_time(network="ethernet", page="youtube")
    time.sleep(5)
    obs.stop_recording()
    youtube.stop_youtube()
    assert get_launcher()

