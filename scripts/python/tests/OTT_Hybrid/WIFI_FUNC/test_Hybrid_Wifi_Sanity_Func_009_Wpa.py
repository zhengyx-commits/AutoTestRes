import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_AP3 = p_conf_wifi['AP3']
p_conf_wifi_AP3_ssid = p_conf_wifi_AP3[0]['ssid']
p_conf_wifi_AP3_pwd = p_conf_wifi_AP3[0]['pwd']
# logging.info(f'test wifi wpa p_conf_wifi_AP3_ssid:{p_conf_wifi_AP3_ssid}, p_conf_wifi_AP3_pwd:{p_conf_wifi_AP3_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self):
        self.wifi.connect_check("wpa", p_conf_wifi_AP3_ssid, p_conf_wifi_AP3_pwd)
