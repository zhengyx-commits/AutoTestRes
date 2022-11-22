import pytest
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from . import *

playerCheck = PlayerCheck()
video, play_command = play_cmd(p_conf_track_path['path'])
start_command = "am broadcast -a com.amlogic.vplayer.startkey"
pause_command = "am broadcast -a com.amlogic.vplayer.pausekey"


@pytest.fixture(scope='function', autouse=True)
def start_pause_setup_teardown():
    set_iptv_path()
    localPlayer.app_stop(app_name)
    yield
    localPlayer.app_stop(app_name)


# @pytest.mark.skip
@pytest.mark.flaky(reruns=3)
def test_start_pause_resume():
    assert p_conf_uuid in localPlayer.getUUIDs()
    localPlayer.run_shell_cmd(play_command)
    # find_resume_element()
    time.sleep(12)
    playerCheck.run_shell_cmd(pause_command)
    assert playerCheck.check_pause()[0], "playback pause failed"
    playerCheck.run_shell_cmd(start_command)
    assert playerCheck.check_resume()[0], "playback resume failed"
