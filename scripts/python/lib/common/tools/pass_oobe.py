#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/8/3 下午4:00
# @Author  : yongbo.shao
# @File    : pass_oobe.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import logging
import time
import pytest
from lib.common.system.ADB import ADB
import os
from tools.yamlTool import yamlTool
from tools.UiautomatorTool import UiautomatorTool
g_config_device_id = pytest.config['device_id']
u2 = UiautomatorTool(g_config_device_id)
adb = ADB()
config_common_yaml = yamlTool(os.getcwd() + '/config/config_common.yaml')
config_account_setting = config_common_yaml.get_note('conf_account_setting')
p_conf_account_setting_WIFI = config_account_setting['wifi_sh']
p_conf_account_setting_WIFI_SSID = p_conf_account_setting_WIFI['ssid']
p_conf_account_setting_WIFI_PWD = p_conf_account_setting_WIFI['pawd']
p_conf_account_setting_ACCOUNT = config_account_setting['account']['acc']
p_conf_account_setting_PWD = config_account_setting['account']['pawd']
CURRENT_FOCUS = 'dumpsys window | grep -i mCurrentFocus'
HOME_ACTIVITY = 'com.google.android.apps.tv.launcherx/com.google.android.apps.tv.launcherx.home.HomeActivity'


def pass_oobe():
    adb.keyevent(4)
    for i in range(20):
        logging.info(i)
        time.sleep(5)
        adb.uiautomator_dump()
        ui_text = adb.get_dump_info()
        if ("English" in ui_text) and ("United States" not in ui_text):
            u2.wait("English")
            time.sleep(2)
            u2.wait("United States")
        if "United States" in ui_text:
            u2.wait("United States")
            time.sleep(2)
        if "English (United States)" in ui_text:
            u2.wait("English (United States)")
            time.sleep(2)
        if "Quickly set up your TV with your Android phone?" in ui_text:
            u2.wait("Skip")
            time.sleep(5)
        if "Set up on TV instead" in ui_text:
            u2.wait("Set up on TV instead")
            time.sleep(5)
        if "Afghanistan" in ui_text:
            u2.wait("Afghanistan")
            time.sleep(5)
        if "Set up Google TV" in ui_text:
            u2.wait("Set up Google TV")
            time.sleep(5)
        if "You're connected to" in ui_text:
            u2.wait("Continue")
            time.sleep(20)
        if "Select your Wi-Fi network" in ui_text:
            for x in range(70):
                adb.shell("input keyevent 20")
            for y in range(6):
                adb.uiautomator_dump()
                ui_text = adb.get_dump_info()
                time.sleep(2)
                if "Other network" in ui_text:
                    u2.wait("Other network…")
                if "Enter name of Wi-Fi" in ui_text:
                    adb.text(p_conf_account_setting_WIFI_SSID)
                    adb.shell("input keyevent 66")
                if "Type of security" in ui_text:
                    u2.wait("WPA/WPA2-Personal")
                if "Enter password for" in ui_text:
                    adb.text(p_conf_account_setting_WIFI_PWD)
                    adb.shell("input keyevent 66")
                    time.sleep(60)
                    res = adb.run_shell_cmd("cmd wifi status")[1]
                    print("res", res)
                    if f"Wifi is connected to \"{p_conf_account_setting_WIFI_SSID}\"" in res:
                        logging.info("Wifi set up success")
                    else:
                        logging.info("Wifi set up failure")
                        adb.keyevent(4)
                        adb.keyevent(4)
        if "Make the most of your TV" in ui_text:
            u2.wait("Sign In")
            adb.text(p_conf_account_setting_ACCOUNT)
            adb.shell("input keyevent 66")
            time.sleep(10)
            adb.text(p_conf_account_setting_PWD)
            adb.shell("input keyevent 66")
            time.sleep(20)
        if "Sign in - Google Accounts" in ui_text:
            adb.text(p_conf_account_setting_ACCOUNT)
            adb.shell("input keyevent 66")
            time.sleep(10)
            adb.text(p_conf_account_setting_PWD)
            adb.shell("input keyevent 66")
            time.sleep(20)
        if "Terms of Service" in ui_text:
            u2.wait("Accept")
            time.sleep(5)
        if "Stay in the know" in ui_text:
            u2.wait("No thanks")
            time.sleep(5)
        if "Did you know?" in ui_text:
            u2.wait("Got it")
            time.sleep(5)
        if "Google Services" in ui_text:
            u2.wait("Accept")
            time.sleep(20)
        if "Get better voice control of your TV" in ui_text:
            u2.wait("Continue")
            time.sleep(5)
        if "text=\"Google Assistant\"" in ui_text:
            u2.wait("Continue")
            time.sleep(5)
        if "Search across all your TV apps" in ui_text:
            u2.wait("Allow")
            time.sleep(5)
        if "Activate Voice Match" in ui_text:
            u2.wait("I agree")
            time.sleep(5)
        if "Get personal results" in ui_text:
            u2.wait("Turn on")
            time.sleep(5)
        if "Get the most out of your Google Assistant" in ui_text:
            u2.wait("Yes")
            time.sleep(5)
        if "Install additional apps" in ui_text:
            u2.wait("Continue")
            time.sleep(5)
        if "You're signed in with" in ui_text:
            u2.wait("Continue")
            time.sleep(5)
        if "Get the full Assistant experience" in ui_text:
            u2.wait("Turn on")
            time.sleep(5)
        if "Choose your subscriptions" in ui_text:
            u2.wait("Confirm")
            time.sleep(10)
            timeout = 600
            counter = 0
            while counter < timeout:
                adb.uiautomator_dump()
                if "USB drive connected" in adb.get_dump_info():
                    adb.keyevent(4)
                    time.sleep(5)
                    break
                if "Your Google TV experience is ready" in adb.get_dump_info():
                    logging.info("Apps installation completed")
                    time.sleep(5)
                    break
                else:
                    time.sleep(10)
                    counter += 10
        if "USB drive connected" in ui_text:
            adb.keyevent(4)
            time.sleep(5)
        if "Your Google TV experience is ready" in ui_text:
            adb.wait_and_tap("Start exploring", "text")
            time.sleep(10)
            window = adb.run_shell_cmd(CURRENT_FOCUS)[1]
            if HOME_ACTIVITY in window:
                logging.info("Launch screen set up success")
                break
        if "Your Chromecast with Google TV is ready" in ui_text:
            adb.wait_and_tap("Start exploring", "text")
            time.sleep(10)
            window = adb.run_shell_cmd(CURRENT_FOCUS)[1]
            if HOME_ACTIVITY in window:
                logging.info("Launch screen set up success")
                break
        if ("Home" in ui_text) and ("Library" in ui_text):
            window = adb.run_shell_cmd(CURRENT_FOCUS)[1]
            if HOME_ACTIVITY in window:
                logging.info("Launch screen set up success")
                break

