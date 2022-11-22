#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/12 10:04
# @Author  : chao.li
# @Site    :
# @File    : VideoPlayerMointor.py
# @Software: PyCharm

import logging
import re
import time

from lib.common.checkpoint.PlayerCheck import PlayerCheck
from lib.common.tools.FrameDropCheck import FrameDropCheck
from lib.common.tools.YUV import YUV


class VideoPlayerMonitor(PlayerCheck):
    '''
    video player apk mointor

    Attributes:
        playfile_error : playfile status
        eof : eof status
        crash : logcat crash status
        play_error : playback error

    '''

    def __init__(self):
        super(VideoPlayerMonitor, self).__init__()
        self.playfile_error = True
        self.eof = True
        self.crash = True
        self.play_error = True
        # self.lastLogcat = ''

    def setup(self, playerType, sourceType, yuv_enable=False, drop_check_enable=False, avsync_check_enable=False,
              random_seek_enable=False, subtitle_check_enable=False):
        '''
        reset mointor status
        @param playerType: playback type
        @param sourceType: source type
        @param yuv_enable: yuv check flag
        @param drop_check_enable: drop check flag
        @param avsync_check_enable:  avsync check flag
        @param random_seek_enable: random seek flag
        @param subtitle_check_enable: subtitle check flag
        @return: None
        '''
        logging.info(
            f"[VideoPlayerMointor][setup]ProjectType:{sourceType},playerType:{playerType}, YUVEnable:{yuv_enable}, "
            f"dropChkEnable:{drop_check_enable},avSyncChkEnable:{avsync_check_enable}, "
            f"randomSeekEnable:{random_seek_enable}, subtitle:{subtitle_check_enable}")
        self.playerType = playerType
        self.yuvEnable = yuv_enable
        self.dropChkEnable = drop_check_enable
        self.avSyncChkEnable = avsync_check_enable
        self.randomSeekEnable = random_seek_enable
        self.subTitleChkEnable = subtitle_check_enable
        self.sourceType = sourceType
        if self.yuvEnable:
            self.yuv = YUV()
            self.yuv.open_yuv()
        if self.dropChkEnable:
            self.dropCheck = FrameDropCheck(self.serialnumber, self.logdir)

    def postInit(self):
        '''
        set apk mointor tag
        @return: None
        '''
        self.reset()
        if self.playerType == self.PLAYER_TYPE_LOCAL:
            self.ONSTART_TAG = '[start]mMediaPlayer:'
            self.ONCOMPLETE_TAG = '[onCompletion]'
            self.ONPAUSE_TAG = '[onPause]'
            self.ONSTOP_TAG = '[onStop]'
            self.ONERROR_TAG = '[onError]mErrorTime:'
            self.PROCESSBAR_TAG = '[updateProgressbar]'
            self.ONPLAY_TAG = '[playFile]'
            self.ONSEEKCOMPLETE_TAG = '[onSeekComplete]'
            self.TAG = 'VideoPlayer'
            self.ACTIVITY_TUPLE = 'com.droidlogic.videoplayer', '.VideoPlayer'
        elif self.playerType == self.PLAYER_TYPE_YOUTUBE:
            ...
            # TODO:
        elif self.playerType == self.PLAYER_TYPE_NETFLIX:
            ...
            # TODO:

    def get_logcat(self, playcommand_time="", yuv=False, drop=False):
        '''

        @param playcommand_time:
        @param yuv:
        @param drop:
        @return:
        '''
        # def stop_play():
        #     logging.info('播放结束')
        #     # logging.info(f"播放结束 [VideoPlayerMointor][getLogcat]self.yuvEnable:{self.yuvEnable}, self.dropChkEnable:{self.dropChkEnable}")
        #     self.logcatStop()
        #     self.stopDecodeChkThread()
        #     self.setStateSafe(False)
        #     self.app_stop(self.activity[0])
        #     logging.debug(f'Play end - {line}')
        #     # self.lastLogcat = line
        #     # self.stopPlay(self.ERROR_TYPE_OK)

        # def count_time(time_list):
        #     return int(time_list[0]) * 3600 + int(time_list[1] * 60) + int(time_list[2])
        self.set_AndroidVersion_R_checkpoint()
        self.startDecodeChkThread()
        self.startFrameChkThread()
        if self.avSyncChkEnable:
            self.startAVSyncThread()
        if self.randomSeekEnable and self.seek.seek_type == 'press_seek':
            self.seek.startSeekThread()
        if self.subTitleChkEnable and self.check_vdec_status('ammvdec_h264_v4'):
            self.subtitle.start_subtitle_thread()
        start_time = time.time()
        self.counter = 0
        # 从logcat中获取播放状态的关键字
        logging.info('Start catch logcat')
        # self.logcat = self.popen('logcat -s %s' % self.TAG)
        # self.startFrameChkThread()
        if self.dropChkEnable:
            self.omxLogcat = self.dropCheck.run()
            # omxLogcat = self.dropcheck.catchLogcat()
        while True:
            if self.getErrorType() != 'OK':
                self.stopPlay(self.getErrorType())
                self.clear_logcat()
                # input('请确认异常后继续测试')
                return
            line = self.logcatReadLine()
            """
            # Judge the logcat readline time and playcommand_time,
            # because readline time from logcat sometimes is earlier than playcommand time
            """
            # check if start play
            if self.ONPLAY_TAG in line:
                logging.info(f"line:{line}")
                res = re.findall("(.*)-(.*) (.*):(.*):(.*)\.(.*) (.*) I", line)[0]

                readline_time = ":".join(res[2:5])
                # readline_time = time.strftime("%H:%M:%S")
                logging.info(f"readline_time:{readline_time}")
                if str(readline_time) >= str(playcommand_time):
                    if self.path.strip() not in line:
                        logging.warning(f'videoName: ->{self.path}<-')
                        logging.warning(f'[playFile]{line}')
                        logging.warning('Not the same file error')
                        self.stopPlay(self.ERROR_TYPE_FILE_CHANGED)
                        self.playfile_error = False
                        break
                    else:
                        self.playfile_error = True
                time.sleep(1)
            # check playback process
            if self.PROCESSBAR_TAG in line and not self.isPlaying:
                logging.info('start playback')
                logging.debug(f'Play start - {line}')
                self.setStateSafe(True)
                time.sleep(3)
                self.setupDecodeType()
                logging.info(f'DecodeType {self.getDecodeType()}')
            # check if end of playback
            if (self.ONPAUSE_TAG in line or self.ONCOMPLETE_TAG in line or self.ONSTOP_TAG in line) and self.isPlaying:
                # if self.lastLogcat and abs(
                #         count_time(line[6:14].split(':')) - count_time(self.lastLogcat[6:14].split(':'))) < 2:
                #     continue
                # stop_play()
                break

            if self.randomSeekEnable:
                if time.time() - start_time > 70:
                    break
                if self.ONSEEKCOMPLETE_TAG in line and self.isPlaying:
                    self.RandomSeekCheck()

            if self.subTitleChkEnable and time.time() - start_time > 70:
                break
            # check if error in logcat
            if self.ONERROR_TAG in line:
                logging.warning(f'[onError]: {line}')
                self.stopPlay(self.ERROR_TYPE_VIDEO_PLAYER)
                self.play_error = False
                return
            # if self.PRINT_EXCEPTION_CRASH in line:
            #     logging.warning(f'crash: {line}')
            #     logging.debug('player crash')
            #     self.stopPlay(self.ERROR_TYPE_PLAYER_CRASH)
            #     self.crash = False
            #     return
            # check if eof in logcat
            if self.PRINT_EXCEPTION_EOF in line:
                logging.warning(f'EOF: {line}')
                logging.debug('logcat EOF')
                self.stopPlay(self.ERROR_TYPE_LOGCAT_ERR)
                self.eof = False
                return
        self.stopPlay(self.ERROR_TYPE_OK)
        time.sleep(1)
        # if drop:
        #     log.frameDropCheck()
        self.clear_logcat()

    def __repr__(self):
        return 'VideoPlayer-PlayBackCheck'
