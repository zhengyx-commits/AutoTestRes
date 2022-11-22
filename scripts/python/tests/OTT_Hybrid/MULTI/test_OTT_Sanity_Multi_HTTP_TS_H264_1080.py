from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

common_case = Common_Playcontrol_Case(playerNum=2)


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


def test_HTTP_TS_H264_1080():
    final_urllist = get_conf_url("conf_http_url", "http_TS_H264_1080")
    for item in final_urllist:
        # start_cmd = multi.get_start_cmd([item])
        start_cmd = multi.get_start_cmd([item, item], channel_num=2)
        multi.send_cmd(start_cmd)
        assert common_case.player_check.check_startPlay()[0], "start playback failed"
        # common_case.pause_resume_seek_stop()
        switch_channel_cmd = multi.SWITCH_CHANNEL
        print(switch_channel_cmd)
        multi.send_cmd(switch_channel_cmd)
        assert common_case.player_check.check_switchChannel()[0], "switch channel failed"
