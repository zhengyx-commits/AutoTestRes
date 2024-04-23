#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/16 08:19
# @Author  : chao.li
# @Site    :
# @File    : HdmiIn.py
# @Software: PyCharm

import logging
import time

from lib.common.tvinput.LiveTv import LiveTv


class HdmiIn(LiveTv):
    '''
    truck code hdmi in test lib

    Attributes:
        HDMI1_COMMAND : hdmi 1 channel command
        HDMI2_COMMAND : hdmi 2 channel command
        HDMI3_COMMAND : hdmi 3 channel command
        HDMI_INFO_COMMAND : cat hdmi rx info

        hdmi_list : hdmi channel command list[str]
    '''
    HDMI1_COMMAND = ('am start -a android.intent.action.VIEW -d '
                     'content://android.media.tv/passthrough/com.droidlogic.tvinput%2F.services.Hdmi1InputService%2FHW5')
    HDMI2_COMMAND = ('am start -a android.intent.action.VIEW -d '
                     'content://android.media.tv/passthrough/com.droidlogic.tvinput%2F.services.Hdmi2InputService%2FHW6')
    HDMI3_COMMAND = ('am start -a android.intent.action.VIEW -d '
                     'content://android.media.tv/passthrough/com.droidlogic.tvinput%2F.services.Hdmi3InputService%2FHW7')
    HDMI_INFO_COMMAND = 'cat /sys/class/hdmirx/hdmirx0/info'

    def __init__(self):
        super(HdmiIn, self).__init__()
        self.hdmi_list = [self.HDMI1_COMMAND, self.HDMI2_COMMAND, self.HDMI3_COMMAND]

    def switch(self, name, during):
        '''
        switch to hdmi channel
        @param name: hdmi channel name
        @param during: playbak duration
        @return: None
        '''
        logging.info(f'Switch to {name}')
        self.app_stop('com.amazon.tv.inputpreference.service')
        # switch_cmd = eval(f'self.{name.upper()}_COMMAND')
        # logging.info(f'switch cmd : {switch_cmd}')
        switch = self.run_shell_cmd(eval(f'self.{name.upper()}_COMMAND'))[1]
        time.sleep(10)
        if 'unable to resolve Intent' in switch:
             logging.warning('No this channel')
             self.result = 'Fail'
             assert False
        if self.find_element('No signal detected.', 'text'):
             logging.info('No signal detected.')
             self.screenshot(f'HDMI_{name}_No_signal_detected')
             assert False
        logging.info(f"switch is {switch}")
        checkPoint = self.check_status(name.title())
        logging.info(f'checkPoint {checkPoint}')
        self.check_hdmi_info()
        time.sleep(5)
        self.player_check.reset()
        self.player_check.setSourceType("tvpath")
        # assert self.player_check.check_frame_rate()
        check_flag = self.player_check.run_check_main_thread(during)
        if not check_flag:
            error_time = self.checkoutput('TZ=UTC-8 date')
            logging.info(f' ----- play error time : {error_time}')
            self.screenshot(f'HDMI_{name}_play_error')
            assert False
        # assert self.check_display_vfm('tvpath'), 'No map was generated!{}'.format(name)
        # assert self.player_check.checkHWDecodePlayback()

    def check_hdmi_info(self):
        '''
        check hdmi rx info
        print out over logging
        @return:
        '''
        try:
            all_status = self.run_shell_cmd(self.HDMI_INFO_COMMAND)[1].strip().split('\n')
            if all_status:
                status = [i for i in all_status if len(i) != 0]
                logging.info('Checking hdmirx driver related information')
                for index, stat in enumerate(status, 1):
                    if index < 18:
                        logging.info('*HDMI info[{}]: {}'.format(str(index).zfill(2), stat))
                    elif 18 < index < 25:
                        logging.info('Audio info[{}]: {}'.format(str(index).zfill(2), stat))
                    elif index > 25:
                        logging.info('*HDCP info[{}]: {}'.format(str(index).zfill(2), stat))
        except Exception as err:
            logging.error('Unable to check hdmirx info, {}'.format(err))
