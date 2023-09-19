import logging
import time
import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_AP5 = p_conf_wifi['AP5']
p_conf_wifi_AP5_ssid = p_conf_wifi_AP5[0]['ssid']
p_conf_wifi_AP5_pwd = p_conf_wifi_AP5[0]['pwd']
# logging.info(f'test wifi restart p_conf_wifi_AP5_ssid:{p_conf_wifi_AP5_ssid}, p_conf_wifi_AP5_pwd:{p_conf_wifi_AP5_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self, device):
        self.wifi.connect_check("wpaAndwpa2", p_conf_wifi_AP5_ssid, p_conf_wifi_AP5_pwd)
        self.wifi.power_relay("powerRelay1_port", 'OFF')
        self.wifi.power_relay("powerRelay1_port", 'ON')
        logging.info('---restart and wait AP reconnect---')
        time.sleep(120)
        assert self.wifi.check_reconnect()
