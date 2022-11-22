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
import os
import enum
import json
import random
import logging
from tools.resManager import ResManager

protocal_type = ['local', 'http', 'igmp', 'rtsp']
format_type = ['ts', 'mp4']


class ProtocolType(enum.Enum):
    LOCAL = 0
    HTTP = 1
    IGMP = 2
    RTSP = 3


class FormatType(enum.Enum):
    TS = 0
    MP4 = 1


class PlaybackMode(enum.Enum):
    PIP = 2
    MULTI_3 = 3
    MULTI_4 = 4
    MULTI_5 = 5
    MULTI_6 = 6
    MULTI_7 = 7
    MULTI_8 = 8
    MULTI_9 = 9


class videoconfig():

    def __init__(self):
        self.resManager = ResManager()
        self._config_path = self.resManager.get_target("videoconfig/videoconfig.json")
        self._save_path = self.resManager.get_target("videoconfig/urilist.txt")
        self.file = open(self._config_path, "rb")
        self._config = json.load(self.file)
        logging.debug(self._config_path)

    def __del__(self):
        self.file.close()
        self._config = None

    def get_protocal_index(self, value='local'):
        index = protocal_type.index(value)
        return ProtocolType(index)

    def get_config_list(self, ptoyocaltype=ProtocolType.LOCAL, resolution=None, format=None):
        list = []
        type = protocal_type[ptoyocaltype.value]
        if resolution is not None:
            for i in self._config[type]:
                if i['resolution'] == resolution:
                    list.append(i)
            if len(list) < 1:
                raise Exception('Could find resolution from videoconfig.json, Please check.')

        if format is not None:
            if len(list) > 0:
                for i in list:
                    if i['format'] == format:
                        list.append(i)
            else:
                for i in self._config[type]:
                    if i['format'] == format:
                        list.append(i)
            if len(list) < 1:
                raise Exception('Could find format from videoconfig.json, Please check.')
            else:
                return list

        if len(list) < 1:
            return self._config[type]
        else:
            return list

    def random_protocol_type_list(self, playback_mode=PlaybackMode.PIP):
        size = len(protocal_type)
        mode = playback_mode.value
        if mode <= size:
            protocols = random.sample(protocal_type, mode)
            return protocols
        else:
            protocols = random.choices(protocal_type, k=mode)
            return protocols

    def save_config_text(self, config=None):
        if config is None:
            raise Exception('Param config is None.')
        config_len = len(config)
        count = 0
        fb = open(self._save_path, "w")
        for str in config:
            count += 1
            if count < config_len:
                str += "\n"
            fb.writelines(str)
        fb.close()
        return self._save_path
