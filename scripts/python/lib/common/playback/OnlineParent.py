#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/24 14:24
# @Author  : chao.li
# @Site    :
# @File    : OnlineParent.py
# @Software: PyCharm

import logging
import os
import re
import signal
import subprocess
import threading
import time

from lib import CheckAndroidVersion
from lib.common.system.ADB import ADB
from util.Decorators import set_timeout

checkandroidversion = CheckAndroidVersion()


class Online(ADB):
    '''
    Online video playback

    Attributes:
        DECODE_TAG : logcat tag
        DECODE_TAG_AndroidS : logcat tag
        PLAYER_PACKAGE_TUPLE : player package tuple

    '''

    DECODE_TAG = 'AmlogicVideoDecoderAwesome'
    DECODE_TAG_AndroidS = 'VDA'
    PLAYER_PACKAGE_TUPLE = '', ''

    def __init__(self, name=''):
        super(Online, self).__init__('OnlinePlayback')

    def playback(self, activity, link):
        '''
        start apk
        am start -n xxx
        @param activity: activity name
        @param link: video link
        @return:
        '''
        logging.info(activity.format(link))
        self.checkoutput(activity.format(link))

    def time_out(self):
        '''
        kill logcat process
        clear logcat
        @return:
        '''
        logging.warning('Time over!')
        if hasattr(self, 'logcat') and isinstance(self.logcat, subprocess.Popen):
            os.kill(self.logcat.pid, signal.SIGTERM)
            self.logcat.terminate()
        self.clear_logcat()

    @set_timeout(120, time_out)
    def check_playback_status(self):
        '''
        Waiting for network load video
        @return: True (When video is playing) or error (Timeout) : boolean
        '''
        logging.info('Start to check playback status')
        self.clear_logcat()
        android_version = self.getprop(checkandroidversion.get_android_version())
        self.logcat = self.popen("logcat -s %s" % self.DECODE_TAG_AndroidS)
        temp, count = 0, 0
        while True:
            line = self.logcat.stdout.readline()
            if android_version in ("31", "34"):
                if 'ServiceDeviceTask INs=' not in line:
                    continue
                number = re.findall(r'ServiceDeviceTask INs=(\d+)/\d+', line, re.S)[0]
                # logging.info(f"number: {number}")
            else:
                if 'buffer counts:' not in line:
                    continue
                number = re.findall(r'IN\[(\d+),\d+\]', line, re.S)[0]
            logging.debug(f'buffer count {number}')
            if int(number) > temp:
                count += 1
            if count > 30:
                logging.info('Video is playing ... ')
                # self.clear_logcat()
                return True
            temp = int(number)
        # return True

    def check_apk_exist(self):
        '''
        check apk status
        @return: apk status : boolean
        '''
        return True if self.PLAYER_PACKAGE_TUPLE[0] in self.checkoutput('ls /data/data/') else False
