import logging
import time
from lib.common.system.ADB import ADB
from tools.StreamProvider import StreamProvider
from . import p_conf_play_time_after_restore_network, p_conf_offline_network_time
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

g_conf_device_id = pytest.config['device_id']
multi = MultiPlayer(g_conf_device_id)
playerCheck = PlayerCheck()
adb = ADB()
streamProvider = StreamProvider()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.stop_multiPlayer_apk()
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()


# @pytest.mark.flaky(reruns=3)
# @pytest.mark.skip
def test_rtsp_TS_H264_4k_offline_restore_network():
    stream_name_list, url = get_conf_url("conf_rtsp_url", "rtsp_TS_H264_4K", "conf_stream_name", "h264_4K")
    for stream_name in stream_name_list:
        file_path = streamProvider.get_file_path('h264_4K', 'ts', stream_name)
        if file_path:
            file_path = file_path[0]
        # if not streamProvider.get_file_path('ts', stream_name):
        #     logging.error("stream provider file path doesn't exist.")
        #     return
        # else:
        #     file_path = streamProvider.get_file_path('ts', stream_name)[0]
            try:
                streamProvider.start_send('rtsp', file_path)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if url:
                start_cmd = multi.get_start_cmd(url)
            else:
                start_cmd = multi.start_play_cmd(1, 'rtsp_TS_H264_4K')
            multi.send_cmd(start_cmd)
            assert playerCheck.check_startPlay()[0], "start playback failed"
            network_interface = playerCheck.create_network_auxiliary()
            # offline network
            playerCheck.offline_network(network_interface)
            time.sleep(p_conf_offline_network_time)
            # restore network
            playerCheck.restore_network(network_interface)
            # restore playing less than 4s
            assert playerCheck.check_play_after_restore(p_conf_play_time_after_restore_network), "check common thread failed"
            # stop_cmd = multi.STOP_CMD
            # multi.send_cmd(stop_cmd)
            # assert playerCheck.check_stopPlay()[0], "stop playback failed"
            multi.stop_multiPlayer_apk()
