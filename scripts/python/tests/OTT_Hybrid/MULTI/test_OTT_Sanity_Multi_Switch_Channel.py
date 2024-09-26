import logging
import numpy
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


def test_Switch_Channel():
    final_urllist = get_conf_url("conf_http_url", "http_TS_H264_1080")
    if p_conf_single_stream:
        for item in final_urllist:
            start_cmd = multi.get_start_cmd(url_list=[item, item], channel="2")
            multi.send_cmd(start_cmd)
            assert playerCheck.check_startPlay()[0], "start playback failed"
            switch_channel_cmd = multi.SWITCH_CHANNEL1
            logging.info(f"switch channel cmd:{switch_channel_cmd}")
            multi.send_cmd(switch_channel_cmd)
            assert playerCheck.check_switchChannel()[0], "switch channel failed"
            multi.stop_multiPlayer_apk()
    else:
        urls = numpy.stack([final_urllist, sorted(final_urllist, reverse=False)], 1).tolist()
        for item in urls:
            start_cmd = multi.get_start_cmd(url_list=[item[0], item[1]], channel="2")
            multi.send_cmd(start_cmd)
            assert playerCheck.check_startPlay()[0], "start playback failed"
            switch_channel_cmd = multi.SWITCH_CHANNEL1
            logging.info(f"switch channel cmd:{switch_channel_cmd}")
            multi.send_cmd(switch_channel_cmd)
            assert playerCheck.check_switchChannel()[0], "switch channel failed"
            multi.stop_multiPlayer_apk()
