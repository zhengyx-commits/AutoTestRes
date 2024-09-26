import logging
import pytest
import time
from lib.common.tools.ProbeInfo import ProbeInfo
from . import p_conf_local_playback, p_conf_uuid, app_name, localPlayer, set_iptv_path

info = ProbeInfo()

p_conf_probeInfo = p_conf_local_playback['probe_path']
p_conf_probe_infoPath = p_conf_probeInfo['Probe']['path']
logging.info(f'localplay ProbeInfo video path:{p_conf_probe_infoPath}')
# info.path = p_conf_probeInfo["path"]
video = info.run_shell_cmd("ls /storage/" + p_conf_uuid + p_conf_probe_infoPath)[1]
play_command = 'am start -n com.droidlogic.videoplayer/.VideoPlayer -d file:/storage/' + p_conf_uuid + p_conf_probe_infoPath + video


@pytest.fixture(scope='function', autouse=True)
def probe_setup_teardown():
    set_iptv_path()
    info.clear_logcat()
    info.pull("/storage/" + p_conf_uuid + p_conf_probe_infoPath + video, info.logdir)
    info.root()
    info.run_shell_cmd("setprop vendor.media.audio.info.report.debug 0x1000")
    info.run_shell_cmd("chmod 664 /sys/class/amaudio/codec_report_info")
    info.app_stop(app_name)
    yield
    info.app_stop(app_name)


# @pytest.mark.skip
def test_probeinfo():
    # info.start_logcat_thread()
    info.run_shell_cmd(play_command)
    info.start_logcat_thread()
    time.sleep(30)
    # info.stop_logcat_thread()
    info.get_video_info(video_file=video)
    time.sleep(3)
    info.check_probe_info()
    info.check_probe_decodedata(status='video_play')
    assert info.error_count == 0

    # Todo add more video status
