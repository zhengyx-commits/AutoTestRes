import pytest
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from . import *

playerCheck = PlayerCheck()
video, play_command = play_cmd(p_conf_track_path['path'])
seek_command = "am broadcast -a com.amlogic.vplayer.seekkey --el seek_pos 30000"


@pytest.fixture(scope='function', autouse=True)
def seek_setup_teardown():
    set_iptv_path()
    localPlayer.app_stop(app_name)
    yield
    localPlayer.app_stop(app_name)


# @pytest.mark.skip
@pytest.mark.flaky(reruns=3)
def test_seek():
    assert p_conf_uuid in localPlayer.getUUIDs()
    localPlayer.run_shell_cmd(play_command)
    # find_resume_element()
    time.sleep(10)
    playerCheck.run_shell_cmd(seek_command)
    assert playerCheck.check_seek()[0]
