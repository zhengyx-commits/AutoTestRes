#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/8/3 下午4:00
# @Author  : yongbo.shao
# @File    : pass_oobe.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import logging
import subprocess
import time
from lib.common.system.ADB import ADB
import os
from tools.yamlTool import yamlTool
from tools.UiautomatorTool import UiautomatorTool
from lib.common.system.Bluetooth import Bluetooth


def check_ipadd(ip_address):
    ipadd = subprocess.run(["ifconfig"], stdout=subprocess.PIPE, text=True)
    return ip_address in ipadd.stdout


adb = ADB()
u2 = UiautomatorTool(adb.serialnumber)
ble = Bluetooth()
workspace = os.getcwd()
CURRENT_FOCUS = 'dumpsys window | grep -i mCurrentFocus'
HOME_ACTIVITY = 'com.google.android.apps.tv.launcherx/com.google.android.apps.tv.launcherx.home.HomeActivity'
STAY_AWAKE = "settings put global stay_on_while_plugged_in 1"
GOOGLE_PLAY_STORE = "com.android.vending/com.google.android.finsky.tvmainactivity.TvMainActivity"
GOOGLE_PLAY_PACKAGE = "com.android.vending"
config_oobe_yaml = yamlTool(os.getcwd() + '/config/config_oobe.yaml')
config_tc8000_yaml = yamlTool(os.getcwd() + '/config/config_tc8000.yaml')
config_tc8000_page_info = config_tc8000_yaml.get_note("oobe_page_info")
config_pages_info = config_oobe_yaml.get_note("pages_info")
if "TC8000" in workspace:
    config_pages_info += config_tc8000_page_info
config_wifi_info = config_oobe_yaml.get_note("wifi_settings")
config_account_info = config_oobe_yaml.get_note("google_account")
if "_SZ" in workspace:
    if "Sanity" in workspace or "Basic" in workspace:
        p_conf_wifi_ssid = config_wifi_info["wifi_sanity"]["ssid"]
        p_conf_wifi_pwd = config_wifi_info["wifi_sanity"]["pwd"]
        p_conf_google_account = config_account_info["account_sz"]["account"]
        p_conf_google_account_pwd = config_account_info["account_sz"]["pwd"]
    else:
        p_conf_wifi_ssid = config_wifi_info["wifi_sz"]["ssid"]
        p_conf_wifi_pwd = config_wifi_info["wifi_sz"]["pwd"]
        p_conf_google_account = config_account_info["account_sz"]["account"]
        p_conf_google_account_pwd = config_account_info["account_sz"]["pwd"]
elif "_XA" in workspace:
    p_conf_wifi_ssid = config_wifi_info["wifi_xa"]["ssid"]
    p_conf_wifi_pwd = config_wifi_info["wifi_xa"]["pwd"]
    p_conf_google_account = config_account_info["account_xa"]["account"]
    p_conf_google_account_pwd = config_account_info["account_xa"]["pwd"]
else:
    if "KPI_common" in workspace or "Basic" in workspace:
        p_conf_wifi_ssid = config_wifi_info["wifi_sh"]["ssid"]
        p_conf_wifi_pwd = config_wifi_info["wifi_sh"]["pwd"]
        p_conf_google_account = config_account_info["account_sh_kpi"]["account"]
        p_conf_google_account_pwd = config_account_info["account_sh_kpi"]["pwd"]
    else:
        p_conf_wifi_ssid = config_wifi_info["wifi_sanity"]["ssid"]
        p_conf_wifi_pwd = config_wifi_info["wifi_sanity"]["pwd"]
        p_conf_google_account = config_account_info["account_sh"]["account"]
        p_conf_google_account_pwd = config_account_info["account_sh"]["pwd"]


def del_input_text(number=20):
    for i in range(int(number)):
        adb.keyevent(67)


def check_bluetooth_pair():
    HAS_IN_HOME = []
    for i in range(15):
        logging.info(f"Pair bluetooth_remote for {i + 1} times")
        ble.remote_enter_pair()
        adb.uiautomator_dump()
        ui_info = adb.get_dump_info()
        # logging.info(f"ui_info is {ui_info}")
        if ("id/remote_pairing_video" in ui_info) or ("id/imageView1" in ui_info and "button exit" in ui_info):
            logging.info(f"{adb.serialnumber} is now in remote pairing mode, Continue to pair bluetooth_remote!")
            continue
        elif ("text=\"Home\"" in ui_info) or ("text=\"Library\"" in ui_info) or ("text=\"Apps\"" in ui_info):
            logging.info(f"{adb.serialnumber} is now in the home page. maybe the OOBE process has passed.")
            HAS_IN_HOME.append(adb.serialnumber)
            continue
        elif "text=\"Restart now\"" in ui_info:
            logging.info(f"{adb.serialnumber} now in sleep mode, reboot it!")
            os.system(f"adb -s {adb.serialnumber} reboot")
            time.sleep(60)
        elif "text=\"Searching for accessories…\"" in ui_info:
            adb.back()
        else:
            pass_oobe(isBlueToothPair=True)
            break


