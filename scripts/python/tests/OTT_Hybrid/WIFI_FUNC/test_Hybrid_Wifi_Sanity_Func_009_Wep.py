import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_AP2 = p_conf_wifi['AP2']
p_conf_wifi_AP2_ssid = p_conf_wifi_AP2[0]['ssid']
p_conf_wifi_AP2_pwd = p_conf_wifi_AP2[0]['pwd']
# logging.info(f'test wifi wep p_conf_wifi_AP2_ssid:{p_conf_wifi_AP2_ssid}, p_conf_wifi_AP2_pwd:{p_conf_wifi_AP2_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self):
        self.wifi.connect_check("wep", p_conf_wifi_AP2_ssid, p_conf_wifi_AP2_pwd)