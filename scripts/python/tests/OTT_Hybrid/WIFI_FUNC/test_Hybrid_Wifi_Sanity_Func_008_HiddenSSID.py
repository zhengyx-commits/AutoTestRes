import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_hiddenSSID = p_conf_wifi['hiddenSSID']
p_conf_wifi_hiddenSSID_ssid = p_conf_wifi_hiddenSSID[0]['ssid']
p_conf_wifi_hiddenSSID_pwd = p_conf_wifi_hiddenSSID[0]['pwd']
p_conf_wifi_hiddenSSID_security = p_conf_wifi_hiddenSSID[0]['security']
# logging.info(f'test wifi hiddenSSID p_conf_wifi_specialSSID_ssid:{p_conf_wifi_specialSSID_ssid}, p_conf_wifi_specialSSID_pwd:{p_conf_wifi_specialSSID_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self):
        self.wifi.connect_check("hiddenSSID", p_conf_wifi_hiddenSSID_ssid, p_conf_wifi_hiddenSSID_pwd, hidden="true", security=p_conf_wifi_hiddenSSID_security)
