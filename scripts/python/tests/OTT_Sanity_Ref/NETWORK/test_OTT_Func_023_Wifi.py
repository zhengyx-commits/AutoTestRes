import logging
import time
import pytest
import allure
from lib.common.system.WIFI import WifiTestApk
from tests.OTT_Sanity_Ref import *

p_conf_wifi = config_ott_sanity_yaml.get_note('conf_wifi')
if not is_sz_server():
    p_conf_wifi_AP = p_conf_wifi['AP_SH']
else:
    p_conf_wifi_AP = p_conf_wifi['AP']
p_conf_wifi_AP_ssid = p_conf_wifi_AP['ssid']
p_conf_wifi_AP_pwd = p_conf_wifi_AP['pwd']
wifi = WifiTestApk()


@allure.step("turn off ethernet and install wifi apk before connect wifi")
@pytest.fixture(scope='module', autouse=True)
def setup():
    if 'com.example.wifiConnect' not in wifi.checkoutput('pm list package'):
        wifi.install_apk('apk/wifiConnect.apk')
        wifi.get_wifi_connect_permission()
    network_interface = adb.create_network_auxiliary()
    adb.offline_network(network_interface)
    time.sleep(5)
    yield
    adb.restore_network(network_interface)
    time.sleep(10)
    wifi.uninstall_apk('com.example.wifiConnect')
    wifi.home()


@allure.step("connect wifi and disconnect")
@pytest.mark.repeat(3)
def test_023_connect_ssid():
    logging.info('use apk connect')
    cmd = wifi.CMD_WIFI_CONNECT.format(p_conf_wifi_AP_ssid, "wpa2", p_conf_wifi_AP_pwd)
    wifi.checkoutput(cmd)
    time.sleep(10)
    assert wifi.ping(), 'wifi connect failed'
    ids = ",".join(wifi.checkoutput(wifi.CMD_WIFI_LIST_NETWORK).strip().split("\n"))
    print("ids: ", ids)
    id_list = ids.split(",")
    for id in id_list:
        wifi.checkoutput(wifi.CMD_WIFI_FORGET_NETWORK.format(id))
    time.sleep(5)
    assert not wifi.ping(), 'wifi disconnected failed'