def check_oobe():
    home_launcher = config_oobe_yaml.get_note("home_launcher")
    adb.keyevent(4)
    adb.home()
    time.sleep(5)
    activity = adb.run_shell_cmd(CURRENT_FOCUS)[1]
    for tv_mode, launcher in home_launcher.items():
        if launcher in activity:
            logging.info(f"{adb.serialnumber} in {tv_mode} home page")
            adb.shell(STAY_AWAKE)
            return True
    logging.info(f"{adb.serialnumber} may pass oobe failed!!!!")
    return False


def pass_oobe(basic=False, isBlueToothPair=False):
    if not isBlueToothPair:
        adb.keyevent(4)
    input_count = 0
    if check_oobe():
        logging.info("oobe passed!")
        return True
    else:
        adb.shell(f"cmd wifi connect-network {p_conf_wifi_ssid} wpa2 {p_conf_wifi_pwd}")
        for i in range(25):
            time.sleep(5)
            adb.uiautomator_dump()
            ui_info = adb.get_dump_info()
            if ("text=\"Library\"" in ui_info) or ("text=\"Apps\"" in ui_info):
                logging.info(
                    f"*****{adb.serialnumber} is now in the home page. maybe the OOBE process has passed.*****")
                return True
            for page in config_pages_info:
                page_info = page.get("page_info", None)
                button = page.get("button", None)
                text = page.get("text", None)
                remote = page.get("remote", None)
                wait_time = page.get("wait_time", 5)
                if page_info is None:
                    raise Exception("Page info is none,please check config_oobe.yaml")
                logging_text = f"Current_page:{page_info}>>click_button:{button}>>text_box:{text}>>remote_control:{remote}>>wait_time:{wait_time}"
                if (button is not None) and (button in ui_info) and (page_info in ui_info):
                    if button == "Set up Google TV" and basic:
                        button = "Set up Basic TV"
                    logging.info(logging_text)
                    u2.wait(button)
                    if button == "Select All":
                        adb.keyevent(19)
                        adb.keyevent(23)
                    if button == "Confirm" or button == "Done":
                        timeout = 600
                        counter = 0
                        while counter < timeout:
                            adb.uiautomator_dump()
                            installing = adb.get_dump_info()
                            if ("Your Google TV experience is ready" in installing) or (
                                    "text=\"100% complete\"" in installing) or ("text=\"Apps\"" in installing) or (
                                    "text=\"Start exploring\"" in installing) or (
                                    "text=\"Pair Your Remote\"" in installing):
                                logging.info("Apps installation completed")
                                break
                            if "USB drive connected" in installing:
                                adb.keyevent(4)
                                break
                            time.sleep(10)
                            counter += 10
                    if button == "Start exploring":
                        return check_oobe()
                    time.sleep(int(wait_time))
                    break
                if (text is not None) and (page_info in ui_info):
                    logging.info(logging_text)
                    if input_count > 0:
                        del_input_text()
                    if text == "wifi_ssid":
                        adb.text(p_conf_wifi_ssid)
                    elif text == "wifi_pwd":
                        adb.text(p_conf_wifi_pwd)
                    elif text == "google_account":
                        adb.text(p_conf_google_account)
                        adb.keyevent(66)
                        time.sleep(10)
                        for string in p_conf_google_account_pwd:
                            adb.text(string)
                            time.sleep(0.5)
                    adb.keyevent(66)
                    input_count += 1
                    time.sleep(int(wait_time))
                    break
                if (remote is not None) and (page_info in ui_info):
                    logging.info(logging_text)
                    for remote_info in remote:
                        for _ in range(int(remote_info["number"])):
                            adb.keyevent(remote_info["keyevent"])
                    time.sleep(int(wait_time))
                    if page_info == "powered by Android TV":
                        return check_oobe()
                    if page_info == "USB drive connected":
                        return check_oobe()


