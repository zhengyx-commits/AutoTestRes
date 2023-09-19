import logging
import time
from lib.common.system.ADB import ADB
from tools.StreamProvider import StreamProvider
from . import p_conf_play_time_after_restore_network, p_conf_offline_network_time
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

playerCheck = PlayerCheck_Iptv()
adb = ADB()
streamProvider = StreamProvider()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.stop_multiPlayer_apk()
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()


@pytest.mark.flaky(reruns=3)
def test_rtsp_TS_H264_4k_offline_restore_network():
    single_stream = p_conf_single_stream
    if single_stream:
        stream_name_list, url = get_conf_url("conf_rtsp_url", "rtsp_TS_H264_4K", "conf_stream_name", "h264_4K")
        file_path = streamProvider.get_file_path('h264_4K', 'ts', stream_name_list[0])
        for stream_name in stream_name_list:
            try:
                streamProvider.start_send('rtsp', url)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            start_cmd = multi.get_start_cmd(url)
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
    else:
        stream_name_list = get_conf_url("conf_rtsp_url", "rtsp_TS_H264_4K")
        for stream_name in stream_name_list:
            try:
                streamProvider.start_send('rtsp', stream_name)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            start_cmd = multi.get_start_cmd(stream_name)
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
            streamProvider.stop_send()
