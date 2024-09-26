import logging
import time
import pytest
from tests.common.wifi.test_wifi_connect_system import WifiConnectBase
from . import *

p_conf_wifi_repeat_count = p_conf_wifi['repeat_count']
p_conf_wifi_AP5 = p_conf_wifi['AP5']
p_conf_wifi_AP5_ssid = p_conf_wifi_AP5[0]['ssid']
p_conf_wifi_AP5_pwd = p_conf_wifi_AP5[0]['pwd']
# logging.info(f'test wifi on/off p_conf_wifi_AP5_ssid:{p_conf_wifi_AP5_ssid}, p_conf_wifi_AP5_pwd:{p_conf_wifi_AP5_pwd}')

class TestWifiConnect(WifiConnectBase):
    def test_wifi_connect(self):
        self.wifi.connect_check("wpaAndwpa2", p_conf_wifi_AP5_ssid, p_conf_wifi_AP5_pwd)
        logging.info(f'---start to chang wifi state {p_conf_wifi_repeat_count} times---')
        for i in range(p_conf_wifi_repeat_count):
            self.wifi.wifi_state_off()
            self.wifi.wifi_state_on()
            logging.info(f'changed -> {i + 1} time')
        time.sleep(10)
        assert self.wifi.check_reconnect()