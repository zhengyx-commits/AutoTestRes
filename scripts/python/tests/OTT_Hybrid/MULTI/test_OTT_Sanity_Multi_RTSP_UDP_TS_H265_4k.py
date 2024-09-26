from lib.common.system.ADB import ADB
from tools.StreamProvider import StreamProvider
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

playerCheck = PlayerCheck_Iptv()
adb = ADB()
streamProvider = StreamProvider()
common_case = Common_Playcontrol_Case()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()
    streamProvider.stop_send()


@pytest.mark.flaky(reruns=3)
def test_RTSP_UDP_TS_H265_4k():
    single_stream = p_conf_single_stream
    if single_stream:
        stream_name_list, url = get_conf_url("conf_rtsp_url", "rtsp_TS_H265_4K", "conf_stream_name", "h265_4K")
        file_path = streamProvider.get_file_path('h265_4K', 'ts', stream_name_list[0])
        if len(file_path) >= 1:
            file_path = file_path[0]
            try:
                streamProvider.start_send('rtsp', file_path)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            start_cmd = multi.get_start_cmd(url)
            multi.send_cmd(start_cmd)
            assert playerCheck.check_startPlay()[0], "start playback failed"
            common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()
    else:
        stream_name_list = get_conf_url("conf_rtsp_url", "rtsp_TS_H265_4K")
        for stream_name in stream_name_list:
            try:
                streamProvider.start_send('rtsp', stream_name)
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            if stream_name:
                start_cmd = multi.get_start_cmd(stream_name)
                multi.send_cmd(start_cmd)
                assert playerCheck.check_startPlay()[0], "start playback failed"
                multi.stop_multiPlayer_apk()
                streamProvider.stop_send()
