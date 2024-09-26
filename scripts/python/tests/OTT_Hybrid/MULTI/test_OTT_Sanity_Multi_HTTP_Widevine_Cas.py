from time import sleep
import pytest
from tools.resManager import ResManager
from lib.common.system.ADB import ADB
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *
import time

common_case = Common_Playcontrol_Case()
res_manager = ResManager()

@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    res_manager.get_target(path="wvcas_so", source_path="so/wvcas_so")
    res_manager.get_target(path="wvcas_video/bbb_1080p_30fps_mp3_enc_cbc_fixed_content_iv.ts",
                           source_path="wvcas_video")
    multi.add_so()
    time.sleep(10)
    multi.multi_setup()
    common_case.set_wifi_enabled()
    time.sleep(5)
    multi.root()
    multi.run_shell_cmd("setenforce 0")
    multi.run_shell_cmd("getenforce")
    multi.run_shell_cmd("chmod 777 /data")
    multi.run_shell_cmd("chmod 777 /data/bbb_1080p_30fps_mp3_enc_cbc_fixed_content_iv.ts")
    yield
    common_case.forget_outside_wifi()
    multi.stop_multiPlayer_apk()


@pytest.mark.flaky(reruns=3)
def test_HTTP_HTTP_Widevine_Cas():
    url = "wcas:/data/bbb_1080p_30fps_mp3_enc_cbc_fixed_content_iv.ts"
    start_cmd = multi.get_start_cmd(url)
    multi.send_cmd(start_cmd)
    common_case.player_check.check_startPlay()
    common_case.pause_resume_seek_stop()
    multi.stop_multiPlayer_apk()
