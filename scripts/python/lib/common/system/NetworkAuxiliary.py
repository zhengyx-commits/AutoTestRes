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
import subprocess
import pytest
import os
import socket
from lib.common.system import SSH
from tools.yamlTool import yamlTool

config_common_yaml = yamlTool(os.getcwd() + '/config/config.yaml')


def differentiate_servers():
    p_conf_ip = config_common_yaml.get_note("ip")
    p_conf_device_ip = p_conf_ip.get("device_ip")
    p_conf_stream_ip = p_conf_ip.get("stream_ip")
    p_conf_rtsp_path = config_common_yaml.get_note("rtsp_path")
    DEVICE_IP = p_conf_device_ip
    STREAM_IP = p_conf_stream_ip
    RTSP_PATH = p_conf_rtsp_path
    return DEVICE_IP, STREAM_IP, RTSP_PATH


def get_hostname():
    hostname = socket.gethostname()
    return hostname


def getIfconfig():
    iplist = []
    p = subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE, encoding="utf-8")
    data = p.stdout.read().split('\n')
    for ips in data:
        ip = re.findall(r"inet (.*) netmask ", ips, re.S)
        if ip:
            iplist.append(ip[0].strip())
    # print(iplist)
    return iplist


class Auxiliary(object):
    LOG_IPERF_OUTPUT = "/tmp/iperf_output"

    def __init__(self, ip, uname, passwd):
        self.ssh = None
        self._start_ssh(ip, uname, passwd)

    def _send_cmd(self, cmd):
        """ Helper function to send a command to the Auxiliary device

        Args:
            cmd (str): OpenWrt UCI command to run on the Auxiliary device

        Optional Args:
            None

        Returns:
            str: output from the cmd

        Raises:
            Exception if unexpected errors occur
        """
        try:
            output = self.ssh.send_cmd(cmd)
            return output.replace('\\n', '\n')
        except Exception as e:
            logging.error("Error in sending cmd {0}. Reason: {1}".format(cmd, e))
            raise e

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
        output = self._send_cmd("which {}".format(command))
        return True if output.find(command) != -1 else False

    def get_ip_info(self, interface='eno1'):
        """ Get IP info after DUT associates with a network

        Args:
            None

        Optional Args:
            None

        Returns:
            str: the IP address of the Auxiliary device

        Raises:
            Exception if unexpected errors occur
        """
        output = self._send_cmd('ifconfig {}'.format(interface))
        logging.debug(output)
        res = re.findall('((?:[0-9]{1,3}.){3}[0-9]{1,3})', output)
        ip_addr = res[0] if res else "0.0.0.0"
        logging.info("AP IP Address is {}".format(ip_addr))
        return ip_addr

    def _start_ssh(self, ip, uname, passwd):
        """ Start SSH connection with the Auxiliary device

        Args:
            None

        Optional Args:
            None

        Returns:
            None

        Raises:
            Exception if unexpected errors occur
        """
        try:
            self.ssh = SSH(ip, uname, passwd)
            self.ssh.open_connection(retries=3)
            logging.debug("start successfully")
        except Exception as e:
            self.ssh = None
            logging.error("SSH access to AP Failed. Reason: %s" % e)
            raise e

    def run_iperf(self, role='server', time=10, dest="", tcp=False, dual=False,
                  bandwith="100M", tos=0):
        """ run iperf on DUT

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
            Exception if unexpected errors occur
        """
        cmds = ["iperf"]

        if role == 'server':
            self._send_cmd("killall iperf")
            if not tcp:
                cmds.append('-u')
            cmds.append('-s')
        elif role == 'client':
            if not tcp:
                cmds.append('-u -b {}'.format(bandwith))
            cmds.append('-c {}'.format(dest))
            if tos:
                cmds.append('-S {}'.format(tos))
            if dual:
                cmds.append('-d')
            cmds.append('-t {}'.format(time))
        else:
            raise ValueError("role ({}) is not supported".format(role))
        logging.debug(cmds)
        self._send_cmd("{} > {} &".format(" ".join(cmds), self.LOG_IPERF_OUTPUT))
