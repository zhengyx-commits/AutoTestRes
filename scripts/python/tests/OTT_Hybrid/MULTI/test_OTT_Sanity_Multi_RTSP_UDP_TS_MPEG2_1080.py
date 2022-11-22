import logging
from lib.common.system.ADB import ADB
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

g_conf_device_id = pytest.config['device_id']
multi = MultiPlayer(g_conf_device_id)
playerCheck = PlayerCheck()
adb = ADB()
streamProvider = StreamProvider()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()


def test_RTSP_UDP_TS_MPEG2_1080():
    stream_name_list, url = get_conf_url("conf_rtsp_url", "rtsp_TS_MPEG2_1080", "conf_stream_name", "mpeg2_1080I_30FPS")
    for stream_name in stream_name_list:
        file_path = streamProvider.get_file_path('mpeg2_1080I_30FPS', 'ts', stream_name)
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
                start_cmd = multi.start_play_cmd(1, 'rtsp_TS_MPEG2_1080')
            multi.send_cmd(start_cmd)
            assert playerCheck.check_startPlay()[0], "start playback failed"
            multi.stop_multiPlayer_apk()
