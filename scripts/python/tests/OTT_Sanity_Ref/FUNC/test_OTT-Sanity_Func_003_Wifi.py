import logging
import time
import pytest

from lib.common.system.WIFI import WifiTestApk
from tests.OTT_Sanity_Ref import config_yaml, is_sz_server
from tests.OTT_Sanity_Ref.FUNC import player_check

p_conf_wifi = config_yaml.get_note('conf_wifi')
if not is_sz_server():
    p_conf_wifi_AP = p_conf_wifi['AP_SH']
else:
    p_conf_wifi_AP = p_conf_wifi['AP']
p_conf_wifi_AP_ssid = p_conf_wifi_AP['ssid']
p_conf_wifi_AP_pwd = p_conf_wifi_AP['pwd']
wifi = WifiTestApk()


@pytest.fixture(scope='function', autouse=True)
def setup():
    if 'com.example.wifiConnect' not in wifi.checkoutput('pm list package'):
        wifi.install_apk('apk/wifiConnect.apk')
        wifi.get_wifi_connect_permission()
    network_interface = player_check.create_network_auxiliary()
    player_check.offline_network(network_interface)
    time.sleep(5)
    yield
    player_check.restore_network(network_interface)
    time.sleep(10)
    wifi.uninstall_apk('com.example.wifiConnect')
    wifi.home()


def test_connect_ssid():
    logging.info('use apk connect')
    cmd = ''
    cmd += wifi.WIFI_CONNECT_COMMAND_REGU.format(p_conf_wifi_AP_ssid)
    cmd += wifi.WIFI_CONNECT_PASSWD_REGU.format(p_conf_wifi_AP_pwd)
    wifi.checkoutput(cmd)
    time.sleep(10)
    assert wifi.ping(), 'wifi connect failed'
    wifi.checkoutput(wifi.WIFI_CONNECT_ACTIVITY + wifi.WIFI_FORGET_WIFI_STR)

