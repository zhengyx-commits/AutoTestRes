import pytest

from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv
from . import *

playerCheck = PlayerCheck_Iptv()
video, play_command = amplayer_play_cmd(p_conf_amplayer_path['OGM_path'])


@pytest.fixture(scope='function', autouse=True)
def start_play_setup_teardown():
    if android_version == "34":
        localPlayer.run_shell_cmd("setprop debug.stagefright.c2-debug 3")

    # clean cache,don't resume
    localPlayer.run_shell_cmd(f'pm clear {amplayer_app_name}')
    localPlayer.run_shell_cmd(
        f"am start -n {localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[0]}/{localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[1]}")
    time.sleep(2)
    start_time = time.time()
    while time.time() - start_time < 60:
        current_window = localPlayer.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
        if "com.google.android.permissioncontroller" in current_window:
            localPlayer.find_and_tap("Allow", "text")  # get permission
            localPlayer.app_stop(amplayer_app_name)
            time.sleep(1)
        else:
            logging.info("permission OK")
            break
    yield
    localPlayer.app_stop(amplayer_app_name)
    if android_version == "34":
        localPlayer.run_shell_cmd("setprop debug.stagefright.c2-debug 0")


@pytest.mark.flaky(reruns=3)
def test_amplayer_play_ogm():
    assert p_conf_uuid in localPlayer.getUUIDs()
    print(play_command)
    localPlayer.run_shell_cmd(play_command)
    assert playerCheck.run_check_main_thread(30), "start play failed"
