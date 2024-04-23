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
from collections import Counter

import pytest
from past.builtins import basestring

from lib.common import config_yaml
from lib.common.system.ADB import ADB
from util.errors import Errors


class Wifi(ADB):
    AML_WIFI_ADD_NETWORK = "wpa_cli -i {} add_network"
    AML_WIFI_REMOVE_NETWORK = "wpa_cli -i {} remove_network"
    AML_WIFI_DISABLE_NETWORK = "wpa_cli -i {} disable_network"
    AML_WIFI_ENABLE_NETWORK = "wpa_cli -i {} enable_network 0"
    AML_WIFI_GET_NETWORK = "wpa_cli -i {} get_network"
    AML_WIFI_SET_NETWORK = "wpa_cli -i {} set_network"
    AML_WIFI_CONNECT_NETWORK = "wpa_cli -i {} select_network"
    AML_WIFI_SAVE_CONFIG = "wpa_cli -i {} save_config"
    AML_WIFI_DISCONNECT_NETWORK = "wpa_cli -i {} disconnect"
    AML_WIFI_GET_NETWORK_STATUS = "wpa_cli -i {} status"
    AML_WIFI_LIST_NETWORK = "wpa_cli -i {} list_networks"
    AML_WIFI_IFCONFIG_IP = "ifconfig {} {}"
    AML_WIFI_IP_RULE = "ip rule add from all lookup main"
    AML_WIFI_SET_DNS = "ndc resolver setnetdns {} {} {}"
    AML_WIFI_SET_VIA = "ip route add default dev {} via {}"

    AML_WIFI_START_WPA = "start wpa_supplicant"
    AML_STOP_WPA_SUPPLICANT = "killall wpa_supplicant"

    RE_ADDNETWORK_ERROR = re.compile("FAIL")
    RE_CONNECTED = re.compile("wpa_state=COMPLETED")
    RE_GET_SSID = "(?<=)([0-9]+)(.*)([0-1])(.*)(CURRENT|ENABLED|DISABLED|UPDATED)"

    # These 4 constants are being used while checking
    # profile existence after add_network
    SECURITY_MODE_OPEN = "Open"
    SECURITY_MODE_WEP = "Wep"
    SECURITY_MODE_WPA2 = "Wpa2"
    SECURITY_MODE_EAP = "Eap"
    SECURITY_MODE_WPA = "WPA"

    _instance = None  # used to create singleton object at upper layers

    NETWORK_WAIT_TIMEOUT = 90

    def __init__(self):
        # self.device = device
        # statistics information
        ADB.__init__(self, 'wifi', unlock_code="", stayFocus=True)
        self._stats = dict()

    def _run_wpa_cli_cmd(self, cmd, msg="", timeout=10):
        """Helper function to run a wpa_cli command

                Args:
                    cmd (str): wpa_cli command to run
                    msg (str, optional) : message to log before running wpa_cli
                    timeout (int, optional): wait time for this method to finish

                Returns:
                    str: stdout + stderr from cmd

                Raises:
                    * TypeError : if incompatible cmd is supplied
                """
        if not (cmd and isinstance(cmd, basestring)):
            raise TypeError("Must supply a cmd(non-empty str)")

        if msg:
            logging.info(msg)

        logging.debug("Invoking command %s" % cmd)
        _, output = self.run_shell_cmd(cmd, timeout)
        logging.debug("Output is %s" % output)

        return output

    def is_connected_to_network(self, interface, ssid=None, timeout=15):
        """Helper function to check if device is connected to an AP.

        Args:
            timeout (int, optional): wait time for this method to finish
            ssid (str, optional): provide ssid for the AP you want to connect

        Returns:
            bool : True if device is connected to an AP, false otherwise

        Raises:
            TypeError : if incompatible ssid is provided
        """
        if ssid and not isinstance(ssid, basestring):
            raise Errors.TaskConfigError("Must supply a ssid in str format")

        self.root()
        msg = "Checking WPA status"

        status = self._run_wpa_cli_cmd(self.AML_WIFI_GET_NETWORK_STATUS.format(interface), msg, timeout)
        # conn_info = self._run_wpa_cli_cmd(self.ACE_CLI_WIFI_CONN_INFO,
        #                                   msg, timeout)
        logging.info(status)
        if self.RE_CONNECTED.search(status):
            if ssid and ssid not in status:
                return False
            else:
                return True
        # return False

    def connect(self, interface, ssid, psk=None, wep0=None, security=None, auth=None,
                hidden=0, add_network=True, save_profile=True, priority=None):
        """Helper function to connect device to a SSID

        Args:
            ssid (str) : Provide SSID of the AP
            psk (str, optional): Provide PSK of the AP for WPA2AES/TKIP
                                 security
            wep0 (str, optional): Provide WEP key for WEP security
            security (str, optional): security type PSK/WEP/TKIP
            auth (str, optional): authentication value of the profile
            hidden (int, optional): describes hidden profile
                                    1: hidden and 0: not hidden
            add_network (bool, optional):
                     if true adds the profile/else doesn't
            save_profile (bool, optional):
                     if True saves the added profile else doesn't
            priority (int, optional): priority value of a profile

        Raises:
            WifiError : If failed to connect
        """

        logging.info("Trying to connect to AP <%s>" % ssid)
        id = None
        stat_start = time.time()
        if add_network:
            id = self.wifi_add_network(interface, ssid, psk=psk, wep0=wep0,
                                       security=security, auth=auth,
                                       hidden=hidden,
                                       save_profile=save_profile, priority=priority)

        self._run_wpa_cli_cmd("%s %s" % (self.AML_WIFI_CONNECT_NETWORK.format(interface), id),
                              "Connecting to network")
        end_time = time.time() + self.NETWORK_WAIT_TIMEOUT

        while time.time() <= end_time:
            if self.is_connected_to_network(interface, ssid):
                self._stats["connect_time"] = time.time() - stat_start
                return
            time.sleep(2)
        raise Errors.WifiError("Failed to connect to <%s>" % ssid)

    def wifi_disconnect_network(self, interface):
        """Helper function to disconnect device from a SSID

        Raises:
            WifiError : if failed to disconnect from network
        """
        stat_start = time.time()
        self._run_wpa_cli_cmd("%s" % (self.AML_WIFI_DISCONNECT_NETWORK.format(interface)),
                              "Disconnecting from network")
        end_time = time.time() + self.NETWORK_WAIT_TIMEOUT
        while time.time() <= end_time:
            if not self.is_connected_to_network(interface=interface):
                self._stats["disconnect_time"] = time.time() - stat_start
                return
            time.sleep(2)
        raise Errors.WifiError("Failed to disconnect from network")

    def wifi_get_profile_list(self, interface, status=None):
        """Helper function to get all wifi profiles

        Args:
            status (str, optional): Fetch with particular status
                      CURRENT|ENABLED|DISABLED|UPDATED

        Returns:
            list : SSID list of profiles or empty list if none found
        """
        profile_list = []
        try:
            device_wifi_profile = self._run_wpa_cli_cmd(
                self.AML_WIFI_LIST_NETWORK.format(interface), "Get wifi config", timeout=20)
            logging.info("wifi config is %s" % device_wifi_profile)
            device_wifi_profile_list = re.findall(self.RE_GET_SSID, device_wifi_profile.strip())
            if device_wifi_profile_list:
                for profile in device_wifi_profile_list:
                    if status:
                        if profile[3] == status:
                            profile_list.append(profile[1].strip())
                            break
                    else:
                        profile_list.append(profile[1].strip())
        except Exception:
            logging.debug("Cannot retrieve profile list")
        return profile_list

    def wifi_add_network(self, interface, ssid, psk=None, wep0=None, security=None,
                         auth=None, hidden=0, save_profile=True,
                         priority=None, timeout=10):
        """Helper function to add network SSID to device

        Args:
            ssid (str): Provide SSID of the AP
            psk (str, optional): Provide PSK of the AP
            wep0 (str, optional): Provide psk for wep security
            security (str, optional): security type PSK/WEP/TKIP
            auth (str, optional): authentication value of the profile
            hidden (int, optional): is SSID hidden or no
            save_profile (bool, optional):
                     if True saves the added profile else doesn't
            priority (int, optional): priority value of a profile
            timeout (int, optional): timeout in seconds for cmd

        Raises:
            TypeError : If incompatible ssid is provided
            WifiError : If failed to add or other security related errors
        """
        logging.info("Input values -{} {} {} {}".format(ssid, psk, wep0,
                                                        hidden))
        cmd = ""
        if not (ssid and isinstance(ssid, basestring)):
            raise Errors.TaskConfigError("Must supply a ssid(non-empty str)")

        cmd = self.AML_WIFI_ADD_NETWORK.format(interface)
        id = self._run_wpa_cli_cmd(
            cmd, "Add network", timeout=timeout)
        if re.search(self.RE_ADDNETWORK_ERROR, id):
            raise Errors.WifiError(
                "Failed to add network with reason - {}".format(id))

        setcmd = self.AML_WIFI_SET_NETWORK.format(interface)
        logging.debug(setcmd)
        if wep0:
            wepcmd = "%s %s ssid \"\\\"%s\"\\\"" % (setcmd, id, ssid)
            logging.debug(wepcmd)
            output = self._run_wpa_cli_cmd(wepcmd, "set network ssid", timeout=timeout)
            if re.search(self.RE_ADDNETWORK_ERROR, output):
                raise Errors.WifiError("Failed to set network ssid with reason - {}".format(output))
            wepcmd = "%s %s key_mgmt NONE" % (setcmd, id)
            logging.debug(wepcmd)
            output = self._run_wpa_cli_cmd(wepcmd, "set network key_mgmt", timeout=timeout)
            if re.search(self.RE_ADDNETWORK_ERROR, output):
                raise Errors.WifiError("Failed to set network key_mgmt with reason - {}".format(output))
            wepcmd = "%s %s auth_alg OPEN SHARED" % (setcmd, id)
            logging.debug(wepcmd)
            output = self._run_wpa_cli_cmd(wepcmd, "set network auth_alg", timeout=timeout)
            if re.search(self.RE_ADDNETWORK_ERROR, output):
                raise Errors.WifiError("Failed to set network auth_alg with reason - {}".format(output))
            wepcmd = "%s %s wep_key0 %s" % (setcmd, id, str(wep0))
            logging.debug(wepcmd)
            output = self._run_wpa_cli_cmd(wepcmd, "set network wep_key0", timeout=timeout)
            if re.search(self.RE_ADDNETWORK_ERROR, output):
                raise Errors.WifiError("Failed to set network wep_key0 with reason - {}".format(output))
        elif security == 'Open':
            wepcmd = "%s %s ssid \"\\\"%s\"\\\"" % (setcmd, id, ssid)
            logging.debug(wepcmd)
            output = self._run_wpa_cli_cmd(wepcmd, "set network ssid", timeout=timeout)
            if re.search(self.RE_ADDNETWORK_ERROR, output):
                raise Errors.WifiError("Failed to set network ssid with reason - {}".format(output))
            wepcmd = "%s %s key_mgmt NONE" % (setcmd, id)
            logging.debug(wepcmd)
            output = self._run_wpa_cli_cmd(wepcmd, "set network key_mgmt", timeout=timeout)
            if re.search(self.RE_ADDNETWORK_ERROR, output):
                raise Errors.WifiError("Failed to set network key_mgmt with reason - {}".format(output))
        elif security == 'Wpa' or security == 'Wpa2':
            wepcmd = "%s %s ssid \"\\\"%s\"\\\"" % (setcmd, id, ssid)
            logging.debug(wepcmd)
            output = self._run_wpa_cli_cmd(wepcmd, "set network ssid", timeout=timeout)
            if re.search(self.RE_ADDNETWORK_ERROR, output):
                raise Errors.WifiError("Failed to set network ssid with reason - {}".format(output))
            # wepcmd = "%s %s key_mgmt WPA-PSK" % (setcmd, id)
            # logging.debug(wepcmd)
            # output = self._run_wpa_cli_cmd(wepcmd, "set network key_mgmt", timeout=timeout)
            # if re.search(self.RE_ADDNETWORK_ERROR, output):
            #     raise Errors.WifiError(
            #         "Failed to set network key_mgmt with reason - {}".format(output))
            # wepcmd = "%s %s psk \"%s\"" % (setcmd, id, psk)
            # logging.debug(wepcmd)
            # output = self._run_wpa_cli_cmd(wepcmd, "set network key_mgmt", timeout=timeout)
            # if re.search(self.RE_ADDNETWORK_ERROR, output):
            #     raise Errors.WifiError(
            #         "Failed to set network key_mgmt with reason - {}".format(output))
            wepcmd = "%s %s psk \"\\\"%s\"\\\"" % (setcmd, id, psk)
            logging.debug(wepcmd)
            output = self._run_wpa_cli_cmd(wepcmd, "set network psk", timeout=timeout)
            if re.search(self.RE_ADDNETWORK_ERROR, output):
                raise Errors.WifiError("Failed to set network ssid with reason - {}".format(output))
        else:
            raise Errors.WifiError("Failed to add network with reason - not supported")

        # hiddencmd = "%s %s scan_ssid %s" % (setcmd, id, hidden)
        # logging.debug(hiddencmd)
        # output = self._run_wpa_cli_cmd(hiddencmd, "set hidden", timeout=timeout)
        # if re.search(self.RE_ADDNETWORK_ERROR, output):
        #     raise Errors.WifiError(
        #         "Failed to set network hidden with reason - {}".format(output))

        logging.info("The profile added successfully.")

        # if save_profile:
        #     self.wifi_save_config(interface)

        return id

    def wifi_save_config(self, interface, timeout=10):
        """Helper function to save network config

        Args:
            timeout (int, optional): timeout in seconds for cmd
        """
        self._run_wpa_cli_cmd(self.AML_WIFI_SAVE_CONFIG.format(interface), "Saving config", timeout=timeout)

    def wifi_remove_all_network(self, interface):
        """Helper function to remove all network in device

        Returns:
            Boolean : True if removed all networks else False
        """
        # retry = 3
        # while(retry > 0):
        #     existing_profiles = self.wifi_get_profile_list()
        #     logging.info(
        #         "Number of profiles exist on device-{}".format(
        #             len(existing_profiles)))
        #     if len(existing_profiles) > 0:
        #         for profile in existing_profiles:
        #             self.wifi_remove_network(profile)
        #     else:
        #         logging.info("No stored profiles to remove on device")
        #         return True
        #     retry -= 1
        # else:
        #     logging.error("Still unable to remove profiles on device")
        #     return False
        t = "%s all" % (self.AML_WIFI_REMOVE_NETWORK.format(interface))
        output = self._run_wpa_cli_cmd(t)
        # "Removing All Network from Device")
        time.sleep(1)
        # self.wifi_save_config(interface)
        # time.sleep(1)

    def wifi_disable_all(self, interface, timeout=10):
        """Helper function to disable wifi network in device

        Args:
            timeout (int, optional) : time in seconds
        """
        self._run_wpa_cli_cmd("%s all" % (self.AML_WIFI_DISABLE_NETWORK.format(interface)),
                              "Disable All Network",
                              timeout=timeout)

    def set_dns_via(self, interface, ip, dns, via, timeout=10):
        cmd = ""
        cmd = self.AML_WIFI_IFCONFIG_IP.format(interface, ip)
        logging.info(cmd)
        self._run_wpa_cli_cmd(cmd, "set wifi ip", timeout=timeout)

        cmd = self.AML_WIFI_IP_RULE
        logging.info(cmd)
        self._run_wpa_cli_cmd(cmd, "set rule", timeout=timeout)

        cmd = self.AML_WIFI_SET_DNS.format(interface, via, dns)
        logging.info(cmd)
        self._run_wpa_cli_cmd(cmd, "set dns", timeout=timeout)

        cmd = self.AML_WIFI_SET_VIA.format(interface, via)
        logging.info(cmd)
        self._run_wpa_cli_cmd(cmd, "set via", timeout=timeout)


