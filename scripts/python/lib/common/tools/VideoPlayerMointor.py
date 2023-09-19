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

from lib.common.tools.FrameDropCheck import FrameDropCheck
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from lib.common.tools.YUV import YUV
from lib.common.system.ADB import ADB
from lib.common.tools.Demux import DemuxCheck


class VideoPlayerMonitor(ADB):
    """
    video player apk mointor

    Attributes:
        playfile_error : playfile status
        eof : eof status
        crash : logcat crash status
        play_error : playback error

    """

    def __init__(self):
        super(VideoPlayerMonitor, self).__init__()
        self.playfile_error = True
        self.eof = True
        self.crash = True
        self.play_error = True
        self.player_check = PlayerCheck_Base()
        self.yuv_thread_switch = True
        # self.lastLogcat = ''

    def set_up(self, player_type, source_type, yuv_enable=False, demux_enable=False, drop_check_enable=False, avsync_check_enable=False,
              random_seek_enable=False, subtitle_check_enable=False):
        """
        reset mointor status
        @param player_type: playback type
        @param source_type: source type
        @param yuv_enable: yuv check flag
        @param drop_check_enable: drop check flag
        @param avsync_check_enable:  avsync check flag
        @param random_seek_enable: random seek flag
        @param subtitle_check_enable: subtitle check flag
        @return: None
        """
        logging.info(
            f"[VideoPlayerMonitor][set_up]project_type:{source_type},player_type:{player_type}, yuv_enable:{yuv_enable},"
            f"drop_check_enable:{drop_check_enable},avsync_check_enable:{avsync_check_enable}, "
            f"random_seek_enable:{random_seek_enable}, subtitle_check_enable:{subtitle_check_enable}")
        self.player_type = player_type
        self.monitor_yuv_enable = yuv_enable
        self.monitor_dmx_enable = demux_enable
        self.drop_check_enable = drop_check_enable
        self.avsync_check_enable = avsync_check_enable
        self.random_seek_enable = random_seek_enable
        self.subtitle_check_enable = subtitle_check_enable
        self.source_type = source_type
        self.player_check.playerType = self.player_type
        if self.monitor_yuv_enable:
            self.yuv = YUV()
            self.yuv.open_yuv()
            self.yuv.yuvEnable = yuv_enable
            # self.yuv.local_player_check.playerType = player_type
        if self.drop_check_enable:
            self.drop_check = FrameDropCheck(self.serialnumber, self.logdir)

    def post_init(self):
        """
        set apk mointor tag
        @return: None
        """
        # self.yuv.local_player_check.reset()
        self.player_check.reset()
        self.player_check.TAG = 'VideoPlayer'
        # if self.player_type == self.yuv.local_player_check.PLAYER_TYPE_LOCAL:
        if self.player_type == self.player_check.PLAYER_TYPE_LOCAL:
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
        else:
            logging.info("Unknown playback type")
        #elif self.player_type == self.PLAYER_TYPE_YOUTUBE:
            ...
            # TODO:
        #elif self.player_type == self.PLAYER_TYPE_NETFLIX:
            ...
            # TODO:

    def get_logcat(self, playcommand_time="", yuv=False, drop=False):
        """
        @param playcommand_time:
        @param yuv:
        @param drop:
        @return:
        """
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

        # start decode and frame check thread
        if self.monitor_yuv_enable:
            self.player_check.set_AndroidVersion_R_checkpoint()
            if not self.yuv_thread_switch:
                logging.info("yuv threads are started")
            else:
               self.player_check.startDecodeChkThread()
               self.player_check.startFrameChkThread()
               self.yuv_thread_switch = False

        if self.avsync_check_enable:
            self.player_check.startAVSyncThread()
        if self.random_seek_enable and self.player_check.seek.seek_type == 'press_seek':
            self.player_check.seek.startSeekThread()
        if self.subtitle_check_enable and self.player_check.check_vdec_status('ammvdec_h264_v4'):
            self.subtitle.start_subtitle_thread()
        start_time = time.time()
        self.counter = 0
        # Get the keywords of the playback status from logcat
        logging.info('Start catch logcat')
        # self.logcat = self.popen('logcat -s %s' % self.TAG)
        # self.startFrameChkThread()
        if self.drop_check_enable:
            self.omx_logcat = self.drop_check.run()
            # omx_logcat = self.drop_check.catchLogcat()

        # analyze logcat
        while True:
            # if self.yuv.local_player_check.getErrorType() != 'OK':
            if self.player_check.getErrorType() != 'OK':
                # self.player_check.stopPlay()
                if self.monitor_yuv_enable:
                    self.player_check.stopPlay()
                    self.player_check.saveYUVinfo(self.player_check.getErrorType())
                elif self.monitor_dmx_enable:
                    self.back()
                # self.player_check.stopPlay(self.player_check.getErrorType())
                self.clear_logcat()
                # input('请确认异常后继续测试')
                return
            else:
                logging.debug("status ok!!!")

            # line = self.yuv.logcat_read_line()
            line = self.player_check.logcatReadLine()
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
                    # if self.yuv.local_player_check.path.strip() not in line:
                    if self.player_check.path.strip() not in line:
                        # logging.warning(f'videoName: ->{self.yuv.local_player_check.path}<-')
                        logging.warning(f'videoName: ->{self.player_check.path}<-')
                        logging.warning(f'[playFile]{line}')
                        logging.warning('Not the same file error')
                        # self.player_check.stopPlay()
                        if self.monitor_yuv_enable:
                            self.player_check.stopPlay()
                            self.player_check.saveYUVinfo(self.player_check.ERROR_TYPE_FILE_CHANGED)
                            # self.yuv.stop_local_play(self.yuv.local_player_check.ERROR_TYPE_FILE_CHANGED)
                        elif self.monitor_dmx_enable:
                            self.back()
                        self.playfile_error = False
                        break
                    else:
                        self.playfile_error = True
                time.sleep(1)
            else:
                logging.debug("start play ok")

            # check playback process
            # if self.PROCESSBAR_TAG in line and not self.yuv.local_player_check.isPlaying:
            if self.PROCESSBAR_TAG in line and not self.player_check.isPlaying:
                logging.info('start playback')
                logging.debug(f'Play start - {line}')
                # self.yuv.local_player_check.setStateSafe(True)
                self.player_check.setStateSafe(True)
                time.sleep(3)
                # self.yuv.local_player_check.setupDecodeType()
                self.player_check.setupDecodeType()
                # logging.info(f'DecodeType {self.yuv.local_player_check.getDecodeType()}')
                logging.info(f'DecodeType {self.player_check.getDecodeType()}')
            else:
                logging.debug("process ok")

            # check if end of playback
            # if (self.ONPAUSE_TAG in line or self.ONCOMPLETE_TAG in line or self.ONSTOP_TAG in line) and self.yuv.local_player_check.isPlaying:
            if (self.ONPAUSE_TAG in line or self.ONCOMPLETE_TAG in line or self.ONSTOP_TAG in line) and self.player_check.isPlaying:
                # if self.lastLogcat and abs(
                #         count_time(line[6:14].split(':')) - count_time(self.lastLogcat[6:14].split(':'))) < 2:
                #     continue
                # stop_play()
                break
            else:
                logging.debug("The play is not over yet")

            if self.random_seek_enable:
                if time.time() - start_time > 70:
                    break
                if self.ONSEEKCOMPLETE_TAG in line and self.player_check.isPlaying:
                    self.player_check.RandomSeekCheck()

            if self.subtitle_check_enable and time.time() - start_time > 70:
                break

            # check if error in logcat
            if self.ONERROR_TAG in line:
                logging.warning(f'[onError]: {line}')
                # self.player_check.stopPlay()
                if self.monitor_yuv_enable:
                    self.player_check.stopPlay()
                    self.player_check.saveYUVinfo(self.player_check.ERROR_TYPE_VIDEO_PLAYER)
                    # self.yuv.stop_local_play(self.yuv.local_player_check.ERROR_TYPE_VIDEO_PLAYER)
                elif self.monitor_dmx_enable:
                    self.back()
                self.play_error = False
                return
            else:
                logging.debug("logcat is normal")

            # if self.PRINT_EXCEPTION_CRASH in line:
            #     logging.warning(f'crash: {line}')
            #     logging.debug('player crash')
            #     self.stopPlay(self.ERROR_TYPE_PLAYER_CRASH)
            #     self.crash = False
            #     return

            # check if eof in logcat
            # if self.yuv.local_player_check.PRINT_EXCEPTION_EOF in line:
            if self.player_check.PRINT_EXCEPTION_EOF in line:
                logging.warning(f'EOF: {line}')
                logging.debug('logcat EOF')
                # self.player_check.stopPlay()
                if self.monitor_yuv_enable:
                    self.player_check.stopPlay()
                    self.player_check.saveYUVinfo(self.player_check.ERROR_TYPE_LOGCAT_ERR)
                    # self.yuv.stop_local_play(self.yuv.local_player_check.ERROR_TYPE_LOGCAT_ERR)
                if self.monitor_dmx_enable:
                    self.back()
                self.eof = False
                return
            else:
                logging.debug("logcat hasn't eof")

        # close play
        # self.yuv.stopPlay(self.yuv.local_player_check.ERROR_TYPE_OK)
        logging.info("stop play")
        if self.monitor_yuv_enable:
            self.player_check.stopPlay()
        if self.monitor_dmx_enable:
            self.back()
        logging.info("stop play success")
        if self.monitor_yuv_enable:
            self.player_check.saveYUVinfo(self.player_check.ERROR_TYPE_OK)
            # self.yuv.stop_local_play(self.yuv.local_player_check.ERROR_TYPE_OK)
        time.sleep(1)
        # if drop:
        #     log.frameDropCheck()
        self.player_check.reset()
        self.clear_logcat()

    def __repr__(self):
        return 'VideoPlayer-PlayBackCheck'
