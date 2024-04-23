#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/7/12 11:02
# @Author  : chao.li
# @Site    :
# @File    : test_OTT-Sanity_Func_079-082_Netflix.py
# @Software: PyCharm
import logging
from time import sleep

from lib.common.playback.Netflix import Netflix
from tests.OTT_Sanity_Ref import *

netflix = Netflix()
apk_exist = netflix.check_apk_exist()
config_seek_press_event = config_ott_sanity_yaml.get_note('conf_seek_press_event')
p_conf_seek_check = config_seek_press_event['seek_enable']
adb = ADB()
p_conf_wifi = config_yaml.get_note('conf_wifi')
if not is_sz_server():
    p_conf_wifi_AP = p_conf_wifi['AP_SH']
else:
    p_conf_wifi_AP = p_conf_wifi['AP']
p_conf_wifi_AP_ssid = p_conf_wifi_AP['ssid']
p_conf_wifi_AP_pwd = p_conf_wifi_AP['pwd']
p_conf_wifi_AP_security = p_conf_wifi_AP['security']


@pytest.fixture(scope='module', autouse=True)
def setup_teardown():
    # Start OMX print
    if netflix.getprop("ro.build.version.sdk") == "34":
        netflix.open_mediahal_info()
    else:
        netflix.open_omx_info()
    netflix.login_netflix(pytest.serialnumber)
    yield
    if netflix.getprop("ro.build.version.sdk") == "34":
        netflix.close_mediahal_info()
    else:
        netflix.close_omx_info()
    netflix.home()


@pytest.mark.skipif(condition=(1 - apk_exist), reason='apk not exist')
@pytest.mark.flaky(reruns=3)
def test_netflix_video():
    logging.info("Check the connection to the outside_internet")
    output = adb.run_shell_cmd("cmd wifi status")
    if f"Wifi is connected to \"{p_conf_wifi_AP_ssid}\"" in output[1]:
        logging.info(f"Wifi is connected to {p_conf_wifi_AP_ssid},start to play")
        assert netflix.netflix_play(seekcheck=p_conf_seek_check), 'playback not success'
    else:
        logging.info(f"No outside internet connection , star to connect {p_conf_wifi_AP_ssid}")
        adb.connect_wifi(ssid=p_conf_wifi_AP_ssid, pwd=p_conf_wifi_AP_pwd, security=p_conf_wifi_AP_security)
        sleep(5)
        assert netflix.netflix_play(seekcheck=p_conf_seek_check), 'playback not success'
