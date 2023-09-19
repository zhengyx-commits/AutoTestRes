import pytest
import logging
from lib.common.tools.Subtitle import Subtitle
from . import *

subtitle = Subtitle()

p_conf_local_playback = config_yaml.get_note('conf_local_playback')
p_conf_subtitle = p_conf_local_playback['subtitle_path']


# @pytest.mark.skip
class TestSubtitleCheck:
    teletext_path = p_conf_subtitle['Teletext']['path']
    video, play_command = play_cmd(teletext_path)
    # localplayer = LocalPlayer(uuid=p_conf_uuid, path=path, playFromList=True)
    # video = localPlayer.run_shell_cmd("ls /storage/" + p_conf_uuid + path)[1]
    # play_cmd = 'am start -n ' + localPlayer.LOCALPLAYER_PACKAGE_TUPLE[0] + '/' + \
    #            localPlayer.LOCALPLAYER_PACKAGE_TUPLE[1] + ' -d file:/storage/' + p_conf_uuid + path + video

    subtitle.pull("/storage/" + p_conf_uuid + teletext_path + video, subtitle.logdir)

    @pytest.fixture(scope='function', autouse=True)
    def subtitle_setup_teardown(self):
        set_iptv_path()
        assert p_conf_uuid in localPlayer.getUUIDs()
        subtitle.error = 0
        subtitle.got_spu = ''
        subtitle.show_spu = ''
        subtitle.subtitle_window = ''
        subtitle.clear_logcat()
        subtitle.app_stop(app_name)
        yield
        subtitle.app_stop(app_name)

    def test_TeletextSubtitleCheck(self):
        subtitle.run_shell_cmd(self.play_command)
        # if subtitle.find_element("Resume this video from last position?", "text"):
        #     subtitle.keyevent('KEYCODE_DPAD_RIGHT')
        #     subtitle.enter()
        time.sleep(15)
        subtitle.clear_logcat()
        subtitle.start_subtitle_datathread(subtitleType='Teletext', apk_name="videoplayer")
        assert subtitle.subtitleThread.is_alive()
        video_totalTime = subtitle.seek_time(self.video)
        if video_totalTime > 30000:
            time.sleep(30)
        elif video_totalTime > 10000:
            time.sleep(10)
        else:
            logging.info('please change video')
        subtitle.teletext_check()
        time.sleep(5)
        # subtitle.stop_subtitle_data_thread()
        assert (subtitle.error == 0) & (subtitle.got_spu != '') & (subtitle.show_spu != '') & (
                subtitle.subtitle_window != ''), \
            'There are some problems with the subtitle shows'
