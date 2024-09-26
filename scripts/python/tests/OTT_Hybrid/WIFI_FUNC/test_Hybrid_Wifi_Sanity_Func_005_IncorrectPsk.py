import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_incorrectPsk = p_conf_wifi['incorrectPsk']
p_conf_wifi_incorrectPsk_ssid = p_conf_wifi_incorrectPsk[0]['ssid']
p_conf_wifi_incorrectPsk_pwd = p_conf_wifi_incorrectPsk[0]['pwd']
# logging.info(f'test wifi incorrectPsk p_conf_wifi_incorrectPsk_ssid:{p_conf_wifi_incorrectPsk_ssid}, p_conf_wifi_incorrectPsk_pwd:{p_conf_wifi_incorrectPsk_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self):
        self.wifi.connect_check("incorrectPsk", p_conf_wifi_incorrectPsk_ssid, p_conf_wifi_incorrectPsk_pwd)
