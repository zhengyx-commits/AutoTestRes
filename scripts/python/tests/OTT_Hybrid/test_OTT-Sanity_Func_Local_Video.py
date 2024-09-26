import pytest
import time
from lib.common.playback.LocalPlayer import LocalPlayer
from lib.common.tools.LoggingTxt import log
from lib.common.system.ADB import ADB
from tests.OTT_Hybrid import config_yaml

adb = ADB()

# Todo: should debug again 20220324
p_conf_local_playback = config_yaml.get_note('conf_local_playback')
p_conf_uuid = p_conf_local_playback['uuid']
p_conf_video_path = p_conf_local_playback['video_path']
p_conf_seek_path = p_conf_local_playback['seek_path']


class TestLocalVideo:
    # @pytest.mark.skip
    def test_local_video(self):
        for video in p_conf_video_path.values():
            localplayer = LocalPlayer(uuid=p_conf_uuid, path=video["path"], playFromList=True)
            localplayer.install_apk('apk/VideoPlayer2.apk')
            time.sleep(5)
            adb.root()
            adb.run_shell_cmd("setenforce 0")
            if p_conf_uuid in localplayer.getUUIDs():
                assert True
            else:
                assert False
            localplayer.setup(videoplayerMonitorEnable=True, randomSeekEnable=False)
            localplayer.permissioncheck()
            assert True if localplayer.startPlay() else False
            assert log.check_result_error() == "Pass"

    @pytest.mark.skip
    def test_local_video_seek(self):
        from tests.common.playback.test_local_video_play import LocalVideo
        local_video = LocalVideo(videoplayerMonitorEnable=True, randomSeekEnable=True)
        local_video.test_local_video(uuid=p_conf_uuid, videos=p_conf_seek_path, sourceType='ottpath')