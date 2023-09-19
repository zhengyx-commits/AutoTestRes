import logging
import pytest
from lib.common.system.Remote import Remote
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

remotePower = Remote()

p_conf_wifi_AP5 = p_conf_wifi['AP5']
p_conf_wifi_AP5_ssid = p_conf_wifi_AP5[0]['ssid']
p_conf_wifi_AP5_pwd = p_conf_wifi_AP5[0]['pwd']
# logging.info(f'test wifi standby wake up p_conf_wifi_AP5_ssid:{p_conf_wifi_AP5_ssid}, p_conf_wifi_AP5_pwd:{p_conf_wifi_AP5_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self, device):
        self.wifi.connect_check("wpaAndwpa2", p_conf_wifi_AP5_ssid, p_conf_wifi_AP5_pwd)
        str1, str2 = remotePower.check_power(flag="ott")
        logging.info('---standby wake up and wait AP reconnect---')
        assert str1 and str2 and str1 != str2
        assert self.wifi.check_reconnect()
