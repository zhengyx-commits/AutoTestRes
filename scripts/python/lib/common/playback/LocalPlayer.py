#!/usr/bin python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/24 16:43
# @Author  : Coco
# @Site    : SH #5-389
# @File    : LocalPlayer.py
# @Email   : chao.li@amlogic.com
# @Software: PyCharm


import logging
import re
import threading
import time
from subprocess import CalledProcessError

import uiautomator2 as u2

from lib.common.playback import Environment_Detection
from lib.common.system.Permission import Permission
from lib.common.system.ADB import ADB
from lib.common.tools.LoggingTxt import log
from lib.common.tools.VideoPlayerMointor import VideoPlayerMonitor
from util.Decorators import stop_thread


class LocalPlayer(Environment_Detection):
    '''
    LocalPlayer apk test lib

    Attributes:
        LOCALPLAYER_PACKAGE_TUPLE： local playback package tuple
        VIDEOPLAYER_APK_NAME: video player apk
        VIDEO_TAG_REGU: video type regular

        uuid: u-disk uuid
        path: u-disk video path
        playFromList:
        sourceType:
        localplayer:

    '''

    LOCALPLAYER_PACKAGE_TUPLE = 'com.droidlogic.videoplayer', '.VideoPlayer'
    VIDEOPLAYER_APK_NAME = 'VideoPlayer2.apk'
    VIDEO_TAG_REGU = r'\.rm|\.rmvb|\.avi|\.mkv|\.mp4|\.wmv|\.mov|\.flv|\.asf|\.3gp|\.mpg|\.mvc|\.m2ts|\.ts|\.swf|\.mlv|\.divx|\.3gp2|\.3gpp|\.h265|\.m4v|\.mts|\.tp|\.bit|\.webm|\.3g2|\.f4v|\.pmp|\.mpeg|\.vob|\.dat|\.m2v|\.iso|\.vp9|\.trp|\.bin|\.hm10'

    def __init__(self, uuid="", path="", playFromList=False, sourceType=""):
        super(LocalPlayer, self).__init__()
        self.uuid = uuid
        self.path = path
        self.playFromList = playFromList
        self.home()
        self.sourceType = sourceType
        # self.permission_check()
        self.localplayer = True
        self.android_s_so_check()


    def setup(self, yuv_able=False, dropcheck_able=False, videoplayerMonitorEnable=False,
              randomSeekEnable=False, play3dEnable=False, avSyncChkEnable=False, subTitleChkEnable=False):
        '''
        set up test env
        1. check u-disk status
        2. check video path
        3. create playerMonitor
        4. setup random and 3d video type command

        @param yuv_able: yuv fun control : boolean
        @param dropcheck_able: drop fun control : boolean
        @param videoplayerMonitorEnable: video mointor control : boolean
        @param randomSeekEnable: random seek control : boolean
        @param play3dEnable: 3d video fun control : boolean
        @param avSyncChkEnable: avsync fun control : boolean
        @param subTitleChkEnable: subtitle fun control : boolean
        @return: None

        Raise：
            EnvironmentError('can not get uuid, no external storage was found')
            EnvironmentError("Can't find path , pls check then retry")
        '''
        logging.info(
            f"[setup]YUVEnable:{yuv_able}, dropChkEnable:{dropcheck_able}, playerMonitorEnable:{videoplayerMonitorEnable}, "
            f"randomSeekEnable:{randomSeekEnable}, play3dEnable:{play3dEnable},avSyncChkEnable:{avSyncChkEnable},"
            f"subTitleChkEnabl:{subTitleChkEnable}")

        # Clear boot video
        self.run_shell_cmd('pm disable com.google.android.tungsten.setupwraith')

        # prepare uuid
        if not self.uuid:
            try:
                self.uuid = self.getUUID().strip()
                logging.info(f"self.uuid: {self.uuid}")
            except AttributeError:
                raise EnvironmentError('can not get uuid, no external storage was found')

        # scan for video list
        if self.playFromList:
            logging.info('play from list path: %s' % self.path)
            if not self.path:
                logging.warning('can not find path: %s' % self.path)
                exit()
            try:
                self.videoList = self.getVideoList()
            except AttributeError:
                raise EnvironmentError("Can't find path , pls check then retry")
        else:
            video = self.path.split("/")[-1]
            self.videoList = [video]
            self.path = self.path[0:self.path.find(video)]

        self.yuvEnable = yuv_able
        self.dropChkEnable = dropcheck_able
        self.videoplayerMonitorEnable = videoplayerMonitorEnable
        self.randomSeekEnable = randomSeekEnable
        self.play3dEnable = play3dEnable
        self.avSyncChkEnable = avSyncChkEnable
        self.subTitleChkEnable = subTitleChkEnable

        # create playerMonitor
        if self.videoplayerMonitorEnable:
            self.videoplayerMonitor = VideoPlayerMonitor()
            self.videoplayerMonitor.setup(self.videoplayerMonitor.PLAYER_TYPE_LOCAL, self.sourceType, self.yuvEnable,
                                          self.dropChkEnable, self.avSyncChkEnable, self.randomSeekEnable,
                                          self.subTitleChkEnable)
            self.videoplayerMonitor.postInit()
            self.videoplayerMonitor.logcatStop()
            self.videoplayerMonitor.set_AndroidVersion_R_checkpoint()

        # random seek
        if self.randomSeekEnable:
            self.randomSeekExt = ' --ez need_random_seek true'
            self.run_shell_cmd('setprop vendor.sys.vprandomseek.enable true')

        # 3d mode
        # 0:3doff, 1:3dlr, 2:3dtb, 3:3dfp
        if self.play3dEnable:
            self.play3dExt = ' --ei 3d_mode 1 '

        # if self.subTitleChkEnable:
        #     subtitle_type = video["type"]

        # connect uiautomator2
        self.d = u2.connect(self.serialnumber)

    def getVideoList(self):
        '''
        get video list from u-disk video path
        @return: video name : list [str]
        '''
        try:
            videoList = self.run_shell_cmd('ls /storage/' + self.uuid + self.path + ' |grep \\\\.')[1]
            # logging.info(f"videolist:{videoList}")
        except CalledProcessError:
            logging.warning("Can't find path , pls check then retry")
        else:
            return list(videoList.split('\n'))

    def check_videoplayerapk_exist(self):
        '''
        check video player apk status
        @return: apk status : boolean
        '''
        return True if self.LOCALPLAYER_PACKAGE_TUPLE[0] in self.checkoutput('pm list packages') else False

    def permissioncheck(self):
        '''
        check localplayer permission status
        @return: None
        '''

        if not self.check_videoplayerapk_exist():
            logging.info("apk not exist,begin to install")
            assert self.install_apk("apk/" + self.VIDEOPLAYER_APK_NAME)
            logging.info("install success")
        else:
            logging.info("apk already exist")
        self.start_activity(*self.LOCALPLAYER_PACKAGE_TUPLE)
        self.permission.permission_check(uiautomator_type="u1")
        self.home()
        self.app_stop(self.LOCALPLAYER_PACKAGE_TUPLE[0])

    def setlocalplayer_flag(self, flag):
        '''
        set local player flag
        @param flag: flag : boolean
        @return: None
        '''
        self.localplayer = True if flag else False

    def startPlay(self):
        '''
        start local play
        @return: res status : boolean
        '''
        res = True
        logging.info('start to play')
        self.clear_logcat()
        self.run_shell_cmd('setprop vendor.sys.videoplayer.debug true')

        if self.videoplayerMonitorEnable:
            self.videoplayerMonitor.logcatStart()
        for video in self.videoList:
            if not re.search(self.VIDEO_TAG_REGU, video):  # filter video type ,must be mp4,ts,....
                continue
            video_for_command = re.sub(r'([\s\(\)])', r'\\\1', video)
            if "vp9" in video_for_command.lower():
                self.videoplayerMonitor.videoType = "vp9"
            if self.videoplayerMonitorEnable:
                # self.playerMonitor.videoPath = video.strip()
                self.videoplayerMonitor.setName(video.strip())
                self.videoplayerMonitor.setPath(video.strip())

            # prepare for play command
            play_command = 'am start -n ' + self.LOCALPLAYER_PACKAGE_TUPLE[0] + '/' + self.LOCALPLAYER_PACKAGE_TUPLE[
                1] + ' -d file:/storage/' + self.uuid + self.path + video_for_command

            if self.randomSeekEnable:  # handle play command with randomseek fun
                if self.videoplayerMonitor.seek.seek_type != 'press_seek':
                    play_command += self.randomSeekExt

            if self.play3dEnable:  # handle play command with 3d fun
                play_command += self.play3dExt
            logging.info('Playing : %s' % video)
            # start to play
            info = self.run_shell_cmd(play_command)[1]
            playcommand_time = time.strftime("%H:%M:%S")  # time.strftime("%H:%M:%S")
            logging.info(f'playcommand_time:{time.strftime("%H:%M:%S")}, Play Command {play_command}')
            time.sleep(10)
            if self.videoplayerMonitorEnable:
                if not self.videoplayerMonitor.check_vfm_map:
                    logging.info(f"check_vfm_map:{self.videoplayerMonitor.check_vfm_map}")
                    res = False
            # TODO @chao.li : add more except situation
            if 'error' in info:  # playback command with error
                logging.warning('Error! Disable to playback')
                if self.videoplayerMonitorEnable:
                    self.videoplayerMonitor.error = 'Error'
                    log.writeResultTXT(self.videoplayerMonitor.getvideoName(), self.videoplayerMonitor.videoType,
                                       self.videoplayerMonitor.decodeType, self.videoplayerMonitor.error)
                continue
            time.sleep(1)
            if self.videoplayerMonitorEnable:
                logging.info('playerMonitor')
                self.videoplayerMonitor.error = 'OK'
                self.videoplayerMonitor.get_logcat(playcommand_time=playcommand_time)  # analyze logcat
                if not (self.videoplayerMonitor.playfile_error or
                        self.videoplayerMonitor.eof or
                        self.videoplayerMonitor.play_error or
                        self.videoplayerMonitor.avSync):
                    res = False
        self.app_stop(self.LOCALPLAYER_PACKAGE_TUPLE[0])
        if self.videoplayerMonitorEnable:  # stop video player monitor
            self.videoplayerMonitor.logcatStop()
        if self.yuvEnable:  # stop yuv
            log.write_yuv_excel()
            log.check_yuv_data()
        # if self.randomSeekEnable:
        #     if not self.videoplayerMonitor.seek.res:
        #         res = False
        time.sleep(5)
        # for i in threading.enumerate()[1:]:
        #     logging.debug(i.__dict__)
        #         stop_thread(i)
        # logging.info(f"res:{res}")
        return res

    def audio_play(self):
        res = True
        logging.info('start to play')
        self.clear_logcat()
        self.run_shell_cmd('setprop vendor.sys.videoplayer.debug true')
        if self.videoplayerMonitorEnable:
            self.videoplayerMonitor.logcatStart()
        play_command = 'am start -n ' + self.LOCALPLAYER_PACKAGE_TUPLE[0] + '/' + self.LOCALPLAYER_PACKAGE_TUPLE[
            1] + ' -d file:/storage/' + self.uuid + self.path
        for video in self.videoList:
            if not re.search(self.VIDEO_TAG_REGU, video):
                continue
            video_for_command = re.sub(r'([\s\(\)])', r'\\\1', video)
            play_command += video_for_command
            logging.info('Playing : %s' % video)
        if self.randomSeekEnable:
            play_command += self.randomSeekExt
        if self.play3dEnable:
            play_command += self.play3dExt
        # start to play
        self.run_shell_cmd(play_command)
        # playcommand_time = time.strftime("%H:%M:%S")  # time.strftime("%H:%M:%S")
        logging.info(f'playcommand_time:{time.strftime("%H:%M:%S")}, Play Command {play_command}')
        time.sleep(15)
        # audio format
        audio_format = self.run_shell_cmd("dumpsys media.audio_flinger |"
                                          "grep 'HAL format' |awk '{print $4}' | sed -n 2p")[1]
        error_data = re.compile(audio_format)
        error_data = error_data.search('(AUDIO_FORMAT_PCM_16_BIT)')
        if error_data:
            logging.info('-----Failed to correctly identify the playback format : %s' % error_data)
            assert log.check_result_error() == "Fail"
        else:
            logging.info('+++++audio format ----> %s ' % audio_format)
        time.sleep(25)
        self.app_stop(self.LOCALPLAYER_PACKAGE_TUPLE[0])
