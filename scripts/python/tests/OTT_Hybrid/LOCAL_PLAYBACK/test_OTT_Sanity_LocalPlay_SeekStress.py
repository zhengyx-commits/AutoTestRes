import logging
import pytest
import random
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv
from . import *

playerCheck = PlayerCheck_Iptv()
p_conf_videoplayer = config_yaml.get_note('conf_videoplayer')
video, play_command = play_cmd(p_conf_track_path['path'])
seek_command = "am broadcast -a com.amlogic.vplayer.seekkey --el seek_pos 30000"
# seekoffset_command = "am broadcast -a com.amlogic.vplayer.seekoffsetkey --el seek_offset 15000"


@pytest.fixture(scope='function', autouse=True)
def seek_setup_teardown():
    set_iptv_path()
    localPlayer.app_stop(app_name)
    yield
    localPlayer.app_stop(app_name)


# @pytest.mark.skip
def test_seek_stress(seek_play_time=30):
    assert p_conf_uuid in localPlayer.getUUIDs()
    localPlayer.run_shell_cmd(play_command)
    # find_resume_element()
    time.sleep(10)
    play_time = seek_play_time
    checked_log_play_duration = localPlayer.run_shell_cmd('logcat -s amlsource -e duration: -m 1 | grep "duration:"')[1]
    play_duration = (checked_log_play_duration[-3:-1])
    p_start_time = time.time()
    seek_duration = p_conf_videoplayer['seek_duration']
    while time.time() - p_start_time <= seek_duration*3600:
        seek_time = p_conf_videoplayer['seek_checktime']
        if seek_time is None:
            logging.info("random seek")
            play_duration = int(play_duration)
            seek_time = random.randint(0, play_duration - play_time)
        else:
            seek_time = int(seek_time)
            logging.info(f"seek time: {seek_time}")
        video_cmd = "am broadcast -a com.amlogic.vplayer.seekkey --el seek_pos " + f'{seek_time}'
        playerCheck.run_shell_cmd(video_cmd)
        assert playerCheck.check_seek()[0]
