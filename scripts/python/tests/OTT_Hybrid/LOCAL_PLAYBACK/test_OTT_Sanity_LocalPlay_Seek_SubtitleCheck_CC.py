import pytest
import time
from lib.common.tools.Subtitle import Subtitle
from . import *

subtitle = Subtitle()

p_conf_subtitle = p_conf_local_playback['subtitle_path']
p_seek_repeat_time = p_conf_local_playback['seek_path']['repeat_time']

# @pytest.mark.skip
class TestSubtitleCheck:
    cc_path = p_conf_subtitle['CC']['path']
    video, play_command = play_cmd(cc_path)
    # video = localPlayer.run_shell_cmd("ls /storage/" + p_conf_uuid + cc_path)[1]
    # play_cmd = 'am start -n ' + localPlayer.LOCALPLAYER_PACKAGE_TUPLE[0] + '/' + \
    #            localPlayer.LOCALPLAYER_PACKAGE_TUPLE[1] + ' -d file:/storage/' + p_conf_uuid + cc_path + video

    subtitle.pull("/storage/" + p_conf_uuid + cc_path + video, subtitle.logdir)

    @pytest.fixture(scope='function', autouse=True)
    def subtitle_setup_teardown(self):
        assert p_conf_uuid in localPlayer.getUUIDs()
        subtitle.error = 0
        subtitle.got_spu = ''
        subtitle.show_spu = ''
        subtitle.subtitle_window = ''
        subtitle.clear_logcat()
        subtitle.app_stop(app_name)
        yield
        subtitle.app_stop(app_name)

    def test_CCSubtitleCheck(self):
        subtitle.run_shell_cmd(self.play_command)
        if subtitle.find_element("Resume this video from last position?", "text"):
            subtitle.keyevent('KEYCODE_DPAD_RIGHT')
            subtitle.enter()
        time.sleep(10)
        video_totalTime = subtitle.seek_time(self.video)
        subtitle.seek_random('CC', video_totalTime, p_seek_repeat_time)
        assert (subtitle.error == 0) & (subtitle.got_spu != '') & (subtitle.show_spu != '') & (
                subtitle.subtitle_window != ''), \
            'There are some problems with the subtitle shows'
