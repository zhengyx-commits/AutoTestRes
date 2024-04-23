import time

import pytest
from tests.OTT.lib.OTTNetset import OTTNetSet
from lib.common.system.WIFI import WifiTestApk

ott_netset = OTTNetSet()
wifi = WifiTestApk()

ipaddr = ott_netset.ipaddr
gateway = ott_netset.gateway


@pytest.fixture(scope='function', autouse=True)
def setUp_teardown():
    ott_netset.start()
    ott_netset.click_ipsetting()
    yield
    ott_netset.click_ipsetting()
    ott_netset.wait_and_tap("IP settings", "text")
    ott_netset.wait_and_tap("DHCP", "text")
    ott_netset.stop()


def test_024_ethernet_connect():
    ott_netset.connect_staticIPv4(ipaddr, gateway)
    assert ott_netset.ethernet_check(ipaddr), 'ethernet connect failed'
    time.sleep(10)
    assert wifi.check_ping_host("eth0"), 'ping host failed'
