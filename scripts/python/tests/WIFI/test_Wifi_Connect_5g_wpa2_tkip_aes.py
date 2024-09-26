#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/6/10 13:55
# @Author  : chao.li
# @Site    :
# @File    : test_Wifi_Connect_5g_wpa2_tkip_aes.py
# @Software: PyCharm

import pytest
import os

from lib.common.system.WIFI import WifiTestApk
from tests.WIFI import Router, connect_wifi, forget_wifi
from tools.RouterControl.Asusac88uControl import Asusac88uControl
from tools.yamlTool import yamlTool

'''
测试配置
1.设置路由器5G 无线网络名称为“ATC_ASUS_AX88U_5G”，隐藏SSID设置为否，无线模式设置为自动，频道带宽设置为20/40/80M,信道设置为149，授权方式为WPA/WPA2-Personal,WPA加密选择TKIP+AES，WPA-PSK无线密码设置为Abc@$123456，受保护的管理帧设置为禁用
2.连接5G SSID
3.从设备 shell里面 ping 路由器网关地址：ping 192.168.50.1
'''

ac88u = Asusac88uControl()
wifi = WifiTestApk()
p_conf_router_info = yamlTool(os.getcwd() + '/config/config_wifi.yaml').get_note('conf_connect_5g_wpa2_tkip_aes')


@pytest.fixture(scope='function', autouse=True)
def setup():
    # set router
    router = Router(band=p_conf_router_info['band'], ssid=p_conf_router_info['ssid'],
                    wireless_mode=p_conf_router_info['wireless_mode'],
                    channel=p_conf_router_info['channel'], bandwidth=p_conf_router_info['bandwidth'],
                    authentication_method=p_conf_router_info['authentication_method'],
                    wpa_passwd=p_conf_router_info['wpa_passwd'], protect_frame=p_conf_router_info['protect_frame'],
                    wpa_encrypt=p_conf_router_info['wpa_encrypt'])
    ac88u.change_setting(router)
    # connect wifi
    connect_wifi(router, type='wpa2', passwd=router.wpa_passwd)
    yield
    forget_wifi()


def test_connect_tkip_aes_ssid():
    assert wifi.ping(hostname="192.168.50.1"), "Can't ping"
