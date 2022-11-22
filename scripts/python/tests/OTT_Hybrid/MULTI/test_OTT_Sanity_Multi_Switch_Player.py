import logging
import time
from lib.common.playback.Youtube import YoutubeFunc
from lib.common.playback.Netflix import Netflix
from lib.common.system.ADB import ADB
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

g_conf_device_id = pytest.config['device_id']
p_conf_multi_player = config_yaml.get_note('conf_multi_player')
p_conf_repeat_count = p_conf_multi_player['repeat_count']
multi = MultiPlayer(g_conf_device_id)
youtube = YoutubeFunc()
netflix = Netflix()
playerCheck = PlayerCheck()
adb = ADB()
streamProvider = StreamProvider()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    netflix.netflix_setup()
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    youtube.stop_youtube()
    streamProvider.stop_send()
    netflix.stop_netflix()


# Switch From IPTV To Youtube,and then back to IPTV,and then Netflix,finally IPTV.
# @pytest.mark.repeat(p_conf_repeat_count)
def test_Switch_Player():
    stream_name_list, url = get_conf_url("conf_rtp_url", "rtp", "conf_stream_name", "h264_1080P")
    for stream_name in stream_name_list:
        file_path = streamProvider.get_file_path('h264_1080P', 'ts', stream_name)
        if file_path:
            file_path = file_path[0]
        # if not streamProvider.get_file_path('ts', stream_name):
        #     logging.error("stream provider file path doesn't exist.")
        #     return
        # else:
        #     file_path = streamProvider.get_file_path('ts', stream_name)[0]
            try:
                streamProvider.start_send('rtp', file_path)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if url:
                start_cmd = multi.get_start_cmd(url)
            else:
                start_cmd = multi.start_play_cmd(1, 'rtp')
            multi.send_cmd(start_cmd)
            assert playerCheck.check_startPlay()[0], "start playback failed"
            for i in range(p_conf_repeat_count):
                youtube.start_youtube()
                time.sleep(10)
                # file_path = streamProvider.get_file_path('ts', 'PhilipsColorsofMiami')[0]
                # streamProvider.start_send('rtp', file_path)
                # start_cmd = multi.start_play_cmd(1, 'rtp')
                # assert playerCheck.check_startPlay(start_cmd)[0]
                os.system(f'adb -s {g_conf_device_id} shell {start_cmd}')
                time.sleep(10)
                netflix.start_play()
                time.sleep(10)
                # file_path = streamProvider.get_file_path('ts', 'PhilipsColorsofMiami')[0]
                # streamProvider.start_send('rtp', file_path)
                # start_cmd = multi.start_play_cmd(1, 'rtp')
                # assert playerCheck.check_startPlay(start_cmd)[0]
                os.system(f'adb -s {g_conf_device_id} shell {start_cmd}')
                time.sleep(10)
                multi.stop_multiPlayer_apk()
