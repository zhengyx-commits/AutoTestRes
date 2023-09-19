#!/usr/bin/env python
# Copyright 2021 Amlogic.com, Inc. or its affiliates. All rights reserved.
#
# AMLOGIC PROPRIETARY/CONFIDENTIAL
#
# You may not use this file except in compliance with the terms and conditions
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMLOGIC SPECIFICALLY
# DISCLAIMS, WITH RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS,
# IMPLIED, OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
#
import logging
import os
import re
import time

import pytest

from lib.common import config_yaml

from .ADB import ADB

ACTIVITY_NAME = "com.android.tv.settings.MainSettings"
TV_SETTING_APP = "com.android.tv.settings"
TV_SETTING_NAME = "TvSettings.apk"
TIMEOUT = 10
WIFI_ON = "svc wifi enable"
WIFI_OFF = "svc wifi disable"
NETWORK_ELEMENT = "Network & Internet"
WIFI_CONNECT_WAIT_TIMEOUT = 30
ENTER_NETWORK_STR = "Enter Network"
FACTORY_RESET_ACTIVITY_NAME = '.device.storage.ResetActivity'


class TvSettingApp(ADB):
    """
    FFS Test App (Android)
    """

    _instance = None  # used to create singleton object at upper layers

    def __init__(self):
        ADB.__init__(self, name="TvSettingApp", unlock_code="", logdir=pytest.result_dir, stayFocus=False)
        self.app_name = TV_SETTING_APP
        self._path = os.getcwd()
        self.apk_exist = self.check_tvsetting_apk_exist()
        self.wifi_initial_state = False
        self.check_ping = ''
        # self.project = pytest.config.get('project', {})
        self.p_config_amazon = config_yaml.get_note('conf_tvsetting')
        self.p_conf_amazon_project = self.p_config_amazon['project']
        self.get_apk = self.res_manager.get_target('apk/TvSettings.apk')
        self.p_config_wifi = config_yaml.get_note('conf_wifi')

    def check_tvsetting_apk_exist(self):
        rc, out = self.run_shell_cmd('pm list packages', TIMEOUT)
        return TV_SETTING_APP in out
        packagelist = out.split()
        # if len(packagelist) > 0:
        #     for item in packagelist:
        #         logging.debug(item)
        #         if TV_SETTING_APP in item:
        #             return True
        #         else:
        #             continue
        #     return False
        # else:
        #     return False

    def check_wifi_initial_state(self):
        if self.find_element("Wi-Fi is turned off", "text"):
            self.wifi_initial_state = False
        else:
            self.wifi_initial_state = True

    def install_tvsetting(self):
        self.install_apk("apk/" + TV_SETTING_NAME)
        # self.start()
        # self.check_wifi_initial_state()
        # self.stop()

    def uninstall_tvsetting(self):
        cmd = ['uninstall', self.app_name]
        logging.debug(cmd)
        self.run_adb_cmd_specific_device(cmd, TIMEOUT)

    def wifi_on(self):
        # if not self.wifi_initial_state:
        # logging.debug(WIFI_ON)
        self.run_shell_cmd(WIFI_ON, TIMEOUT)

    def wifi_off(self):
        # if not self.wifi_initial_state:
        # logging.debug(WIFI_OFF)
        self.run_shell_cmd(WIFI_OFF, TIMEOUT)

    def start(self):
        logging.debug("Start TvSetting App")
        self.start_activity(self.app_name, ACTIVITY_NAME)

    def stop(self):
        logging.debug("Stop TvSetting App")
        self.app_stop(self.app_name)

    def change_language(self):
        logging.debug("Change language to English")
        cmd = f'monkey -p {self.app_name} 1'
        self.run_shell_cmd(cmd, TIMEOUT)
        time.sleep(2)
        x, y = self.find_and_tap("设备偏好设置", "text")
        if x == -1 and y == -1:
            logging.debug("not need to change language!")
            self.stop()
            return
        time.sleep(5)
        self.find_and_tap("语言", "text")
        time.sleep(5)
        self.find_and_tap("English (United States)", "text")
        time.sleep(5)
        self.stop()

    def check_status(self, ssid):
        logging.debug("Check WiFi Status")
        logging.info(ENTER_NETWORK_STR)
        self.find_and_tap(NETWORK_ELEMENT, "text")
        time.sleep(5)
        self.find_and_tap(ssid, "text")
        time.sleep(5)
        wifi_status = self.find_element("Connected", "text")
        if wifi_status:
            return True
        else:
            end = time.time() + WIFI_CONNECT_WAIT_TIMEOUT
            while (not wifi_status) and (time.time() < end):
                time.sleep(1)
                logging.info("find Connected status.")
                wifi_status = self.find_element("Connected", "text")
                logging.info("wifi_status = " + wifi_status)
                if wifi_status:
                    return True
            return False

    def connect_wifi(self, ssid, pwd, mode='Wpa2'):
        time.sleep(2)
        logging.info(ENTER_NETWORK_STR)
        self.find_and_tap(NETWORK_ELEMENT, "text")
        time.sleep(5)
        self.find_and_tap("Add new network", "text")
        time.sleep(5)
        logging.info("Focus ssid EditText")
        if self.p_conf_amazon_project == 'iptv_ref':
            self.enter()
            self.enter()
            time.sleep(2)
            self.back()
        if self.p_conf_amazon_project == 'ott_ref':
            logging.info('p_conf_amazon_project is ott')
        time.sleep(2)
        logging.info("Enter ssid")
        self.text(ssid)
        time.sleep(2)
        self.enter()
        time.sleep(2)
        if mode == 'Open':
            self.enter()
            # self.find_and_tap("None", "text")
        elif mode == 'Wep':
            self.keyevent("KEYCODE_DPAD_DOWN")
            time.sleep(2)
            self.enter()
            # time.sleep(2)
            # self.enter()
            # self.enter()
            time.sleep(2)
            self.back()
            time.sleep(2)
            logging.info("Enter password")
            self.text(pwd)
            time.sleep(2)
            self.enter()
        elif mode == 'Wpa' or mode == 'Wpa2':
            self.keyevent("KEYCODE_DPAD_DOWN")
            time.sleep(2)
            self.keyevent("KEYCODE_DPAD_DOWN")
            time.sleep(2)
            if self.p_conf_amazon_project == 'iptv_ref':
                self.enter()
                # time.sleep(2)
                # self.enter()
                # self.enter()
                time.sleep(2)
                self.back()
            if self.p_conf_amazon_project == 'ott_ref':
                self.keyevent("KEYCODE_DPAD_DOWN")
                time.sleep(2)
                self.enter()
            time.sleep(2)
            logging.info("Enter password")
            self.text(pwd)
            time.sleep(2)
            self.enter()
        else:
            # TODO : handle other wifi mode
            raise ValueError("No solution to deal with this situation")

        logging.info("Connecting to WiFi")
        load_screen = self.find_element(f"Connecting to {ssid}", "text")
        failure_screen = self.find_element(f"Couldn't find {ssid}", "text")
        end = time.time() + WIFI_CONNECT_WAIT_TIMEOUT
        while (load_screen and not failure_screen) and (time.time() < end):
            time.sleep(1)
            load_screen = self.find_element("CONNECTING_TO_DEVICE", "text")
            failure_screen = self.find_element("Failure", "text")
        if failure_screen:
            logging.error(f"cant connect to wifi {ssid}.")
            self.screenshot("cant_connect_to_wifi")
            raise ConnectionError("connect wifi failure.")

    def disconnect_wifi(self, ssid):
        logging.info(ENTER_NETWORK_STR)
        self.find_and_tap(NETWORK_ELEMENT, "text")
        time.sleep(5)
        self.find_and_tap(ssid, "text")
        time.sleep(5)
        self.find_and_tap("Forget network", "text")
        time.sleep(2)
        self.enter()
        time.sleep(2)
        self.enter()
        time.sleep(5)

    # as the same as ping of ADB()

    # def ping_host(self, interface, hostname="www.baidu.com",
    #               interval_in_seconds=1, ping_time_in_seconds=5,
    #               timeout_in_seconds=10, size_in_bytes=None):
    #     """Can ping the given hostname without any packet loss
    #
    #     Args:
    #         hostname (str, optional): ip or URL of the host to ping
    #         interval_in_seconds (float, optional): Time interval between
    #                                                pings in seconds
    #         ping_time_in_seconds (int, optional)  : How many seconds to ping
    #         timeout_in_seconds (int, optional): wait time for this method to
    #                                             finish
    #         size_in_bytes (int, optional): Ping packet size in bytes
    #
    #     Returns:
    #         dict: Keys: 'sent' and 'received', values are the packet count.
    #               Empty dictionary if ping failed
    #     """
    #     try:
    #         ping_output = {}
    #         if not (hostname and isinstance(hostname, str)):
    #             logging.error("Must supply a hostname(non-empty str)")
    #             return False
    #
    #         try:
    #             # ping_time_in_seconds = pytest.config.get("wifi")['ping_count']
    #             ping_time_in_seconds = self.p_config_wifi['wifi']['ping_count']
    #         except Exception as e:
    #             logging.error("ping_count config doesn't exist, so default value "
    #                           "is used")
    #         count = int(ping_time_in_seconds / interval_in_seconds)
    #         timeout_in_seconds += ping_time_in_seconds
    #         # Changing count based on the interval, so that it always finishes
    #         # in ping_time seconds
    #
    #         try:
    #             # ping_percentge = pytest.config.get("wifi")['ping_pass_percentage']
    #             p_conf_wifi_ping_pass_percentage = self.p_config_wifi['wifi']['ping_pass_percentage']
    #         except Exception as e:
    #             logging.error("ping_pass_percentage config doesn't exist, "
    #                           "so default value 0 is used")
    #             p_conf_wifi_ping_pass_percentage = 0
    #         ping_pass_percentage = int(count * p_conf_wifi_ping_pass_percentage * 0.01)
    #
    #         # if "rtos" in pytest.device.get_platform():
    #         #     hostname = "8.8.8.8"
    #         #     cmd = "%s %s %s" % (pytest.wifi.ACE_CLI_PING_RTOS, hostname,
    #         #                         count)
    #         # else:
    #         if size_in_bytes:
    #             cmd = "ping -i %s -I %s -c %s -s %s %s" % (
    #                 interval_in_seconds, interface, count, size_in_bytes, hostname)
    #         else:
    #             cmd = "ping -i %s -I %s -c %s %s" % (interval_in_seconds, interface, count, hostname)
    #         logging.info("Ping command: %s" % cmd)
    #         rc, output = self.run_shell_cmd(cmd, timeout=timeout_in_seconds)
    #         logging.info(output)
    #
    #         # if "serial" == self.device.PROTOCOL:
    #         #     if output:
    #         #         success_cnt = re.search('success=(.*?),', output).group(1)
    #         #         logging.info("Ping success count: %s" % (success_cnt))
    #         #         ping_output['transmitted'] = int(count)
    #         #         ping_output['received'] = int(success_cnt)
    #         #         ping_output['packet_loss'] = int(ping_output[
    #         #                                              'transmitted']
    #         #                                          - ping_output['received'])
    #         #         logging.info("Ping Stats Dictionary:-{}".format(ping_output))
    #         #         if ping_output['packet_loss'] <= count \
    #         #                 - ping_pass_percentage:
    #         #             return True
    #         # else:
    #
    #         RE_PING_STATUS = re.compile(
    #             r".*(---.+ping statistics ---\s+\d+ packets transmitted, \d+ received, "
    #             r"(?:\+\d+ duplicates, )?(\d+)% packet loss, time.+ms\s*?rtt\s+?"
    #             r"min/avg/max/mdev)\s+?=\s+?(\d+(\.\d+)?)/(\d+(\.\d+)?)/(\d+(\.\d+)?)"
    #             r"/(\d+(\.\d+)?)\s+?ms.*?")
    #         # group(1) - ping statistics
    #         # group(2) - packet loss
    #         # group(3) - rtt min
    #         # group(5) - rtt avg
    #         # group(7) - rtt max
    #         # group(9) - rtt mdev
    #         match = RE_PING_STATUS.search(output)
    #         logging.info(match)
    #         ping_output['duplicates'] = 0
    #         if match:
    #             stats = match.group(1).split('\n')[1].split(',')
    #             ping_output['transmitted'] = int(
    #                 stats[0].split()[0].strip())
    #             ping_output['received'] = int(stats[1].split()[0].strip())
    #             if 'duplicates' in match.group(1):
    #                 ping_output['duplicates'] = int(
    #                     stats[2].split()[0].strip().split('+')[1])
    #             ping_output['packet_loss'] = int(match.group(2))
    #             logging.info("Ping Stats Dictionary:-{}".format(ping_output))
    #             expected_pkt_loss = int(((count - ping_pass_percentage) /
    #                                      count) * 100)
    #             if ping_output['packet_loss'] <= expected_pkt_loss:
    #                 return True
    #             else:
    #                 return False
    #     except Exception as e:
    #         logging.error("Problem in executing ping - %s" % e)
    #     # return False

    def check_ping_host(self, case_name, interface):
        self.root()
        time.sleep(5)
        for _ in range(3):
            if self.ping(interface):
                logging.info(f'{case_name} ping baidu.com is ok')
                return True
            else:
                logging.info(f'{case_name} ping baidu.com failed')

    def tvSet_setup(self):
        if not self.apk_exist:
            self.install_tvsetting()
        self.change_language()
        self.start()
        self.wifi_on()

    def connect_and_check(self, ssid, pwd):
        self.connect_wifi(ssid, pwd)
        time.sleep(20)
        self.back()
        if self.check_status(ssid):
            logging.info('wifi connected,start to check ping host')
            self.check_ping = self.check_ping_host("wifi", "wlan0")
            self.keyevent('KEYCODE_DPAD_DOWN')
            self.back()
            self.back()
            self.disconnect_wifi(ssid)
            return True
        else:
            logging.info('wifi connect failed')
