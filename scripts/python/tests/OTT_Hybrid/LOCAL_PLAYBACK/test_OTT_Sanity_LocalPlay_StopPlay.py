import pytest
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from . import *

playerCheck = PlayerCheck()
video, play_command = play_cmd(p_conf_track_path['path'])
stop_command = "am broadcast -a com.amlogic.vplayer.stopkey"


@pytest.fixture(scope='function', autouse=True)
def start_pause_setup_teardown():
    set_iptv_path()
    localPlayer.app_stop(app_name)
    yield
    localPlayer.app_stop(app_name)


# @pytest.mark.skip
@pytest.mark.flaky(reruns=3)
def test_stop():
    assert p_conf_uuid in localPlayer.getUUIDs()
    localPlayer.run_shell_cmd(play_command)
    # find_resume_element()
    time.sleep(12)
    playerCheck.run_shell_cmd(stop_command)
    assert playerCheck.check_stopPlay()[0]
