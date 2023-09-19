import logging
import re
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
def test_RTP_TS_H265_1080():
    stream_name_list, url = get_conf_url("conf_rtp_url", "rtp", "conf_stream_name", "h265_1080P")
    for stream_name in stream_name_list:
        file_path = streamProvider.get_file_path('h265_1080P', 'ts', stream_name)
        if len(file_path) >= 1:
            file_path = file_path[0]
            try:
                streamProvider.start_send('rtp', file_path, url=url[-4:])
            except Exception as e:
                logging.error("stream provider start send failed.")
                raise False
            start_cmd = multi.get_start_cmd(url)
            multi.send_cmd(start_cmd)
            assert playerCheck.check_startPlay()[0], "start playback failed"
            #common_case.pause_resume_seek_stop()
            multi.stop_multiPlayer_apk()
            streamProvider.stop_send()
