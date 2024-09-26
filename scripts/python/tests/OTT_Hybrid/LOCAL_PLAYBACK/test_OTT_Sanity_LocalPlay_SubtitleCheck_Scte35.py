import pytest
import logging
from lib.common.tools.Subtitle import Subtitle
from . import *

subtitle = Subtitle()

p_conf_local_playback = config_yaml.get_note('conf_local_playback')
p_conf_subtitle = p_conf_local_playback['subtitle_path']


# @pytest.mark.skip
class TestSubtitleCheck:
    scte35_path = p_conf_subtitle['Scte35']['path']
    video, play_command = play_cmd(scte35_path)
    # localplayer = LocalPlayer(uuid=p_conf_uuid, path=path, playFromList=True)
    # video = localPlayer.run_shell_cmd("ls /storage/" + p_conf_uuid + path)[1]
    # play_cmd = 'am start -n ' + localPlayer.LOCALPLAYER_PACKAGE_TUPLE[0] + '/' + \
    #            localPlayer.LOCALPLAYER_PACKAGE_TUPLE[1] + ' -d file:/storage/' + p_conf_uuid + path + video

    subtitle.pull("/storage/" + p_conf_uuid + scte35_path + video, subtitle.logdir)

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

    def test_Scte35InfoCheck(self):
        subtitle.run_shell_cmd(self.play_command)
        # find_resume_element()
        time.sleep(2)
        from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
        playerCheck = PlayerCheck_Base()
        logging.info('checking，please wait about 420s')
        seek_command = "am broadcast -a com.amlogic.vplayer.seekkey --el seek_pos 300000"
        subtitle.run_shell_cmd(seek_command)
        playerCheck.start_check_keywords_thread(subtitle.CMD_SCTE35, subtitle.scte35Parser_keywords, 420)
        assert playerCheck.flag & (playerCheck.checked_log_dict != {}), 'No scte35 parser info in logcat, ' \
                                                                        'Please check '
