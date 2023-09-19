#!/usr/bin/env python
# Copyright 2020 Amlogic.com, Inc. or its affiliates. All rights reserved.
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

import enum
import json
import logging
import os

import broadlink as blkrm3
import pytest

from tools.resManager import ResManager

KeyEvent = ["power", "mute", "enter", "back", "up", "down", "left", "right", "volume_up", "volume_down", "channel_up",
            "channel_down"]


class KeyEventMapping(enum.Enum):
    KEYEVENT_POWER = 0
    KEYEVENT_MUTE = 1
    KEYEVENT_ENTER = 2
    KEYEVENT_BACK = 3
    KEYEVENT_UP = 4
    KEYEVENT_DOWN = 5
    KEYEVENT_LEFT = 6
    KEYEVENT_RIGHT = 7
    KEYEVENT_VOLUME_UP = 8
    KEYEVENT_VOLUME_DOWN = 9
    KEYEVENT_CHANNEL_UP = 10
    KEYEVENT_CHANNEL_DOWN = 11


class IRControl:
    """
        *Broadlinkrm3 example demo*
        base_config = baseconfig.get_config_json_data("config")
        broadlinkconfig = base_config.get("broadlink")
        ipaddr = broadlinkconfig.get("ipaddr")
        broadcast_addr = broadlinkconfig.get("broadcast_addr")
        host = broadlinkconfig.get("host")

        remote = IRControl(ip=ipaddr, broadcastaddr=broadcast_addr, host=host)
        ret = remote.init_blkrm3()
        remote.set_irkey_by_project()
        remote.send_irkey(KeyEventMapping.KEYEVENT_UP)
    """
    PROJECT_NAME = 'iptv_ref'

    def __init__(self, ip=None, broadcastaddr=None, host=None, port=80, project=None, configpath=None):
        self.configpath = configpath
        self.ipaddr = ip
        self.broadcastaddr = broadcastaddr
        self.host = host
        self.port = port
        self.remote = None
        self.irkeydata = None
        self.res = ResManager()
        self.init_blkrm3()
        self.get_irkey_by_project(project)
        if self.remote:
            self.remote.auth()

    def init_blkrm3(self):
        # host = self.confg.get('host')
        # host_port = self.confg.get('host_port')
        # ipaddr = self.confg.get('ipaddr')
        # broadcastaddr = self.confg.get('broadcast_addr')

        try:
            if self.host is not None:
                remote = blkrm3.hello(host=self.host, timeout=5, local_ip_address=self.ipaddr)
                if remote:
                    self.remote = remote
                    return True

            if self.ipaddr is None and self.broadcastaddr is None:
                remotes = blkrm3.discover(timeout=10)
                if len(remotes) >= 1:
                    self.remote = remotes[0]
                    return True

            if self.ipaddr is not None:
                remotes = blkrm3.discover(timeout=5, local_ip_address=self.ipaddr)
                if len(remotes) >= 1:
                    self.remote = remotes[0]
                    return True

            if self.broadcastaddr is not None:
                remotes = blkrm3.discover(timeout=5, discover_ip_address=self.broadcastaddr)
                if len(remotes) >= 1:
                    self.remote = remotes[0]
                    return True

            return False
        except Exception as e:
            error_message = "{}".format(e)
            print(error_message)

    def get_irkey_by_project(self, project=None):
        logging.info('get {} remote irkey'.format(project))
        if project is not None:
            self.PROJECT_NAME = project

        if self.configpath is None:
            self.res.get_target("project/")
            with open(os.path.join(os.getcwd(),
                                   "res/project/" + self.PROJECT_NAME + "_irkey_mapping.json")) as data_file:
                date = json.loads(data_file.read())
        else:
            with open(self.configpath) as data_file:
                date = json.loads(data_file.read())

        self.irkeydata = date['keymapping']

    def send_irkey(self, keycode):
        if keycode is None:
            logging.debug("send irkey keycode is None.")
            return False

        if self.irkeydata is None:
            logging.debug("irkey map not found")
            return False

        if self.remote is None:
            logging.debug("broadlink rm3 not found. init error, please check broadlink rm 3.")
            return False

        sendkey = bytes.fromhex(self.irkeydata[KeyEvent[keycode.value]])
        logging.info('remote project: {}, keycode: {}'.format(self.PROJECT_NAME, keycode))
        logging.info('sendkey: {}'.format(self.irkeydata[KeyEvent[keycode.value]]))
        self.remote.send_data(sendkey)
        return True
