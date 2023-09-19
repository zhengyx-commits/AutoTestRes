import logging
import time
import os
import pytest
from lib.common.playback.LocalPlayer import LocalPlayer
from tools.yamlTool import yamlTool

localPlayer = LocalPlayer(play_from_list=True)
uuids = localPlayer.getUUIDs()
config_yaml = yamlTool(os.getcwd() + '/config/config_ott_hybrid.yaml')
p_conf_local_playback = config_yaml.get_note('conf_local_playback')
p_conf_sz_uuid = p_conf_local_playback['sz_uuid']
p_conf_sh_uuid = p_conf_local_playback['sh_uuid']
p_conf_track_path = p_conf_local_playback['track_path']
app_name = 'com.droidlogic.videoplayer'
if p_conf_sz_uuid in uuids:
    p_conf_uuid = p_conf_sz_uuid
else:
    p_conf_uuid = p_conf_sh_uuid


def play_cmd(path):
    video = localPlayer.run_shell_cmd("ls /storage/" + p_conf_uuid + path)[1]
    play_command = 'am start -n ' + localPlayer.LOCALPLAYER_PACKAGE_TUPLE[0] + '/' + \
                   localPlayer.LOCALPLAYER_PACKAGE_TUPLE[
                       1] + ' -d file:/storage/' + p_conf_uuid + path + video
    return video, play_command


# def find_resume_element():
#     if localPlayer.find_element("Resume this video from last position?", "text"):
#         localPlayer.keyevent('KEYCODE_DPAD_RIGHT')
#         localPlayer.enter()


def set_iptv_path():
    #if localPlayer.LOCALPLAYER_PACKAGE_TUPLE[0] not in localPlayer.checkoutput('pm list packages'):
    #    assert localPlayer.install_apk('apk/VideoPlayer2.apk')
    localPlayer.install_apk('apk/VideoPlayer.apk')
    time.sleep(5)
    localPlayer.root()
    localPlayer.run_shell_cmd("setenforce 0")
    #if not localPlayer.check_player_path():
        #logging.info("Not IPTV path!!!")
    localPlayer.run_shell_cmd("setprop vendor.media.ammediaplayer.enable 1;setprop iptv.streamtype 1")
