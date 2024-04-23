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
from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv

devices = get_device()
playerCheck = PlayerCheck_Iptv()
localPlayer = LocalPlayer(play_from_list=True)
amplayer_activity = f"{localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[0]}/{localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[1]}"
# video, play_command = amplayer_play_cmd(p_conf_amplayer_path['4KH264_path'])
amplayer_app_name = f'{localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[0]}'
p_conf_local_playback = config_ott_sanity_yaml.get_note('conf_local_playback')
if is_sz_server():
    p_conf_uuid = p_conf_local_playback['sz_uuid']
else:
    p_conf_uuid = p_conf_local_playback['sh_amplayer_uuid']


def create_play_video_cmd(uuid, video):
    play_cmd = f"am start -n {amplayer_activity} -d file:/storage/{uuid}/video/{video}"
    return play_cmd


play_command = create_play_video_cmd(p_conf_uuid, 'H264_Butterfly_4k_High@L5.1_AAC_30M_30fps_3min.ts')


@pytest.fixture(scope='function', autouse=True)
@allure.step("multi_teardown")
def multi_teardown():
    adb.disable_cec()
    display_mode_before = get_display_mode()
    assert get_launcher()
    assert check_network()

    if android_version == "34":
        playerCheck.run_shell_cmd("setprop debug.stagefright.c2-debug 3")

    # clean cache,don't resume
    playerCheck.run_shell_cmd(f'pm clear {amplayer_app_name}')
    playerCheck.run_shell_cmd(
        f"am start -n {amplayer_activity}")
    time.sleep(2)
    start_time = time.time()
    while time.time() - start_time < 60:
        current_window = playerCheck.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
        if "com.google.android.permissioncontroller" in current_window:
            playerCheck.find_and_tap("Allow", "text")  # get permission
            playerCheck.app_stop(amplayer_app_name)
            time.sleep(1)
        else:
            logging.info("permission OK")
            break

    yield
    stop_app()
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


def stop_app():
    playerCheck.app_stop(amplayer_app_name)
    if android_version == "34":
        playerCheck.run_shell_cmd("setprop debug.stagefright.c2-debug 0")


@allure.step("Start suspend at exoplayer and wakeup, check wifi connect time")
def test_008_localplay_suspend_and_check_wifi():
    off_ethernet()
    assert connect_network()
    time.sleep(5)
    assert check_network()
    assert p_conf_uuid in playerCheck.getUUIDs()
    print(play_command)
    playerCheck.run_shell_cmd(play_command)
    assert playerCheck.run_check_main_thread(30), "start play failed"

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
    assert check_network_connect_time(page="exo_local")
    time.sleep(5)
    obs.stop_recording()
    stop_app()
    assert get_launcher()


# @pytest.mark.skip
@allure.step("Start suspend at exoplayer and wakeup, check ethernet connect time")
def test_008_localplay_suspend_and_check_ethernet():
    adb.forget_wifi()
    time.sleep(3)
    restore_ethernet()
    time.sleep(2)

    assert p_conf_uuid in playerCheck.getUUIDs()
    print(play_command)
    playerCheck.run_shell_cmd(play_command)
    assert playerCheck.run_check_main_thread(30), "start play failed"

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
    assert check_network_connect_time(network="ethernet", page="exo_local")
    time.sleep(5)
    obs.stop_recording()
    stop_app()
    assert get_launcher()

