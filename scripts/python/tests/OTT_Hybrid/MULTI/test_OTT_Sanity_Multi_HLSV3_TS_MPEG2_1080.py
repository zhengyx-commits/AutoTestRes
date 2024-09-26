from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

common_case = Common_Playcontrol_Case()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


@pytest.mark.skip
def test_HLSV3_TS_MPEG2_1080():
    final_urllist = get_conf_url("conf_hls_url", "hlsV3_TS_MPEG2_1080")
    for item in final_urllist:
        start_cmd = multi.get_start_cmd([item])
        multi.send_cmd(start_cmd)
        assert common_case.player_check.check_startPlay()[0], "start playback failed"
        fb_cmd_1 = multi.FB_CMD
        assert common_case.player_check.check_speed(fb_cmd_1, 0.5, 120), "playback fb-0.5x speed failed"
        ff_cmd_1 = multi.FF_CMD_1
        assert common_case.player_check.check_speed(ff_cmd_1, 1.5, 30), "playback ff-1.5x speed failed"
        ff_cmd_2 = multi.FF_CMD_2
        assert common_case.player_check.check_speed(ff_cmd_2, 2.0, 30), "playback ff-2.0x speed failed"
        common_case.pause_resume_seek_stop()
        multi.stop_multiPlayer_apk()
