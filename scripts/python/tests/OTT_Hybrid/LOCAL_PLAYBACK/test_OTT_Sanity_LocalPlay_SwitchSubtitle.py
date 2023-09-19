import logging
import pytest
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv
from lib.common.system.ADB import ADB
import re
from . import *

adb = ADB()
playerCheck = PlayerCheck_Iptv()
video, play_command = play_cmd(p_conf_track_path['path'])


@pytest.fixture(scope='function', autouse=True)
def switch_subtitle_setup_teardown():
    set_iptv_path()
    localPlayer.app_stop(app_name)
    yield
    localPlayer.app_stop(app_name)


# @pytest.mark.skip
def test_switchSubtitle():
    subtitle_index = []
    rc, output = adb.run_terminal_cmd("ffprobe " + video, output_stderr=True)
    for line in output:
        linestr = line.decode('utf-8')
        if "Subtitle:" in linestr:
            subtitle_index.append(re.findall(r'Subtitle: (.\S*)', linestr))
            logging.info(subtitle_index)
            continue
    logging.info(len(subtitle_index))
    subtitle_index_num = int(len(subtitle_index))
    assert p_conf_uuid in localPlayer.getUUIDs()
    localPlayer.run_shell_cmd(play_command)
    time.sleep(50)
    if subtitle_index_num >= 2:
        for i in range(1, subtitle_index_num):
            num = str(i)
            switch_subtitleTrack_command = "am broadcast -a com.amlogic.vplayer.switchsubtitletrackkey --ei subtitle_index " + num
            logging.info({switch_subtitleTrack_command})
            playerCheck.run_shell_cmd(switch_subtitleTrack_command)
            assert playerCheck.check_switchSubtitleTrack()[0]
    else:
        assert False, 'subtitletrack not exist or just one subtitletrack'