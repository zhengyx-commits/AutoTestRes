from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

common_case = Common_Playcontrol_Case()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


@pytest.mark.skip
def test_HLSV5_TS_H264_1080():
    final_urllist = get_conf_url("conf_hls_url", "hlsV5_TS_H264_1080")
    for item in final_urllist:
        start_cmd = multi.get_start_cmd([item])
        multi.send_cmd(start_cmd)
        assert common_case.player_check.check_startPlay()[0], "start playback failed"
        common_case.pause_resume_seek_stop()
