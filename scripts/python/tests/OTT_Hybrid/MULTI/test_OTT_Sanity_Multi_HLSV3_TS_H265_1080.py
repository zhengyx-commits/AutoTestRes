from lib.common.system.ADB import ADB
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

playerCheck = PlayerCheck_Iptv()
adb = ADB()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


def test_HLSV3_TS_H265_1080():
    final_urllist = get_conf_url("conf_hls_url", "hlsV3_TS_H265_1080")
    for item in final_urllist:
        start_cmd = multi.get_start_cmd(item)
        multi.send_cmd(start_cmd)
        assert playerCheck.check_startPlay()[0], "start playback failed"
        multi.stop_multiPlayer_apk()
