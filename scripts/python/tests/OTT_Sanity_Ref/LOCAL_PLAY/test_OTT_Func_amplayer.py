import logging
import time

import allure
import pytest

from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv
from tests.OTT_Sanity_Ref.LOCAL_PLAY import *

playerCheck = PlayerCheck_Iptv()


@pytest.fixture(scope='function', autouse=True)
def start_play_setup_teardown():
    if android_version == "34":
        localPlayer.run_shell_cmd("setprop debug.stagefright.c2-debug 3")
    localPlayer.run_shell_cmd(f'pm clear {amplayer_package}')
    localPlayer.run_shell_cmd(f"am start -n {amplayer_activity}")
    time.sleep(2)
    start_time = time.time()
    while time.time() - start_time < 60:
        current_window = localPlayer.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
        if "android.permissioncontroller" in current_window:
            localPlayer.find_and_tap("Allow", "text")  # get permission
            localPlayer.app_stop(amplayer_package)
            time.sleep(1)
        else:
            logging.info("permission OK")
            break
    yield
    localPlayer.app_stop(amplayer_package)
    if android_version == "34":
        localPlayer.run_shell_cmd("setprop debug.stagefright.c2-debug 0")


# @pytest.mark.flaky(reruns=3)
@pytest.mark.parametrize("video_name,video_format", get_video_list())
def test_amplayer_play(video_name, video_format):
    allure.dynamic.title(f"Test video format {video_format.upper()}")
    play_cmd = create_play_video_cmd(uuid, video_name)
    print(play_cmd)
    with allure.step(f"Start play {video_name}"):
        localPlayer.run_shell_cmd(play_cmd)
    with allure.step(f"Check play status"):
        assert playerCheck.run_check_main_thread(30), "start play failed"
