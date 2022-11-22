from lib.common.system.ADB import ADB
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

g_conf_device_id = pytest.config['device_id']
multi = MultiPlayer(g_conf_device_id)
playerCheck = PlayerCheck(playerNum=2)
adb = ADB()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


def test_Switch_Channel():
    final_urllist = get_conf_url("conf_http_url", "http_TS_H264_1080")
    for item in final_urllist:
        start_cmd = multi.get_start_cmd([item, item])
        multi.send_cmd(start_cmd)
        assert playerCheck.check_startPlay()[0], "start playback failed"
        # common_case.pause_resume_seek_stop()
        switch_channel_cmd = multi.SWITCH_CHANNEL
        print(switch_channel_cmd)
        multi.send_cmd(switch_channel_cmd)
        assert playerCheck.check_switchChannel()[0], "switch channel failed"
