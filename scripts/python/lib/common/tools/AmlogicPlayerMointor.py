#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/9 9:23
# @Author  : chao.li
# @Site    :
# @File    : AmlogicPlayerMointor.py
# @Software: PyCharm

import logging
import re
import time

from lib.common.avsync.avmonitor.av_libplayer_monitor import AVLibplayerMonitor
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from lib.common.tools.YUV import YUV


class AmlogicPlayerMointor(PlayerCheck_Base):
    '''
    amlogic player apk mointror

    Attributes:

    '''

    def __init__(self):
        super(AmlogicPlayerMointor, self).__init__()

    def setup(self, playerType, YUVEnable=False, dropChkEnable=False, avSyncChkEnable=False):
        '''
        set up playback check control
        @param playerType: playback type
        @param YUVEnable: yuv check flag
        @param dropChkEnable: framedrop check flag
        @param avSyncChkEnable: av sync check flag
        @return:
        '''
        logging.info(f"[{self.__class__.__name__}][setup]playerType:"
                     f"{playerType}, YUVEnable:{YUVEnable},avSyncChkEnable:{avSyncChkEnable}")

        self.playerType = playerType
        self.yuvEnable = YUVEnable
        self.avSyncChkEnable = avSyncChkEnable

        if self.yuvEnable:
            self.yuv = YUV()
            self.yuv.open_yuv()
        if self.avSyncChkEnable:
            self.avMointer = AVLibplayerMonitor.get_monitor()

    def postInit(self):
        self.reset()
        if self.playerType == self.PLAYER_TYPE_LOCAL:
            self.ONSTARG_TAG = 'Start player'
            self.ONRELEASE_TAG = 'AmlogicPlayer: release'
            self.ONSTOP_TAG = 'AmlogicPlayer: stop'
            self.ONERROR_TAG = ''
            self.PROCESSBAR_TAG = 'getCurrentPosition'
            self.TAG = 'MediaPlayerService amplayer AmlogicPlayer SHCMCC_LocalPlayer'
            self.activity = ''
            self.PRINT_EXCEPTION_CRASH = 'beginning of crash'
        elif self.playerType == self.PLAYER_TYPE_YOUTUBE:
            ...
            # TODO:
        elif self.playerType == self.PLAYER_TYPE_NETFLIX:
            ...
            # TODO:

    def get_logcat(self, yuv=False, drop=False):
        '''
        get logcat ana analyze
        @param yuv:
        @param drop:
        @return:
        '''
        def stop_play():
            '''
            stop logcat catch
            stop playback
            re set playback status
            @return: None
            '''
            logging.info('Plyback End')
            # logging.info(f"播放结束 [VideoPlayerMointor][getLogcat]self.yuvEnable:{self.yuvEnable}, self.dropChkEnable:{self.dropChkEnable}")
            self.logcatStop()
            # self.stopDecodeChkThread()
            self.setStateSafe(False)
            self.app_stop(self.activity[0])
            logging.debug(f'Play end - {line}')
            # self.lastLogcat = line
            # self.stopPlay(self.ERROR_TYPE_OK)

        def count_time(time_list):
            return int(time_list[0]) * 3600 + int(time_list[1] * 60) + int(time_list[2])

        # 从logcat中获取播放状态的关键字
        logging.info('Getting logcat')
        self.startFrameChkThread()

        self.logcatStart()
        while True:
            if self.getErrorType() != 'OK':
                self.stopPlay(self.getErrorType())
                self.clear_logcat()
                return
            line = self.logcatReadLine()
            if not line:
                continue
            line = line.strip()
            # logging.info(line)
            # check if start playback
            if self.ONSTARG_TAG in line and not self.isPlaying:
                logging.info('Start playback')
                logging.debug(f'Play start - {line}')
                self.setStateSafe(True)
                time.sleep(3)
                self.setupDecodeType()
                logging.info(f'DecodeType {self.getDecodeType()}')
                self.startDecodeChkThread()
            # check if playback is stop
            if (self.ONSTOP_TAG in line or self.ONRELEASE_TAG in line) and self.isPlaying:
                stop_play()
                break
            # detect playback progress
            if self.PROCESSBAR_TAG in line and self.isPlaying:
                cur = re.findall(r'{}\s=\s(\d+)'.format(self.PROCESSBAR_TAG), line, re.S)[0]
                logging.info(f'current index {cur}')
            # if self.onError in line:
            #     logging.warning(f'[onError]: {line}')
            #     self.stopPlay(self.ERROR_TYPE_VIDEO_PLAYER)
            #     return
            # check if apk crash
            if self.PRINT_EXCEPTION_CRASH in line:
                logging.warning(f'crash: {line}')
                logging.warning('Player crash')
                self.stopPlay(self.ERROR_TYPE_PLAYER_CRASH)
                return
            # check if logcat eof
            if self.PRINT_EXCEPTION_EOF in line:
                logging.warning(f'EOF: {line}')
                logging.debug('logcat eof')
                self.stopPlay(self.ERROR_TYPE_LOGCAT_ERR)
                return
        self.stopPlay(self.ERROR_TYPE_OK)
        time.sleep(1)
        # if drop:
        #     log.frameDropCheck()
        self.clear_logcat()

    def __repr__(self):
        return 'AmlogicPlayer-Playback Check'
