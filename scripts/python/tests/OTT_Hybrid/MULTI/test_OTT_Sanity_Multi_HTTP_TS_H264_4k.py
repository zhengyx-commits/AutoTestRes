from lib.common.system.ADB import ADB
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

playerCheck = PlayerCheck_Iptv()
adb = ADB()
common_case = Common_Playcontrol_Case()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


def test_HTTP_TS_H264_4k():
    final_urllist = get_conf_url("conf_http_url", "http_TS_H264_4K")
    for item in final_urllist:
        start_cmd = multi.get_start_cmd([item])
        multi.send_cmd(start_cmd)
        assert playerCheck.check_startPlay()[0], "start playback failed"
        common_case.pause_resume_seek_stop()
        multi.stop_multiPlayer_apk()