def close_app_return_home(package):
    adb.shell(f"am force-stop {package}")
    adb.home()
    if check_oobe():
        logging.info("Return Home success")


def open_google_play():
    start_google_play_count = 0
    max_play_count = 3
    while start_google_play_count < max_play_count:
        adb.shell(f"am start -n {GOOGLE_PLAY_STORE}")
        time.sleep(10)
        res = adb.run_shell_cmd(CURRENT_FOCUS)[1]
        if GOOGLE_PLAY_STORE in res:
            logging.info("Google Play opened successfully")
            return True
        else:
            logging.info("Google Play open failed, return home and retry")
            adb.shell(f"am force-stop {GOOGLE_PLAY_PACKAGE}")
            adb.home()
        start_google_play_count += 1
    return False


def search_download_app(app_name, time_out=180):
    if open_google_play():
        time.sleep(3)
        adb.keyevent(19)
        adb.keyevent(19)
        time.sleep(3)
        adb.keyevent(21)
        time.sleep(3)
        adb.keyevent(20)
        time.sleep(3)
        adb.keyevent(22)
        time.sleep(3)
        adb.shell(f"'input text \"{app_name}\";input keyevent 66'")
        time.sleep(3)
        adb.uiautomator_dump()
        search_result = adb.get_dump_info()
        if app_name in search_result:
            if "text=\"Install\"" in search_result:
                u2.wait("Install")
                logging.info(f"{app_name} installing>>>")
                count = 0
                while count <= time_out:
                    adb.uiautomator_dump()
                    installing = adb.get_dump_info()
                    if "text=\"Open\"" in installing or "text=\"Play\"" in installing:
                        logging.info(f"{app_name} install successful")
                        close_app_return_home(GOOGLE_PLAY_PACKAGE)
                        return True
                    if "Connect a gamepad" in installing:
                        u2.wait("Continue")
                    time.sleep(10)
                    count += 10
            elif "text=\"Open\"" in search_result:
                logging.info(f"{app_name} has installed,return home")
                close_app_return_home(GOOGLE_PLAY_PACKAGE)
                return True
            else:
                adb.keyevent(23)
                time.sleep(3)
                adb.uiautomator_dump()
                ui_info = adb.get_dump_info()
                if "text=\"Install\"" in ui_info:
                    u2.wait("Install")
                    logging.info(f"{app_name} installing>>>")
                    count = 0
                    while count <= time_out:
                        adb.uiautomator_dump()
                        installing = adb.get_dump_info()
                        if "text=\"Open\"" in installing or "text=\"Play\"" in installing:
                            logging.info(f"{app_name} install successful")
                            close_app_return_home(GOOGLE_PLAY_PACKAGE)
                            return True
                        if "Connect a gamepad" in installing:
                            u2.wait("Continue")
                        time.sleep(10)
                        count += 10
        else:
            logging.info(f"Can't find {app_name} in Google Play Store")
            close_app_return_home(GOOGLE_PLAY_PACKAGE)
            return False
    logging.info("May open Google Play failed!")
    return False


def update_apps():
    if open_google_play():
        time.sleep(3)
        adb.shell("'input keyevent 19;input keyevent 19;input keyevent 19'")
        time.sleep(1)
        adb.shell("'input keyevent 22;input keyevent 22;input keyevent 22'")
        time.sleep(3)
        u2.wait("Updates")
        u2.wait("Updates")
        time.sleep(3)
        adb.uiautomator_dump()
        ui_info = adb.get_dump_info()
        if "Update all" in ui_info:
            u2.wait("Update all")
            time_out = 600
            counter = 0
            while counter < time_out:
                adb.uiautomator_dump()
                ui_text = adb.get_dump_info()
                if "No updates available" in ui_text:
                    logging.info("Update apps finished, return home")
                    close_app_return_home(GOOGLE_PLAY_PACKAGE)
                    return True
                if "Update all" in ui_text:
                    u2.wait("Update all")
                time.sleep(20)
                counter += 20
    logging.info("May open update failed!")
    return False


def check_privacy(package):
    adb.shell(f"monkey -p {package} 1")
    time.sleep(5)
    adb.uiautomator_dump()
    res = adb.get_dump_info()
    if "text=\"ACKNOWLEDGE\"" in res:
        u2.wait("ACKNOWLEDGE")
        time.sleep(3)
        adb.uiautomator_dump()
        res = adb.get_dump_info()
        if "text=\"Allow\"" in res:
            u2.wait("Allow")
    adb.shell(f"am force-stop {package}")
    adb.home()

