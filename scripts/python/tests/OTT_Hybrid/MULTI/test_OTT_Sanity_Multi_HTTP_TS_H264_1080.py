from time import sleep
import pytest
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

common_case = Common_Playcontrol_Case()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


@pytest.mark.flaky(reruns=3)
def test_HTTP_TS_H264_1080():
    final_urllist = get_conf_url("conf_http_url", "http_TS_H264_1080")
    for item in final_urllist:
        start_cmd = multi.get_start_cmd([item])
        multi.send_cmd(start_cmd)
        common_case.player_check.check_startPlay()
        common_case.pause_resume_seek_stop()
        multi.stop_multiPlayer_apk()
        sleep(2)