class WifiTestApk(ADB):
    PACKAGE = 'com.amlogic.wifitest'
    WIFITEST_APK = 'WifiTests-debug.apk'
    ACTIVITY_NAME_TUPLE = 'com.amlogic.wifitest', '.MainActivity'
    SETTING_NAME_TUPLE = ('com.google.android.permissioncontroller',
                          'com.android.permissioncontroller.permission.ui.ManagePermissionsActivity ')

    SETTING_ACTIVITY_TUPLE = 'com.android.tv.settings', '.MainSettings'
    MORE_SETTING_ACTIVITY_TUPLE = 'com.droidlogic.tv.settings', '.more.MorePrefFragmentActivity'

    # iperf 相关命令
    IPERF_SERVER = 'iperf -s -w 4m -i 1'
    IPERF_CLIENT_REGU = 'iperf -c {} -w 4m -i 1 -t 60 -P{}'
    IPERF_MULTI_SERVER = 'iperf -s -w 4m -i 1 {}&'
    IPERF_MULTI_CLIENT_REGU = './data/iperf -c {} -w 4m -i 1 -t 60 -p {}'

    IPERF3_SERVER = 'iperf3 -s -i 1&'
    IPERF3_CLIENT_TCP_REGU = 'iperf3 -c {} -t 60 -P {}'
    IPERF3_CLIENT_UDP_REGU = 'iperf3 -c {} -i 1 -t 60 -u -b 120M -l63k -P {}'

    IPERF3_KILL = '[ -n "`ps -A|grep iperf`" ] && killall -9 iperf3 || echo no'
    # IPERF_KILL = '[ -n "`ps -A|grep iperf`" ] && killall -9 iperf || echo no'
    IPERF_KILL = 'killall -9 iperf'
    IW_LINNK_COMMAND = 'iw wlan0 link'

    CMD_WIFI_CONNECT = 'cmd wifi connect-network {} {} {}'
    CMD_WIFI_CONNECT_OPEN = 'cmd wifi connect-network {} open'
    CMD_WIFI_HIDE = ' -h'

    WIFI_CONNECT_PACKAGE = 'com.example.wifiConnect'
    WIFI_CONNECT_ACTIVITY = f'am start -n {WIFI_CONNECT_PACKAGE}/.MainActivity'
    WIFI_CONNECT_COMMAND_REGU = 'am start -n com.example.wifiConnect/.MainActivity -e ssid {}'
    WIFI_CONNECT_PASSWD_REGU = ' -e passwd {}'
    WIFI_CONNECT_HIDE_SSID_REGU = ' --ez hide_ssid true -e type {}'
    WIFI_DISCONNECT_COMMAND = WIFI_CONNECT_ACTIVITY + ' --ez disconnect true'
    WIFI_CHANGE_STATUS_REGU = ' -e wifi_status {}'
    WIFI_FORGET_WIFI_STR = ' --ez forget true'
    CMD_WIFI_LIST_NETWORK = "cmd wifi list-networks |grep -v Network |awk '{print $1}'"
    CMD_WIFI_FORGET_NETWORK = 'cmd wifi forget-network {}'

    MCS_RX_GET_COMMAND = 'iwpriv wlan0 get_last_rx'
    MCS_RX_CLEAR_COMMAND = 'iwpriv wlan0 clear_last_rx'
    MCS_TX_GET_COMMAND = 'iwpriv wlan0 get_rate_info'
    MCS_TX_KEEP_GET_COMMAND = "'for i in `seq 1 10`;do iwpriv wlan0 get_rate_info;sleep 6;done ' & "
    POWERRALAY_COMMAND_FORMAT = './tools/powerRelay /dev/tty{} -all {}'

    GET_COUNTRY_CODE = 'iw reg get'
    SET_COUNTRY_CODE_FORMAT = 'iw reg set {}'

    def __init__(self):
        ADB.__init__(self, 'wifi', unlock_code="", stayFocus=False)
        self.wifi_cmd = ('am instrument -w {} -e class com.amlogic.wifitest.Wifitests#test{} '
                         'com.amlogic.wifitest/android.support.test.runner.AndroidJUnitRunner')
        # self.get_wifiApk = self.res_manager.get_target('apk/WifiTests-debug.apk')
        self.get_iperf = self.res_manager.get_target('wifi/iperf', source_path='wifi/iperf')
        # self.get_iperf = self.res_manager.get_target('apk/iperf3.apk')
        self.p_config_wifi = config_yaml.get_note('conf_wifi_and_bluetooth')

    def check_ping_host(self, interface):
        self.root()
        time.sleep(5)
        for _ in range(3):
            hostname = "www.sohu.com"
            logging.info(f'----start to ping host {hostname}')
            if self.ping(interface, hostname):
                return True
            logging.info('ping sohu.com failed')
            # return False
        for _ in range(3):
            hostname = "www.google.com"
            logging.info(f'----start to ping host {hostname}')
            if self.ping(interface, hostname):
                return True
            logging.info('ping google.com failed')
            return False

    def check_wifiApk_exist(self):
        return True if self.PACKAGE in self.checkoutput('pm list packages') else False

    def wifi_setup(self):
        if not self.check_wifiApk_exist():
            assert self.install_apk("apk/" + self.WIFITEST_APK)
        self.get_permissions()
        self.clear_logcat()

    def push_config(self):
        project = pytest.target.get("prj")
        path = f'config/config_{project}.json'
        logging.info(path)
        self.push(path, "/sdcard/config_wifi.json")

    def get_permissions(self):
        self.clear_logcat()
        self.run_shell_cmd(self.wifi_cmd.format('', 'Check_permissions'))
        result = self.logcat_save("permissions")
        if 'the permission not granted' in result:
            self.start_activity(*self.ACTIVITY_NAME_TUPLE)
            time.sleep(2)
            if self.wait_element("Allow WifiTests to access this device’s location?", "text"):
                self.wait_and_tap('While using the app', "text")
                if self.wait_element("Allow WifiTests to access photos, media, and files on your device?", "text"):
                    self.wait_and_tap("Allow", "text")
                if self.build_version == "30" or self.build_version == "31":
                    self.start_activity(*self.SETTING_NAME_TUPLE, intentname="android.intent.action.MANAGE_PERMISSIONS")
                    for _ in range(4):
                        self.keyevent(20)
                        if self.wait_and_tap("Location", "text"):
                            break
                        else:
                            self.wait_and_tap("Other permissions", "text")
                            self.wait_and_tap("Location", "text")
                            self.wait_and_tap("Show system apps", "text")
                    if self.wait_element("WifiTests", "text"):
                        self.wait_and_tap("WifiTests", "text")
                    else:
                        for _ in range(20):
                            self.keyevent(20)
                            if self.wait_and_tap("WifiTests", "text"):
                                break
                    self.wait_and_tap("Allow all the time", "text")
                    self.app_stop(self.SETTING_NAME_TUPLE[0])
            if self.wait_element("Allow WifiTests to access photos, media, and files on your device?", "text"):
                self.wait_and_tap("Allow", "text")
            self.app_stop(self.ACTIVITY_NAME_TUPLE[0])

    def get_wifi_connect_permission(self):
        self.checkoutput(self.WIFI_CONNECT_ACTIVITY)
        time.sleep(3)
        self.wait_and_tap('While using the app', 'text')
        self.wait_and_tap('Allow', 'text')
        self.wait_and_tap('Allow', 'text')
        self.home()
        self.app_stop(self.WIFI_CONNECT_PACKAGE)

    def wifi_connect(self, ssid, psk, hidden, security):
        if hidden == "true":
            ''''in config.json security should be set : PSK, WEP, NONE OR EAP'''
            cmd = 'WifiConnectHiddenSsid'
            argument = f"-e SSID {ssid} -e PASSWD {psk}  -e SECURITY {security}"
        else:
            cmd = 'WifiConnectNotHiddenSsid'
            argument = f"-e SSID {ssid} -e PASSWD {psk}"
        logging.info(self.wifi_cmd.format(argument, cmd))
        self.run_shell_cmd(self.wifi_cmd.format(argument, cmd))

    def wifi_disconnect(self):
        self.run_shell_cmd(self.wifi_cmd.format('', 'WifiDisconnect'))
        logging.info('wifi disconnect')

    def wifi_state_on(self):
        self.clear_logcat()
        self.run_shell_cmd(self.wifi_cmd.format('', 'ChangeWifiState_on'))

    def wifi_state_off(self):
        self.clear_logcat()
        self.run_shell_cmd(self.wifi_cmd.format('', 'ChangeWifiState_off'))

    def check_status(self, type):
        result = self.logcat_save(type)
        if type == 'incorrectPsk':
            if 'wifi psk not right' in result:
                logging.info('wifi not connected,because incorrect psk')
                return True
        else:
            if 'The ssid is connected status' in result:
                logging.info('wifi connected')
                res = re.findall(r'Ip address is:(\d*.\d*.\d*.\d*)', result, re.S)[0]
                if res != '0.0.0.0':
                    logging.info('wlan ip is:{}'.format(res))
                    return True

    def logcat_save(self, type):
        name = type + '.log'
        log, logcat_file = self.save_logcat(name, 'WifiTest')
        time.sleep(7)
        self.stop_save_logcat(log, logcat_file)
        with open(logcat_file.name, 'r') as f:
            result = f.read()
            return result

    def power_relay(self, powerRelay_port, power_state):
        p_conf_wifi_powerRelay = self.p_config_wifi['powerRelay'][powerRelay_port]
        os.system(self.POWERRALAY_COMMAND_FORMAT.format(p_conf_wifi_powerRelay, power_state))
        logging.info(self.POWERRALAY_COMMAND_FORMAT.format(p_conf_wifi_powerRelay, power_state))

    def connect_check(self, type, ssid, psk=None, hidden='false', security=''):
        self.wifi_connect(ssid, psk, hidden, security)
        time.sleep(3)
        assert self.check_status(type)
        if type == "incorrectPsk":
            assert not self.check_ping_host('wlan0')
        else:
            assert self.check_ping_host('wlan0')

    def check_reconnect(self):
        self.clear_logcat()
        self.run_shell_cmd(self.wifi_cmd.format('', 'CheckConnectInfo'))
        result = self.logcat_save('reconnect')
        if 'The ssid is connected status' in result:
            logging.info('the wifi ssid keep connecting status')
            assert self.check_ping_host('wlan0')
            return True

    def get_connectedInfo(self):
        self.clear_logcat()
        self.run_shell_cmd(self.wifi_cmd.format('', 'GetConnectedInfo'))
        result = self.logcat_save('connected_info')
        if 'Current wifi connected ssid is ' in result:
            ssid = re.findall(r'Current wifi connected ssid is "(.*?)"', result, re.S)[0]
            logging.info(f'"{ssid}" ssid is connected status')
            if self.check_ping_host('wlan0'):
                return ssid

    def run_vtscts(self, sh_name, case_filename, file_directory, tools_directory):
        os.system("chmod +x " + sh_name)
        cmd = "./" + sh_name + " " + case_filename + " " + file_directory + " " + tools_directory
        logging.info(cmd)
        os.system(cmd)

    def check_wifi_driver(self):
        self.clear_logcat()
        file_list = self.run_shell_cmd("ls /vendor/lib/modules")[1]
        if 'vlsicomm.ko' in file_list:
            logging.info('Wifi driver is exists')
            return True
        else:
            logging.info('Wifi driver is not exists')
            return False

    def get_mcs_rx(self):
        try:
            self.checkoutput(self.MCS_RX_GET_COMMAND)
            mcs_info = self.checkoutput(self.DMESG_COMMAND)
            # logging.debug(mcs_info)
            result = re.findall(r'RX rate info for \w\w:\w\w:\w\w:\w\w:\w\w:\w\w:(.*?)Last received rate', mcs_info, re.S)
            result_list = []
            for i in result[0].split('\n'):
                if ':' in i:
                    rate = re.findall(r'(\w+\.?\/?\w+)\s+:\s+\d+\((.*?)\)', i)
                    result_list.append(rate[0])
            result_list = [(i[0], float(i[1][:-1].strip())) for i in result_list]

            result_list.sort(key=lambda x: x[1], reverse=True)
            logging.info(result_list)
            return '|'.join(['{}:{}%'.format(i[0], i[1]) for i in result_list[:3]])
        except Exception as e:
            return 'mcs_rx'

    def get_mcs_tx(self):
        try:
            mcs_info = self.checkoutput(self.DMESG_COMMAND)
            # logging.debug(mcs_info)
            result = re.findall(r'TX rate info for \w\w:\w\w:\w\w:\w\w:\w\w:\w\w:(.*?)MPDUs AMPDUs AvLen trialP', mcs_info,
                                re.S)
            result_list = []
            for i in result:
                for j in i.split('\n'):
                    if ' T ' in j:
                        temp = re.findall(r'(MCS\d+\/\d+)', j)
                        result_list.append(temp[0])
                        break
            counts = Counter(result_list)
            logging.info(counts)
            return max(counts.keys(), key=counts.get)
        except Exception as e:
            return 'mcs_tx'

    def get_tx_bitrate(self):
        '''
        return tx bitrate
        @return: rate (str)
        '''
        try:
            self.root()
            result = self.checkoutput(self.IW_LINNK_COMMAND)
            rate = re.findall(r'tx bitrate:\s+(.*?)\s+MBit\/s',result,re.S)[0]
            return rate
        except Exception as e:
            return 'Data Error'