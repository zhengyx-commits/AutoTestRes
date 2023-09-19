#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/12/27 14:22
# @Author  : chao.li
# @Site    :
# @File    : __init__.py.py
# @Software: PyCharm


from lib.common.system.ADB import ADB
from lib.common.system.TvSetting import TvSettingApp
from tools.resManager import ResManager
import pytest
import logging
import time
from tests.OTT_Hybrid import *

p_conf_oobe = config_yaml.get_note('conf_oobe')
p_conf_wifi_ssid = p_conf_oobe['wifi']['ssid']
p_conf_wifi_pwd = p_conf_oobe['wifi']['pwd']
p_conf_account_acc = p_conf_oobe['account']['acc']
p_conf_account_pwd = p_conf_oobe['account']['pwd']
IPTV_MEDIA_SO = 'libAmIptvMedia.so'
resManager = ResManager()
adb = ADB()
# logging.info(f'oobe init wifi_ssid:{p_conf_wifi_ssid}, wifi_pwd:{p_conf_wifi_pwd}, account_acc:{p_conf_account_acc}, account_pwd:{p_conf_account_pwd}')

def connect_wifi():
    # connect wifi
    adb.wait_and_tap('Network & Internet', 'text')
    logging.info('Try to find See all')
    adb.keyevent(20)
    adb.keyevent(20)
    adb.keyevent(20)
    adb.keyevent(20)
    adb.wait_and_tap('See all', 'text')
    adb.uiautomator_dump()
    count = 0
    while p_conf_wifi_ssid not in adb.get_dump_info():
        adb.keyevent(20)
        adb.uiautomator_dump()
        count += 1
        if count > 50:
            raise Exception(f"Can't find {p_conf_wifi_ssid}")
    adb.u2.wait(p_conf_wifi_ssid)
    adb.text(p_conf_wifi_pwd)
    # for i in range(5):
    #     adb.keyevent(20)
    #     time.sleep(1)
    # adb.keyevent(21)
    time.sleep(1)
    adb.find_and_tap('com.android.tv.settings:id/guidedactions_item_title', 'resource-id')
    adb.enter()
    time.sleep(50)
    adb.keyevent(4)
    adb.keyevent(4)
    adb.keyevent(4)


def ott_login():
    adb.keyevent(20)
    adb.find_and_tap('Accounts & sign-in', 'text')
    time.sleep(3)
    adb.uiautomator_dump()
    if 'amlogictest1@gmail.com' in adb.get_dump_info():
        return
    logging.info('start to init ott')
    time.sleep(3)
    adb.wait_and_tap('Add another account', 'text')
    time.sleep(20)
    adb.u2.wait('Sign In')
    adb.text(p_conf_account_acc)
    time.sleep(3)
    adb.keyevent(4)
    adb.u2.wait('Next')
    time.sleep(5)
    adb.text(p_conf_account_pwd)
    time.sleep(5)
    adb.keyevent(4)
    adb.u2.wait('Next')
    adb.wait_and_tap('Accept', 'text')
    time.sleep(5)
    adb.keyevent(4)
    adb.keyevent(4)
    adb.keyevent(4)
    adb.keyevent(4)


if 'ott_hybrid' == pytest.target.get("prj"):
    adb = ADB()
    adb.keyevent(4)
    # adb.checkoutput('su')
    adb.run_shell_cmd('pm disable com.google.android.tungsten.setupwraith;settings put secure user_setup_complete 1;settings put secure tv_user_setup_complete 1;settings put global device_provisioned 1')
    adb.home()
    setting = TvSettingApp()
    if not adb.ping():
        logging.info('Try to connect wifi')
        setting.start()
        connect_wifi()
    setting.start()
    ott_login()
    time.sleep(5)

