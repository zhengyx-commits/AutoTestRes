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
import re

import pytest
from past.builtins import basestring

from .ADB import ADB
from lib import get_device
from .TvSetting import TvSettingApp


class Ethernet:

    def __init__(self, device):
        self.device = device
        self.ssh = None

    def is_supported(self, command):
        """ Validates that the given command is executable

        Args:
            command: the command to be checked

        Optional Args:
            None

        Returns:
            Boolean: True if the given command is executable
                     False if the given command is not executable

        Raises:
            Exception if unexpected errors occur
        """
        if "linux" in self.device.get_platform() or "Android" in self.device.get_platform():
            output = self._send_cmd("which {}".format(command))
        else:
            logging.error("executable command does not exist on {}"
                          .format(self.device.get_platform))
            return False

        return True if output.find(command) != -1 else False

    def _send_cmd(self, cmd, timeout=1):
        """ Helper function to send a hal wifi cli command to the device

        Args:
            cmd (str): wifi dpk cli command to run

        Optional Args:
            timeout (int): wait time for the command to fi nish

        Returns:
            str: stdout + stderr from cmd

        Raises:
            TypeError if input with empty cmd
            Exception if unexpected errors occur
        """
        if not (cmd and isinstance(cmd, basestring)):
            raise TypeError("Must supply a cmd(non-empty str)")

        try:
            _, output = self.device.shell(cmd, timeout)
            logging.debug("Output is %s" % output)
            return output
        except Exception as e:
            logging.error("Error in sending cmd {0}. Reason: {1}".format(cmd, e))
            raise e

    def run_iperf(self, role='server', time=10, dest="", tcp=False,
                  bandwith="100M", tos=0):
        """ run iperf

         Args:
            None

        Optional Args:
            role (str): run in 'server' mode or 'client' mode
            time (int): time in seconds to receive or transmit traffics
            dest (str): destination (iperf server) IP address
            tcp (Boolean): True to use TCP traffic, False to use UDP traffic
            bandwidth (str): Target bandwidth
            tos (int): value of tos field in IP header Normally the value is
            mapped to access category (0xC0, 0xB8, 0xE0 -> AC_VO, 0x80
            0xA0, 0x88 -> AC_VI, 0x0, 0x60 -> AC_BE, 0x40, 0x20 -> AC_BK)

        Returns:
            None

        Raises:
            None
        """
        cmds = ['iperf']
        RE_LOST_DATAGRAMS = re.compile(r"(\()(\d+)(%\))")
        RE_MAX_DATAGRAMS = re.compile(r"(\d+\.?\d+)( Mbits/sec)")

        if role == 'server':
            if not tcp:
                cmds.append('-u')
            cmds.append('-s')
        elif role == 'client':
            cmds.append('-c {}'.format(dest))
            if not tcp:
                cmds.append('-u -b {}'.format(bandwith))
        else:
            raise ValueError("role ({}) is not supported".format(role))
        try:
            logging.debug(cmds)
            output = self._send_cmd("{}".format(" ".join(cmds)), time + 2)
            logging.debug(output)
            if tcp:
                match = RE_MAX_DATAGRAMS.search(output)
                if match:
                    max_bandwith = match.group(1)
                    logging.debug(max_bandwith)
                    return max_bandwith
            else:
                match = RE_LOST_DATAGRAMS.search(output)
                if match:
                    lost_datagrams = match.group(2)
                    logging.debug(lost_datagrams)
                    return lost_datagrams
        except Exception as e:
            logging.info(str(e))
            # Suppress this due to timeout once in a while even with -t 1 option


class EthernetFunc(ADB):
    DISABLE_COMMAND = 'ifconfig eth0 down'
    ENABLE_COMMAND = 'ifconfig eth0 up'

    def __init__(self):
        ADB.__init__(self, 'ethernet', unlock_code="", stayFocus=True)
        if isinstance(self.serialnumber, list):
            for device_config in pytest.config:
                self.ethernet_config = device_config.get('ethernet', {})
                self.staticIPV4_config = self.ethernet_config.get('staticIPV4', {})
                self.ipaddr = self.staticIPV4_config.get('ipaddr', '')
                self.mask = self.staticIPV4_config.get('mask', '')
                self.gateway = self.staticIPV4_config.get('gateway', '')
                self.prefix_length = self.staticIPV4_config.get('prefix_length', '')
                self.dns = self.staticIPV4_config.get('dns', '')
                self.spare_dns = self.staticIPV4_config.get('spare_dns', '')

                self.PPPOE_config = self.ethernet_config.get('PPPOE', {})
                self.PPPOE_ip = self.PPPOE_config.get("ipaddr", '')
                self.PPPOE_pwd = self.PPPOE_config.get("pwd", '')
        else:
            self.ethernet_config = pytest.config.get('ethernet', {})
            self.staticIPV4_config = self.ethernet_config.get('staticIPV4', {})
            self.ipaddr = self.staticIPV4_config.get('ipaddr', '')
            self.mask = self.staticIPV4_config.get('mask', '')
            self.gateway = self.staticIPV4_config.get('gateway', '')
            self.prefix_length = self.staticIPV4_config.get('prefix_length', '')
            self.dns = self.staticIPV4_config.get('dns', '')
            self.spare_dns = self.staticIPV4_config.get('spare_dns', '')

            self.PPPOE_config = self.ethernet_config.get('PPPOE', {})
            self.PPPOE_ip = self.PPPOE_config.get("ipaddr", '')
            self.PPPOE_pwd = self.PPPOE_config.get("pwd", '')

    def ethernet_disable(self):
        self.run_shell_cmd(self.DISABLE_COMMAND)

    def ethernet_enable(self):
        self.run_shell_cmd(self.ENABLE_COMMAND)
