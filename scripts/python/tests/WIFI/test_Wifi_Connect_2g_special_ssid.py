#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/30 10:23
# @Author  : chao.li
# @Site    :
# @File    : test_Wifi_Connect_2g_special_ssid.py
# @Software: PyCharm

import logging
import time

import pytest
import os

from lib.common.system.WIFI import WifiTestApk
from tests.WIFI import Router, connect_wifi, forget_wifi
from tools.RouterControl.Asusac88uControl import Asusac88uControl
from tools.yamlTool import yamlTool

'''
测试配置
1.设置路由器2.4G 无线网络名称为“Abc123!@#2G测试”，隐藏SSID设置为否，无线模式设置为自动，频道带宽设置为20/40M,信道设置为自动，授权方式为open
2.连接2.4G SSID
3.从设备 shell里面 ping 路由器网关地址：ping 192.168.50.1
'''

ac88u = Asusac88uControl()
wifi = WifiTestApk()
p_conf_router_info = yamlTool(os.getcwd() + '/config/config_wifi.yaml').get_note('conf_connect_2g_special_ssid')


@pytest.fixture(scope='function', autouse=True)
def setup():
    # set router
    router = Router(band=p_conf_router_info['band'], ssid=p_conf_router_info['ssid'],
                    wireless_mode=p_conf_router_info['wireless_mode'],
                    channel=p_conf_router_info['channel'], bandwidth=p_conf_router_info['bandwidth'],
                    authentication_method=p_conf_router_info['authentication_method'])
    ac88u.change_setting(router)
    # connect wifi
    connect_wifi(router, passwd='')
    yield
    forget_wifi()


def test_connect_special_ssid():
    assert wifi.ping(hostname="192.168.50.1"), "Can't ping"
