#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/13 10:12
# @Author  : chao.li
# @Site    :
# @File    : DTV.py
# @Software: PyCharm

import logging
import re
import threading
import time

from lib.common.tvinput.LiveTv import LiveTv
from util.Decorators import set_timeout


class DTV(LiveTv):
    '''
    truck code dtv test lib

    Attributes:
        CHANNEL_1_COMMAND : dtv channe playback command
        SEARCH_COUNTSH : count check
        SEARCH_STORESH : store check

        result : test result

    '''
    CHANNEL_1_COMMAND = 'am start -a android.intent.action.VIEW -d content://android.media.tv/channel/1'
    SEARCH_COUNTSH = 'DTV_Search_Channel_CountCheck.sh'
    SEARCH_STORESH = 'DTV_Search_Channel_StoreCheck.sh'

    def __init__(self):
        LiveTv.__init__(self)
        self.root()
        self.home()
        self.result = 'Pass'

    def enter_dtv(self):
        '''
        enter in dtv channel
        @return: None
        '''
        self.run_shell_cmd(self.CHANNEL_1_COMMAND)
        time.sleep(2)
        self.screenshot('enter_DTV')

    def error(self):
        logging.info('something wrong')
        self.result = 'Fail'

    @set_timeout(5, error)
    def check_display(self):
        '''
        check the print to determine if display
        @return: status : boolean
        '''
        self.clear_logcat()
        logcat = self.popen('logcat')
        while True:
            line = logcat.stdout.readline()
            logging.info(line)
            if not line:
                continue
            if 'video available' in line:
                return True

    def playback(self, switch=False, during=120):
        '''
        playback dtv for few minutes
        @param switch: switch channel flag
        @param during: playback duration
        @return: None
        '''
        self.enter_dtv()
        temp = 0
        start = time.time()
        while time.time() - start < 120:
            frame = int(self.run_shell_cmd(self.FRAME_CHECK)[1])
            if switch and frame > 2000:
                self.keyevent('20')
                temp = 0
                if not self.check_display():
                    logging.warning('Playback not current')
                continue
            if frame > temp:
                temp = frame
            elif frame < temp:
                logging.info('Frame check error')
                logging.info(f'Last time frame{frame} , Current time frame{temp}')
                self.result = 'Fail'
                break

    def catch_epg(self):
        '''
        screen shot epg display
        @return:
        '''
        self.enter_dtv()
        self.check_display()
        self.keyevent('23')
        self.keyevent('23')
        self.screenshot('EPG')

    def audio_track(self):
        # Todo
        ...

    def get_channel_count(self):
        '''
        check dtv channel number
        @return: channel number
        '''
        log = self.run_shell_cmd(f'sh {self.TESTSH}')[1]
        if "DTV_Search_Channel_CountCheck is correct" in log:
            self.channel = re.findall(r'DTV_Search_Channel_CountCheck is correct (\d)', log, re.S)[0]
            logging.info(f'channel number is {self.channel}')
            return self.channel
