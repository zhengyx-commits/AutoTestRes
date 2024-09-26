import logging
import pytest
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv
from lib.common.system.ADB import ADB
import re
from . import *

playerCheck = PlayerCheck_Iptv()
adb = ADB()
video, play_command = play_cmd(p_conf_track_path['path'])


@pytest.fixture(scope='function', autouse=True)
def switch_audio_track_setup_teardown():
    set_iptv_path()
    localPlayer.app_stop(app_name)
    yield
    localPlayer.app_stop(app_name)


# @pytest.mark.skip
def test_audioTrack():
    audio_track_num = 2
    assert p_conf_uuid in localPlayer.getUUIDs()
    logging.info(play_command)
    localPlayer.run_shell_cmd(play_command)
    localPlayer.run_shell_cmd("logcat -c")
    logging.info(f"audio_track_num: {audio_track_num}")
    time.sleep(10)
    if int(audio_track_num) >= 2:
        for i in range(1, int(audio_track_num)):
            num = str(i)
            switch_audioTrack_command = "am broadcast -a com.amlogic.vplayer.switchaudiotrackkey --ei audio_index " + num
            logging.info({switch_audioTrack_command})
            playerCheck.run_shell_cmd(switch_audioTrack_command)
            assert playerCheck.check_switchAudioTrack()[0]
    else:
        assert False, 'audiotrack not exist or just one audiotrack'