#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/13 16:37
# @Author  : chao.li
# @Site    :
# @File    : AudioCheck.py
# @Software: PyCharm

import logging
import re
import threading

from lib.common.system.ADB import ADB

from . import Check


class AudioCheck(ADB, Check):
    '''
    Singleton class,should not be inherited

    Attributes:
        TINY_MIX_COMMAND : tinymix command
        VOLUME_COMMAND : media volume command

    '''

    _INSTANCE_LOCK = threading.Lock()

    TINY_MIX_COMMAND = 'tinymix'
    VOLUME_COMMAND = 'media volume --stream 3 --get'

    def __init__(self):
        ADB.__init__(self, 'Player', unlock_code="", stayFocus=True)
        Check.__init__(self)

    def __new__(cls, *args, **kwargs):
        if not hasattr(AudioCheck, "_instance"):
            with AudioCheck._INSTANCE_LOCK:
                if not hasattr(AudioCheck, "_insatnce"):
                    AudioCheck._instance = object.__new__(cls)
        return AudioCheck._instance

    def get_audio_type(self):
        '''
        get audio type over tinymix command
        command : tinymix
        @return: audio type : str
        '''
        audio_info = self.checkoutput(self.TINY_MIX_COMMAND)
        audio_type = re.findall(r'HDMIIN Audio Type\s+(\w+)', audio_info, re.S)[0]
        logging.debug(audio_type)
        return audio_type

    def get_volume(self):
        '''
        get software volume value over media volume command
        command : media volume --stream 3 --get
        @return: volume : int
        '''
        volume_info = self.checkoutput(self.VOLUME_COMMAND)
        volume = re.findall(r'volume is (\d+) in range', volume_info, re.S)[0]
        logging.debug(volume)
        return int(volume)

    def __repr__(self):
        return 'Audio check point'
