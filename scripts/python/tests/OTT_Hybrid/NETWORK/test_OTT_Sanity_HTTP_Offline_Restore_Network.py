import time
from lib.common.system.ADB import ADB
from tools.StreamProvider import StreamProvider
from . import p_conf_play_time_after_restore_network, p_conf_offline_network_time
from tests.OTT_Hybrid.MULTI import *
from tests.OTT_Hybrid import *

playerCheck = PlayerCheck_Iptv()
adb = ADB()
streamProvider = StreamProvider()


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    multi.stop_multiPlayer_apk()
    multi.multi_setup()
    yield
    multi.stop_multiPlayer_apk()


@pytest.mark.flaky(reruns=3)
def test_http_TS_H265_4k_offline_restore_network():
    finalurl_list = get_conf_url('conf_http_url', 'http_TS_H265_4K')
    for item in finalurl_list:
        start_cmd = multi.get_start_cmd(item)
        multi.send_cmd(start_cmd)
        assert playerCheck.check_startPlay()[0], "start playback failed"
        network_interface = playerCheck.create_network_auxiliary()
        # offline network
        playerCheck.offline_network(network_interface)
        time.sleep(p_conf_offline_network_time)
        # restore network
        playerCheck.restore_network(network_interface)
        # restore playing less than 4s
        assert playerCheck.check_play_after_restore(p_conf_play_time_after_restore_network), "check common thread failed"
        # stop_cmd = multi.STOP_CMD
        # multi.send_cmd(stop_cmd)
        # assert playerCheck.check_stopPlay()[0], "stop playback failed"
        multi.stop_multiPlayer_apk()
