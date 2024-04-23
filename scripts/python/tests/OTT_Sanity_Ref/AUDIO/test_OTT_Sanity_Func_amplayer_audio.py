import logging
import time

import allure
import pytest

from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv
from tests.OTT_Sanity_Ref.AUDIO import *

playerCheck = PlayerCheck_Iptv()
uuid = get_uuid()


@pytest.fixture(scope='function', autouse=True)
def start_play_setup_teardown():
    if android_version == "34":
        adb.run_shell_cmd("setprop debug.stagefright.c2-debug 3")
    adb.run_shell_cmd(f'pm clear {amplayer_package}')
    adb.run_shell_cmd(f"am start -n {amplayer_activity}")
    time.sleep(2)
    start_time = time.time()
    while time.time() - start_time < 60:
        current_window = adb.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
        if "android.permissioncontroller" in current_window:
            adb.find_and_tap("Allow", "text")  # get permission
            adb.app_stop(amplayer_package)
            time.sleep(1)
        else:
            logging.info("permission OK")
            break
    yield
    adb.app_stop(amplayer_package)
    if android_version == "34":
        adb.run_shell_cmd("setprop debug.stagefright.c2-debug 0")


# @pytest.mark.flaky(reruns=3)
@pytest.mark.parametrize("audio_name,audio_format", get_audio_list())
def test_amplayer_audio_play(audio_name, audio_format):
    allure.dynamic.title(f"Test video format {audio_format.upper()}")
    play_cmd = create_play_audio_cmd(uuid, audio_name)
    print(play_cmd)
    with allure.step(f"Start play {audio_name}"):
        adb.run_shell_cmd(play_cmd)
    with allure.step(f"Check play status"):
        assert playerCheck.run_check_main_thread(10), "start play failed"
