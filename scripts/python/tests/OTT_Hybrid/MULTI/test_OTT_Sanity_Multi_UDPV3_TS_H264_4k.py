import logging
from lib.common.system.ADB import ADB
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

playerCheck = PlayerCheck_Iptv()
adb = ADB()
streamProvider = StreamProvider()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()


def test_UDPV3_TS_H264_4k():
    stream_name_list, url = get_conf_url("conf_udp_url", "udp", "conf_stream_name", "h264_4K_1")
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
                streamProvider.start_send('udp', file_path, iswait=True)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if url:
                start_cmd = multi.get_start_cmd(url)
            else:
                start_cmd = multi.start_play_cmd(1, 'udp')
            multi.send_cmd(start_cmd)
            assert playerCheck.check_startPlay()[0], "start playback failed"
            stop_cmd = multi.STOP_CMD
            multi.send_cmd(stop_cmd)
            assert playerCheck.check_stopPlay()[0], "stop playback failed"
            multi.stop_multiPlayer_apk()
