#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/13 10:12
# @Author  : chao.li
# @Site    :
# @File    : ATV.py
# @Software: PyCharm

import logging
import re
import time

from lib.common.tvinput.LiveTv import LiveTv
from util.Decorators import set_timeout

SOURCE = '178'


class ATV(LiveTv):
    '''
    truck code atv test lib

    Attributes:
        SEARCH_COUNTSH : count check sh
        SEARCH_STORESH : store check sh

        result : test result

    '''
    SEARCH_COUNTSH = 'ATV_Search_Channel_CountCheck.sh'
    SEARCH_STORESH = 'ATV_Search_Channel_StoreCheck.sh'

    def __init__(self):
        LiveTv.__init__(self)
        self.root()
        self.home()
        self.result = 'Pass'

    def enter_atv(self):
        '''
        enter in atv activity
        @return:
        '''
        self.keyevent(SOURCE)
        self.u2.wait('ATV')
        time.sleep(2)

    def error(self):
        logging.info('something wrong')
        self.result = 'Fail'

    def playback(self, switch=False, during=120):
        '''
        start playback and play for two minutes
        @param switch: switch channel flag
        @return:
        '''
        self.enter_atv()
        temp = 0
        start = time.time()
        while time.time() - start < during:
            frame = int(self.run_shell_cmd(self.FRAME_CHECK)[1])
            if switch and frame > 2000:
                self.keyevent('20')
                temp = 0
                if not self.check_display():
                    logging.warning("Vfm map doesn't current")
                continue
            if frame > temp:
                temp = frame
            elif frame < temp:
                logging.info('Frame check error')
                logging.info(f'Last time frame{frame} , Current time frame{temp}')
                self.result = 'Fail'
                break

    def audio_track(self):
        # Todo
        ...

    def check_atvdemod_info(self):
        '''
        check atv demod info
        print out info
        @return: None
        '''
        try:
            atvdemod_status = self.run_shell_cmd('cat /sys/class/aml_atvdemod/atvdemod_debug')[1].strip().split('\n')
            for index, stat in enumerate(atvdemod_status, 1):
                logging.info('[{}] {}'.format(str(index).zfill(2), stat))
        except Exception as err:
            logging.info('Unable to check atvdemod status, {}'.format(err))
