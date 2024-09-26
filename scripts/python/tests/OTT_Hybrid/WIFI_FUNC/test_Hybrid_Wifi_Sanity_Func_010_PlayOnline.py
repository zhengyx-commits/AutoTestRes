import logging
import time
import pytest

from lib.common.system.WIFI import WifiTestApk
from lib.common.playback.Youtube import YoutubeFunc
from . import *

wifi = WifiTestApk()
youtube = YoutubeFunc()
p_conf_wifi_test_time = p_conf_wifi['test_time']
test_time = p_conf_wifi_test_time * 60

p_conf_wifi_AP5 = p_conf_wifi['AP5']
p_conf_wifi_AP5_ssid = p_conf_wifi_AP5[0]['ssid']
p_conf_wifi_AP5_pwd = p_conf_wifi_AP5[0]['pwd']
# logging.info(f'test wifi play online p_conf_wifi_AP5_ssid:{p_conf_wifi_AP5_ssid}, p_conf_wifi_AP5_pwd:{p_conf_wifi_AP5_pwd}')

@pytest.fixture(scope='function', autouse=True)
def wifi_setup_teardown():
    wifi.wifi_setup()
    yield
    wifi.wifi_disconnect()


def test_PlayOnline():
    wifi.connect_check("wpaAndwpa2", p_conf_wifi_AP5_ssid, p_conf_wifi_AP5_pwd)
    time_ticks_begin = time.time()
    youtube.start_youtube()
    while True:
        localtime = time.asctime(time.localtime(time.time()))
        logging.info(f"local time is {localtime}")
        time_ticks_end = time.time()
        logging.info(f"time ticks is {time_ticks_end}")
        youtube.connect_speed(p_conf_wifi_AP5_ssid, p_conf_wifi_AP5_pwd)
        if time_ticks_end - time_ticks_begin > test_time:
            break
    youtube.stop_youtube()
