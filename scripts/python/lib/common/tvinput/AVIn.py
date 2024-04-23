#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/13 10:12
# @Author  : chao.li
# @Site    :
# @File    : AVIn.py
# @Software: PyCharm

import logging
import time

from lib.common.tvinput.LiveTv import LiveTv


class AVIn(LiveTv):
    '''
    truck code avin test lib

    Attributes:
        AVIN_COMMAND : av in activity command
        SEARCH_STORESH : store check sh

        result : test result

    '''
    AVIN_COMMAND = ('am start -a android.intent.action.VIEW -d '
                    'content://android.media.tv/passthrough/com.droidlogic.tvinput%2F.services.AV1InputService%2FHW1')

    def __init__(self):
        super(AVIn, self).__init__()

    def switch(self, during):
        '''
        enter in av-in channel
        check frame rate and playback status for few seconds
        @param during: playback duration
        @return:
        '''
        logging.info('Switching playback scene -- AV')
        # switch = ''.join(self.popen(f' shell {self.AVIN_COMMAND}').stdout.readlines())
        switch = self.checkoutput(self.AVIN_COMMAND)
        self.screenshot('AVin')
        if 'unable to resolve Intent' in switch:
            logging.warning('The playback channel was not found')
            self.result = 'Fail'
            return
        if self.find_element('No signal detected.', 'text'):
            logging.info('No signal detected.')
            self.screenshot('Avin_No_Signal')
            assert False
        checkPoint = self.check_status('AV1')
        logging.info(f'checkPoint {checkPoint}')
        assert self.player_check.check_frame_rate()
        check_flag = self.player_check.run_check_main_thread(during)
        if not check_flag:
            error_time = self.checkoutput('TZ=UTC-8 date')
            logging.info(f' ----- play error time : {error_time} -----')
            self.screenshot(f'avin_play_error')
            assert False

    def display(self, during=120):
        '''
        check channel status
        playback two minutes
        @param during: duation
        @return: check status
        '''
        if 'AV1' == self.check_status('AV1'):
            time.sleep(4)
            self.check_display()
            time.sleep(during)
        else:
            self.result = 'Fail'
