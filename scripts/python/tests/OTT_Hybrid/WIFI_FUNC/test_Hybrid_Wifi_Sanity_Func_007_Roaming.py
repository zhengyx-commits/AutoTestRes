import logging
import pytest
import time
from lib.common.system.WIFI import WifiTestApk
from . import *

wifi = WifiTestApk()

p_conf_wifi_AP5 = p_conf_wifi['AP5']
p_conf_wifi_AP5_ssid = p_conf_wifi_AP5[0]['ssid']
p_conf_wifi_AP5_pwd = p_conf_wifi_AP5[0]['pwd']
# logging.info(f'test wifi roaming p_conf_wifi_AP5_ssid:{p_conf_wifi_AP5_ssid}, p_conf_wifi_AP5_pwd:{p_conf_wifi_AP5_pwd}')

@pytest.fixture(scope='function', autouse=True)
def wifi_setup_teardown():
    wifi.wifi_setup()
    yield
    wifi.wifi_disconnect()
    wifi.power_relay('powerRelay2_port', 'ON')


@pytest.mark.skip()
def test_roaming():
    wifi.power_relay('powerRelay1_port', 'OFF')
    wifi.power_relay('powerRelay2_port', 'ON')
    wifi.connect_check("wpaAndwpa2", p_conf_wifi_AP5_ssid, p_conf_wifi_AP5_pwd)
    wifi.power_relay('powerRelay1_port', 'ON')
    wifi.power_relay('powerRelay2_port', 'OFF')
    logging.info('---restart DUT and wait AP reconnect---')
    time.sleep(90)
    assert wifi.check_reconnect()
