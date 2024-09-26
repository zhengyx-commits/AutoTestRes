import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_AP5 = p_conf_wifi['AP5']
p_conf_wifi_AP5_ssid = p_conf_wifi_AP5[0]['ssid']
p_conf_wifi_AP5_pwd = p_conf_wifi_AP5[0]['pwd']
# logging.info(f'test wifi wpaAndwpa2 p_conf_wifi_AP5_ssid:{p_conf_wifi_AP5_ssid}, p_conf_wifi_AP5_pwd:{p_conf_wifi_AP5_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self):
        self.wifi.connect_check("wpaAndwpa2", p_conf_wifi_AP5_ssid, p_conf_wifi_AP5_pwd)
