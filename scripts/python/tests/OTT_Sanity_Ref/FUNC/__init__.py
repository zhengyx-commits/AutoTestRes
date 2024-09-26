import logging
import time
import pytest

from lib.common.playback.LocalPlayer import LocalPlayer
from .. import *
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from lib.common.tools.pass_oobe import *
from lib import get_device

localPlayer = LocalPlayer(play_from_list=True)
config_yaml_local = yamlTool(os.getcwd() + '/config/config_ott_hybrid.yaml')
p_conf_local_playback = config_yaml_local.get_note('conf_local_playback')
p_conf_amplayer_path = p_conf_local_playback['amplayer_path']
if is_sz_server():
    p_conf_uuid = p_conf_local_playback['sz_uuid']
else:
    p_conf_uuid = p_conf_local_playback['sh_amplayer_uuid']

amplayer_app_name = 'com.droidlogic.exoplayer2.demo'
serialnumbers = get_device()
u2 = UiautomatorTool(serialnumbers)
adb = ADB()
player_check = PlayerCheck_Base()
android_version = adb.getprop("ro.build.version.sdk")

def amplayer_play_cmd(path):
    video = localPlayer.run_shell_cmd("ls /storage/" + p_conf_uuid + path)[1]
    play_command = 'am start -n ' + localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[0] + '/' + \
                   localPlayer.LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE[
                       1] + ' -d file:/storage/' + p_conf_uuid + path + video
    return video, play_command


if 'ott_sanity' == pytest.target.get("prj") or 'ott_hybrid_u_sanity' == pytest.target.get("prj"):
    adb.shell('\"echo 2 > /sys/class/remote/amremote/protocol\"')
    # adb.home()
    # adb.run_shell_cmd(f"am start -an {HOME_ACTIVITY}")
    time.sleep(1)
    adb.home()
    adb.home()
    current_window = adb.run_shell_cmd(CURRENT_FOCUS)[1]
    if HOME_ACTIVITY not in current_window:
        # adb.reboot()
        # time.sleep(60)
        # adb.wait_devices()
        adb.root()
        network_interface = player_check.create_network_auxiliary()
        player_check.offline_network(network_interface)
        time.sleep(5)
        logging.info('start to oobe')
        adb.keyevent(4)
        adb.shell(f"cmd wifi connect-network {p_conf_account_setting_WIFI_SSID} wpa2 {p_conf_account_setting_WIFI_PWD}")
        time.sleep(10)
        # ott_oobe()
        pass_oobe()
        adb.shell("settings put global stay_on_while_plugged_in 1")
        player_check.restore_network(network_interface)
    else:
        logging.info('oobe is complete')
        time.sleep(2)

def reboot_and_retore():
    adb.reboot()
    start_time = time.time()
    while time.time() - start_time < 60:
        reboot_check = adb.run_shell_cmd("getprop sys.boot_completed")[1]
        if reboot_check == "1":
            logging.info("booted up")
            break
        else:
            time.sleep(5)
    reboot_check = adb.run_shell_cmd("getprop sys.boot_completed")[1]
    if reboot_check != "1":
        raise Exception('boot up run time error')
    else:
        pass
    time.sleep(20)
    adb.root()