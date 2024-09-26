#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/3/2 10:17
# @Author  : chao.li
# @Site    :
# @File    : OpenWrtWifi.py
# @Software: PyCharm

import logging
import time
from collections import namedtuple

from lib.common.system.SSH import SSH


def router_str(self):
    return f'{self.band} {self.ssid} {self.passwd} {self.wireless_mode} {self.channel} {self.bandwidth} {self.authentication_method}'


Router = namedtuple('Router',
                    ['band', 'channel', 'bandwidth', 'wireless_mode', 'authentication_method', 'ssid', 'passwd'],
                    defaults=(None, None, None, None, None, '@wifismoketest', '@12345678')
                    )
Router.__str__ = router_str


class OpenWrt:
    '''
    openwrt router control

    Attributes:
        SECURITY_MODE : encryption mode
        WIFI_MODE_5G : 5g mode
        WIDTH_5G : 5g width
        CHANNEL_5G : 5g channel
        WIFI_MODE_2G : 2g mode
        WIDTH_2G : 2g width
        CHANNEL_2G : 2g channel
        ESSID : wifi ssid
        PASSWD : wifi password

        TESTCASE_5G : 5g Router list
        TESTCASE_2G : 2g Router list

        ssh : SSH instance
        set_command_format : set wifi env command

    '''
    SECURITY_MODE = {
        'WPA2-PSK (strong security)': 'psk2',
        'WPA3-SAE (strong security)': 'sae',
        'WPA2-PSK/WPA3-SAE Mixed Mode (strong security)': 'sae-mixed',
        'WPA-PSK/WPA2-PSK Mixed Mode (medium security)': 'psk-mixed',
        'WPA-PSK (medium security)': 'psk',
        # 'OWE (open network)': 'owe',
    }
    WIFI_MODE_5G = {
        'Legacy': '',
        'N': 'n',
        'AC': 'ac'
    }
    WIDTH_5G = {
        '20 MHz': 'VHT20',
        '40 MHz': 'VHT40',
        '80 MHz': 'VHT80',

    }
    CHANNEL_5G = {
        'auto': 'auto',
        '36 (5180 Mhz)': '36',
        '48 (5240 Mhz)': '48',
        '64 (5320 Mhz)': '64',
        '104 (5520 Mhz)': '104',
        '132 (5660 Mhz)': '132',
        '149 (5745 Mhz)': '149',
        '165 (5825 Mhz)': '165',
    }
    WIFI_MODE_2G = {
        'Legacy': '',
        'N': 'n'
    }
    WIDTH_2G = {
        '20 MHz': 'HT20',
        '40 MHz': 'HT40'
    }
    CHANNEL_2G = {
        'auto': 'auto',
        '1 (2412 Mhz)': '1',
        '6 (2437 Mhz)': '6',
        '10 (2457 Mhz)': '10',
        '11 (2462 Mhz)': '11',
    }

    ESSID = {
        '1': 'AAA'
    }
    PASSWD = {
        '1': 'AAA'
    }

    def __init__(self):
        try:
            self.ssh = SSH('192.168.1.1', uname='root', passwd='root')
        except Exception as e:
            raise EnvironmentError("Can't connect Tp-link pls check again!!")
        # band   ssid  passwd wireless_mode channel bandwidth authentication_method
        # 5 GHz Cocoishandsome 12345678  auto VHT20 psk2
        self.TESTCASE_5G = [Router('5 GHz', v, v1, v2, v3, '@5gwifismoketest') for k, v in self.CHANNEL_5G.items()
                            for k1, v1 in self.WIDTH_5G.items()
                            for k2, v2 in self.WIFI_MODE_5G.items()
                            for k3, v3 in self.SECURITY_MODE.items()]
        self.TESTCASE_2G = [Router('2 GHz', v, v1, v2, v3, '@2gwifismoketest') for k, v in self.CHANNEL_2G.items()
                            for k1, v1 in self.WIDTH_2G.items()
                            for k2, v2 in self.WIFI_MODE_2G.items()
                            for k3, v3 in self.SECURITY_MODE.items()]
        self.set_command_format = ("uci set wireless.@wifi-iface[{0}].ssid='{1}';"
                                   "uci set wireless.@wifi-iface[{0}].key='{2}';"
                                   "uci set wireless.@wifi-iface[{0}].encryption={3};"
                                   "uci set wireless.@wifi-device[{0}].channel='{4}';"
                                   "uci set wireless.@wifi-device[{0}].htmode='{5}';"
                                   "uci commit;"
                                   "/etc/init.d/network restart;")

    def change_router(self, router):
        logging.info(router)
        command = self.set_command_format.format('0' if '5' in router.band else '1', router.ssid, router.passwd,
                                                 router.authentication_method, router.channel, router.bandwidth)
        logging.info(command)
        logging.info(time.asctime())
        self.ssh.send_cmd(command)
        logging.info('done')
        logging.info(time.asctime())

# openWrt = OpenWrt()
# print(len(openWrt.TESTCASE_2G))
# print(len(openWrt.TESTCASE_5G))
