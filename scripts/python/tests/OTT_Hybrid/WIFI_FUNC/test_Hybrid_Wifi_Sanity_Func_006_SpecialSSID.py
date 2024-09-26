import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_specialSSID = p_conf_wifi['specialSSID']
p_conf_wifi_specialSSID_ssid = p_conf_wifi_specialSSID[0]['ssid']
p_conf_wifi_specialSSID_pwd = p_conf_wifi_specialSSID[0]['pwd']
# logging.info(f'test wifi specialSsid p_conf_wifi_specialSSID_ssid:{p_conf_wifi_specialSSID_ssid}, p_conf_wifi_specialSSID_pwd:{p_conf_wifi_specialSSID_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self):
        self.wifi.connect_check("specialSsid", p_conf_wifi_specialSSID_ssid, p_conf_wifi_specialSSID_pwd)
