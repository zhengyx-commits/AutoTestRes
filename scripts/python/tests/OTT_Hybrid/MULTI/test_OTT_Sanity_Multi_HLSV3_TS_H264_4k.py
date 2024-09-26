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


@pytest.mark.skip
def test_HLSV3_TS_H264_4k():
    final_urllist = get_conf_url("conf_hls_url", "hlsV3_TS_H264_4K")
    for final_url in final_urllist:
        start_cmd = multi.get_start_cmd([final_url])
        multi.send_cmd(start_cmd)
        assert playerCheck.check_startPlay()[0], "start playback failed"
        pause_cmd = multi.PAUSE_CMD
        multi.send_cmd(pause_cmd)
        assert playerCheck.check_pause()[0], "playback pause failed"
        resume_cmd = multi.RESUME_CMD
        multi.send_cmd(resume_cmd)
        assert playerCheck.check_resume()[0], "playback resume failed"
        seek_cmd = multi.SEEK_CMD
        multi.send_cmd(seek_cmd)
        assert playerCheck.check_seek()[0], "playback seek failed"
        fb_cmd_1 = multi.FB_CMD
        assert playerCheck.check_speed(fb_cmd_1, 0.5, 120), "playback fb-0.5x speed failed"
        ff_cmd_1 = multi.FF_CMD_1
        assert playerCheck.check_speed(ff_cmd_1, 1.5, 30), "playback ff-1.5x speed failed"
        ff_cmd_2 = multi.FF_CMD_2
        assert playerCheck.check_speed(ff_cmd_2, 2.0, 30), "playback ff-2.0x speed failed"
        stop_cmd = multi.STOP_CMD
        multi.send_cmd(stop_cmd)
        assert playerCheck.check_stopPlay()[0], "stop playback failed"
        multi.stop_multiPlayer_apk()
