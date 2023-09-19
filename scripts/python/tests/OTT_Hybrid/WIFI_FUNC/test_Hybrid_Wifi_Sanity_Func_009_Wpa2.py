import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_AP4 = p_conf_wifi['AP4']
p_conf_wifi_AP4_ssid = p_conf_wifi_AP4[0]['ssid']
p_conf_wifi_AP4_pwd = p_conf_wifi_AP4[0]['pwd']
# logging.info(f'test wifi wp2 p_conf_wifi_AP4_ssid:{p_conf_wifi_AP4_ssid}, p_conf_wifi_AP4_pwd:{p_conf_wifi_AP4_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self):
        self.wifi.connect_check("wp2", p_conf_wifi_AP4_ssid, p_conf_wifi_AP4_pwd)