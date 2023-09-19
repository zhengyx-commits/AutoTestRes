from lib.common.system.WIFI import WifiTestApk
import pytest

wifi = WifiTestApk()


@pytest.fixture(scope='function', autouse=True)
def wifi_setup_teardown():
    wifi.wifi_setup()
    yield
    wifi.wifi_disconnect()


def test_wifi_nonePsk():
    wifi.connect_check('nonePsk')


def test_wifi_wep():
    wifi.connect_check('wep')


def test_wifi_wpa():
    wifi.connect_check('wpa')


def test_wifi_wpa2():
    wifi.connect_check('wpa2')


def test_wifi_wpaAndwpa2():
    wifi.connect_check('wpaAndwpa2')
