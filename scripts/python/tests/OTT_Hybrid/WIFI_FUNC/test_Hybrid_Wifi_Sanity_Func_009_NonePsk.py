import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_AP1 = p_conf_wifi['AP1']
p_conf_wifi_AP1_ssid = p_conf_wifi_AP1[0]['ssid']
# logging.info(f'test wifi nonePsk p_conf_wifi_AP1_ssid:{p_conf_wifi_AP1_ssid}}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self):
        self.wifi.connect_check("nonePsk", p_conf_wifi_AP1_ssid)
