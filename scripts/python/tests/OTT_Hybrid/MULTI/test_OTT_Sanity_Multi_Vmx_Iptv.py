import pytest

from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

common_case = Common_Playcontrol_Case()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.root()
    os.system(f"adb -s {multi.serialnumber} shell su 0 date `date +%m%d%H%M%Y.%S`")
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


@pytest.mark.flaky(reruns=3)
def test_HTTP_HTTP_Widevine_Cas():
    url = "vstb:http://192.168.1.100/video/content_aa_clear.mpg"
    start_cmd = multi.get_start_cmd(url)
    multi.send_cmd(start_cmd)
    common_case.player_check.check_startPlay()
    common_case.pause_resume_seek_stop()
    multi.stop_multiPlayer_apk()
