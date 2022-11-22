#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/24 14:24
# @Author  : chao.li
# @Site    :
# @File    : Netflix.py
# @Software: PyCharm

import logging
import os
import re
import signal
import time

from lib import CheckAndroidVersion
from lib.common.checkpoint.PlayerCheck import PlayerCheck
from util.Decorators import set_timeout

from .OnlineParent import Online

check_android_version = CheckAndroidVersion()
player_check = PlayerCheck()


class Netflix(Online):
    '''
    netflix test lib

    Attributes:
        PLAYBACK_COMMAND_FORMAT : netflix playback command format (need video link)
        PLAYTYPE : playback type
        ACCOUNT : test account
        PASSWORD : test passwd
        DECODE_TAG : logcat decode tag
        VIDEO_TAG_LIST : test video info : list [dict]
        VIDEO_INFO : video info

    '''

    PLAYBACK_COMMAND_FORMAT = ('am start -n com.netflix.ninja/com.netflix.ninja.MainActivity '
                               '-a android.intent.action.VIEW -d https://www.netflix.com/watch/{}?source=99')
    PACKAGE_NAME = 'com.netflix.ninja'
    PLAYTYPE = 'Netflix'
    ACCOUNT = 'xxx'
    PASSWORD = 'xxx'
    DECODE_TAG = 'AmlogicVideoDecoderAwesome2'
    VIDEO_INFO = []

    VIDEO_TAG_LIST = [
        {'link': '80010857', 'name': 'Marco Polo S1:E2 The Wolf and the Deer'},  # H.265
        {'link': '80190487', 'name': 'Giri/Haji S1:E1'},  # DolbyVision + Atmos H265
        {'link': '80003008', 'name': 'Peaky Blinders S1:E1'},  # DolbyVision + Atmos av1
        {'link': '80138257', 'name': 'Lucifer S1:E2 Lucifer,Stay.Good Devil.'},
        # DolbyVision + 5.1 av1
        {'link': '80006792', 'name': 'Tears of Steel'},  # H265
        # {'link': '80221640', 'name': '超级破坏王'},
        # {'link': '80104446', 'name': 'SCREAM'},
        # {'link': '70118402', 'name': 'Salt'}
        {'link': '80164308', 'name': 'Minaculous'}
    ]

    def __init__(self, name=''):
        super(Netflix, self).__init__(name)

    def login(self):
        '''
        login netflix
        @return: None
        '''
        logging.info('input account')
        self.text(self.ACCOUNT)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        self.enter()
        logging.info('input passwd')
        self.text(self.PASSWORD)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        time.sleep(1)
        self.enter()
        time.sleep(60)
        self.enter()
        time.sleep(3)
        logging.info('login done')

    def check_Netflix_exist(self):
        return True if self.PACKAGE_NAME in self.checkoutput('pm list packages') else False

    def start_play(self):
        '''
        start playback
        @return: none
        '''
        video = self.VIDEO_TAG_LIST[5]
        logging.info(f"Start playing Netflix - {video['name']}")
        self.playback(self.PLAYBACK_COMMAND_FORMAT, video['link'])
        time.sleep(30)
        logging.info("netflix is start successfully")

    def stop_netflix(self):
        '''
        stop netflix
        @return: None
        '''
        stop_cmd = f'am force-stop {self.PACKAGE_NAME}'
        self.run_shell_cmd(stop_cmd)
        logging.info("nexflix is closed successfully")

    def time_out(self):
        logging.warning('Time over!')

    @set_timeout(60, time_out)
    def check_playback_status(self):
        '''
        check if video is start playback
        @return: status : boolean
        '''
        logging.info('Start check playback status')
        self.clear_logcat()
        self.logcat = self.popen("logcat -s %s" % self.DECODE_TAG_AndroidS)
        temp, count = 0, 0
        while True:
            line = self.logcat.stdout.readline()
            if self.getprop(check_android_version.get_android_version()) == "31":
                if 'ServiceDeviceTask' not in line:
                    continue
            else:
                if 'AllocTunneledBuffers' not in line:
                    continue
            number = re.findall(r'IN\[(\d+),\d+\]', line, re.S)[0]
            logging.debug(f'buffer count {number}')
            if int(number) > temp:
                count += 1
            if count > 5:
                logging.info('Video is playing')
                os.kill(self.logcat.pid, signal.SIGTERM)
                self.logcat.terminate()
                self.clear_logcat()
                return True
            temp = int(number)

    def netflix_setup(self):
        '''
        set ui enter login interface
        @return: None
        '''
        self.open_omx_info()
        self.run_shell_cmd(f"monkey -p {self.PACKAGE_NAME} 1")
        time.sleep(20)
        logging.info('start to login')
        for i in range(5):
            self.keyevent(21)
        time.sleep(1)
        self.keyevent(22)
        time.sleep(1)
        self.enter()
        time.sleep(1)
        self.login()
        time.sleep(20)
        self.enter()
        self.home()
        time.sleep(3)

    # def netflix_hybrid_setup(self):
    #     self.open_omx_info()
    #     self.run_shell_cmd(f"monkey -p {self.PACKAGE} 1")
    #     time.sleep(20)
    #     logging.info('start to login')
    #     self.keyevent(21)
    #     time.sleep(1)
    #     self.enter()
    #     time.sleep(1)
    #     self.login()
    #     time.sleep(15)
    #     self.app_stop(self.PACKAGE)

    def netflix_play(self, seekcheck=False):
        '''
        playback netflix video (from VIDEO_TAG_LIST)
        @param seekcheck: seek check status : boolean
        @return: playback status : boolean
        '''
        for i in self.VIDEO_TAG_LIST:
            logging.info(f"Start playing Netflix - {i['name']}")
            self.playback(self.PLAYBACK_COMMAND_FORMAT, i['link'])
            play = self.check_playback_status()
            time.sleep(30)
            if play:
                player_check.check_secure()
                # playerCheck.run_check_main_thread(30)
                time.sleep(30)
            else:
                return False
            if seekcheck == "True":
                # TODO seek_check not founc
                player_check.seek_check()
        return True
