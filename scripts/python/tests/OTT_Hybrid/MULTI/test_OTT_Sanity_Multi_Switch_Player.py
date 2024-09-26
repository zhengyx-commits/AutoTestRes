import logging
import time
from lib.common.playback.Youtube import YoutubeFunc
from lib.common.playback.Netflix import Netflix
from lib.common.system.ADB import ADB
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

# g_conf_device_id = pytest.config['device_id']
p_conf_multi_player = config_yaml.get_note('conf_multi_player')
p_conf_repeat_count = p_conf_multi_player['repeat_count']
# multi = MultiPlayer(g_conf_device_id)
youtube = YoutubeFunc()
youtube.open_omx_info()
netflix = Netflix()
adb = ADB()
streamProvider = StreamProvider()
common_case = Common_Playcontrol_Case()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    common_case.set_wifi_enabled()  # Connect wifi of outside network before start netflix
    netflix.netflix_setup_with_files(target=pytest.target.get("prj"))
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    youtube.stop_youtube()
    streamProvider.stop_send()
    netflix.stop_netflix()
    common_case.forget_outside_wifi()
    youtube.close_omx_info()


# Switch From IPTV To Youtube,and then back to IPTV,and then Netflix,finally IPTV.
# @pytest.mark.repeat(p_conf_repeat_count)
@pytest.mark.flaky(reruns=3)
def test_Switch_Player():
    queue_flag = False
    stream_name_list, url = get_conf_url("conf_rtp_url", "rtp", "conf_stream_name", "h264_1080P")
    for stream_name in stream_name_list:
        file_path = streamProvider.get_file_path('h264_1080P', 'ts', stream_name)
        if file_path:
            file_path = file_path[0]
            try:
                streamProvider.start_send('rtp', file_path, url=url[-4:])
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if url:
                start_cmd = multi.get_start_cmd(url)
            else:
                start_cmd = multi.start_play_cmd(1, 'rtp')
            common_case.set_wifi_disabled()   # Forget wifi of outside network before start MultiMediaPlayer
            if queue_flag:
                while not pytest.device._adblogcat_reader._read_buffer.empty():
                    pytest.device._adblogcat_reader._read_buffer.get()
            multi.send_cmd(start_cmd)
            assert common_case.player_check.check_startPlay()[0], "start playback failed"
            for i in range(p_conf_repeat_count):
                time.sleep(5)
                common_case.set_wifi_enabled()  # Connect wifi of outside network before start youtube
                time.sleep(10)
                youtube.start_youtube()
                time.sleep(10)
                common_case.set_wifi_disabled()
                multi.run_shell_cmd(start_cmd)
                time.sleep(10)
                common_case.set_wifi_enabled()  # Connect wifi of outside network before start netflix
                netflix.start_play()
                time.sleep(10)
                common_case.set_wifi_disabled()
                multi.run_shell_cmd(start_cmd)
                time.sleep(10)
                multi.stop_multiPlayer_apk()
            streamProvider.stop_send()
            queue_flag = True
