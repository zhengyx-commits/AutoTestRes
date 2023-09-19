import logging
import os
import re
import signal
import threading
import time

import pytest

from lib.common.system.ADB import ADB
from util.Decorators import set_timeout, stop_thread

from . import config_yaml


class SeekFun(ADB):
    LOADING_TAG = ['PlayerBuffering buffering', 'need_start=1']
    POSITION_TAG_CMCC = ['curtime=', ' (ms:']
    POSITION_TAG_CMCC_RE = r' \(ms:(.*?)\) fulltime'
    LOGCAT_FILE = 'logcat.log'
    VIDEOPLAYER_POSITION_TAG = '[getCurrentPosition]'
    VIDEOPLAYER_POSITION_RE = r'position : (\d+) msec'
    LOGCAT_TAG_VIDEOPLAYER = 'NU-AmNuPlayerDriver'
    LOGCAT_TAG_AMPLAYER = 'amplayer'
    OTT_ONLINE_PLAY_POSITION_TAG = 'pts_time'
    LOGCAT_TAG_OTT_ONLINEPALY = 'AmlogicVideoDecoderAwesome2 | grep rumtime'
    OTT_ONLINEPALY_POSITION_RE = r'pts_time=(\d+)'

    direction_dict = {
        'right': ['right', '106', 2],
        'left': ['left', '105', 2],
        'stop': ['stop', '164', 2]
        # 'start': ['start', '166', 2]
    }

    def __init__(self):
        super(SeekFun, self).__init__('seekFunc', unlock_code="", stayFocus=False)
        self.press_event = ''
        self.position_list = []
        self.res = ''
        self.config_yaml = config_yaml()
        self.p_conf_seek = self.config_yaml.get_note('conf_seek')
        self.p_conf_seek_type = self.p_conf_seek['seek_press_event']['seek_type']
        self.p_conf_seek_event = self.p_conf_seek['seek_press_event']['event']
        # self.avSync = avSync
        # if self.avSync:
        #     self.avMointer = AVLibplayerMonitor.get_monitor()

    def checkSeekLoop(self):
        while True:
            for key in self.direction_dict.keys():
                logging.info(key)
                self.local_play_seek(str(key))
                time.sleep(10)
            # self.process_switch("left", direction_dict=self.direction_dict, press_event='event3')

    def startSeekThread(self):
        if not hasattr(self, 's'):
            self.s = threading.Thread(target=self.checkSeekLoop,
                                      name='seekThread')
            self.s.setDaemon(True)
            self.s.start()
            logging.info('startSeekThread')

    def stopSeekThread(self):
        if isinstance(self.s, threading.Thread):
            logging.info('stopSeekThread')
            stop_thread(self.s)

    def online_play_seek(self, direction):
        if direction == "right" or direction == "left":
            self.keyevent('KEYCODE_DPAD_UP')
            # start longPress
            self.process_switch(direction)
            self.keyevent('KEYCODE_DPAD_CENTER')
            self.check_seek_position(position_tag=self.OTT_ONLINE_PLAY_POSITION_TAG,
                                     position_re=self.OTT_ONLINEPALY_POSITION_RE,
                                     logcat_tag=self.LOGCAT_TAG_OTT_ONLINEPALY)
            if self.get_position_direction() == direction:
                logging.info(f'Process bar direction: {direction}')

        elif direction == 'stop':
            self.keyevent('KEYCODE_DPAD_UP')
            self.keyevent('KEYCODE_DPAD_CENTER')
            time.sleep(5)
            self.keyevent('KEYCODE_DPAD_CENTER')

    def local_play_seek(self, direction):
        if direction == "right" or direction == "left":
            self.keyevent("KEYCODE_DPAD_CENTER")
            self.keyevent('KEYCODE_DPAD_UP')
            # start longPress
            self.process_switch(direction)
            self.check_seek_position(position_tag=self.VIDEOPLAYER_POSITION_TAG,
                                     position_re=self.VIDEOPLAYER_POSITION_RE,
                                     logcat_tag=self.LOGCAT_TAG_VIDEOPLAYER)
            if self.get_position_direction() == direction:
                logging.info(f'Process bar direction: {direction}')
        elif direction == 'stop':
            # stop and start play
            self.keyevent("KEYCODE_DPAD_CENTER")
            self.keyevent("KEYCODE_DPAD_CENTER")
            time.sleep(5)
            self.keyevent("KEYCODE_DPAD_CENTER")
            self.keyevent("KEYCODE_DPAD_CENTER")

    @set_timeout(300)
    def check_seek_position(self, position_tag, position_re):
        '''
        detects changes in the position
        @param position_tag: tag
        @param position_re: regular
        @return: None
        '''

        def count_time(time_list):
            return int(time_list[0]) * 3600 + int(time_list[1]) * 60 + int(time_list[2])

        logging.info('Cheking position info')
        temp = self.position_list[:]
        self.position_list.clear()
        logcat = self.popen('logcat -s amplayer')
        start = ''
        while True:
            line = logcat.stdout.readline()
            if 'unexpected EOF!' in line:
                raise ValueError('logcat buffer crash ,no data in file')
            if position_tag[0] and position_tag[1] in line:
                if not start:
                    start = count_time(line[6:14].split(':'))
                    logging.info(f'start {start}')
                    logging.info(line[6:14])
                logging.info(line)
                self.position_list.append(int(re.findall(position_re, line, re.S)[0]))
                logging.info(f'position_list:{self.position_list}')
                if count_time(line[6:14].split(':')) - start > 50:
                    logging.info(f"end {count_time(line[6:14].split(':'))}")
                    os.kill(logcat.pid, signal.SIGTERM)
                    logcat.terminate()
                    break
                if len(self.position_list) > 2 and abs(self.position_list[-1] - self.position_list[-2]) > 50000:
                    logging.info(f"end {count_time(line[6:14].split(':'))}")
                    os.kill(logcat.pid, signal.SIGTERM)
                    logcat.terminate()
                    break
        if temp and temp[-1] in self.position_list:
            self.position_list = self.position_list[self.position_list.index(temp[-1]) + 1:]
        self.clear_logcat()

    def get_position_direction(self):
        '''
        get seek direction over position value
        @return: direction
        '''
        self.position_list = list(map(int, self.position_list))
        logging.info(self.position_list)
        for i in range(len(self.position_list) - 1):
            if self.position_list[i + 1] - self.position_list[i] > 50000:
                # logging.info(f'right {self.position_list[i + 1]} - {self.position_list[i]} ')
                return 'right'
            if self.position_list[i + 1] - self.position_list[i] < -50000:
                # logging.info(f'left {self.position_list[i + 1]} - {self.position_list[i]} ')
                return 'left'
        return ''

    def process_switch(self, direction, position_tag='', position_re='', hold_time=0):
        '''
        random seek
        @param direction: seek direction
        @param position_tag: logcat tag
        @param position_re: logcat regular
        @param hold_time: seek hold time
        @return: None
        '''
        self.root()
        direction_dict = {
            'left': ['left', '105', 2],
            'right': ['right', '106', 2]
        }
        # 开始长按
        logging.info(f'Start {direction_dict[direction][0]} hold click')
        self.clear_logcat()
        logging.info(f'start tap {time.asctime()}')
        self.run_shell_cmd(
            f'sendevent /dev/input/event0 1 {direction_dict[direction][1]} 1;sendevent /dev/input/event0 0 0 0')
        if hold_time == 0:
            time.sleep(2)
        else:
            time.sleep(hold_time)
        self.run_shell_cmd(
            f'sendevent /dev/input/event0 1 {direction_dict[direction][1]} 0;sendevent /dev/input/event0 0 0 0')
        logging.info(f'end tap {time.asctime()}')
        time.sleep(10)
        logging.info(time.asctime())
        self.check_seek_position(position_tag or self.POSITION_TAG_CMCC, position_re or self.POSITION_TAG_CMCC_RE)
        logging.info(f'get_position_direction:{self.get_position_direction()}')
        if self.get_position_direction() == direction:
            logging.info(f'Process bar direction: {direction_dict[direction][0]}')
            return True
        else:
            return False
