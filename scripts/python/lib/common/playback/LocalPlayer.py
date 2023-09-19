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

import pytest
import uiautomator2 as u2
from lib import get_device
from lib.common.system.Permission import Permission
from lib.common.system.ADB import ADB
from lib.common.tools.LoggingTxt import log
from lib.common.tools.VideoPlayerMointor import VideoPlayerMonitor
from util.Decorators import stop_thread


class LocalPlayer(Permission, ADB):
    """
    LocalPlayer apk test lib

    Attributes:
        LOCALPLAYER_PACKAGE_TUPLE： local playback package tuple
        VIDEOPLAYER_APK_NAME: video player apk
        VIDEO_TAG_REGU: video type regular

        uuid: u-disk uuid
        path: u-disk video path
        play_from_list:
        source_type:
        localplayer:

    """

    LOCALPLAYER_PACKAGE_TUPLE = 'com.droidlogic.videoplayer', '.VideoPlayer'
    LOCALPLAYER_AMPLAYER_PACKAGE_TUPLE = 'com.droidlogic.exoplayer2.demo', 'com.droidlogic.videoplayer.MoviePlayer'
    VIDEOPLAYER_APK_NAME = 'VideoPlayer2.apk'
    VIDEO_TAG_REGU = r'\.rm|\.rmvb|\.avi|\.mkv|\.mp4|\.wmv|\.mov|\.flv|\.asf|\.3gp|\.mpg|\.mvc|\.m2ts|\.ts|\.swf|\.mlv|\.divx|\.3gp2|\.3gpp|\.h265|\.m4v|\.mts|\.tp|\.bit|\.webm|\.3g2|\.f4v|\.pmp|\.mpeg|\.vob|\.dat|\.m2v|\.iso|\.vp9|\.trp|\.bin|\.hm10'
    IPTV_PATH = 'setenforce 0;setprop vendor.media.ammediaplayer.enable 1;setprop iptv.streamtype 1'

    def __init__(self, uuid="", path="", play_from_list=False, source_type=""):
        super(LocalPlayer, self).__init__()
        self.uuid = uuid
        self.path = path
        self.play_from_list = play_from_list
        self.home()
        self.source_type = source_type
        # self.permission_check()
        self.localplayer = True
        # self.permission = Permission()

    def set_up(self, yuv_able=False, demux_able=False, drop_check_able=False, video_player_monitor_enable=False,
               random_seek_enable=False, play_3d_enable=False, av_sync_chk_enable=False, subtitle_chk_enable=False):
        """
        set up test env
        1. check u-disk status
        2. check video path
        3. create playerMonitor
        4. setup random and 3d video type command

        @param yuv_able: yuv fun control : boolean
        @param drop_check_able: drop fun control : boolean
        @param video_player_monitor_enable: video monitor control : boolean
        @param random_seek_enable: random seek control : boolean
        @param play_3d_enable: 3d video fun control : boolean
        @param av_sync_chk_enable: avsync fun control : boolean
        @param subtitle_chk_enable: subtitle fun control : boolean
        @return: None

        Raise：
            EnvironmentError('can not get uuid, no external storage was found')
            EnvironmentError("Can't find path , pls check then retry")
        """
        logging.info(
            f"[set_up]yuv_able:{yuv_able}, demux_able:{demux_able}, drop_check_able:{drop_check_able}, video_player_monitor_enable:{video_player_monitor_enable}, "
            f"random_seek_enable:{random_seek_enable}, play_3d_enable:{play_3d_enable},av_sync_chk_enable:{av_sync_chk_enable},"
            f"subtitle_chk_enable:{subtitle_chk_enable}")

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
        if self.play_from_list:
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

        self.yuv_enable = yuv_able
        self.demux_enable = demux_able
        self.drop_check_able = drop_check_able
        self.video_player_monitor_enable = video_player_monitor_enable
        self.random_seek_enable = random_seek_enable
        self.play_3d_enable = play_3d_enable
        self.av_sync_chk_enable = av_sync_chk_enable
        self.subtitle_chk_enable = subtitle_chk_enable

        # create playerMonitor
        if self.video_player_monitor_enable:
            self.video_player_monitor = VideoPlayerMonitor()
            self.video_player_monitor.set_up("Local", self.source_type, self.yuv_enable, self.demux_enable,
                                             self.drop_check_able, self.av_sync_chk_enable, self.random_seek_enable,
                                             self.subtitle_chk_enable)
            self.video_player_monitor.post_init()
            if self.yuv_enable or self.demux_enable:
                self.video_player_monitor.player_check.logcatStop()
                self.video_player_monitor.player_check.set_AndroidVersion_R_checkpoint()
        else:
            logging.info("VideoPlayerMonitor hasn't create")

        if self.demux_enable:
            self.run_shell_cmd(self.IPTV_PATH)
            from lib.common.tools.Demux import DemuxCheck
            self.demux_check = DemuxCheck()

        # random seek
        if self.random_seek_enable:
            self.random_seek_ext = ' --ez need_random_seek true'
            self.run_shell_cmd('setprop vendor.sys.vprandomseek.enable true')

        # 3d mode
        # 0:3doff, 1:3dlr, 2:3dtb, 3:3dfp
        if self.play_3d_enable:
            self.play_3d_ext = ' --ei 3d_mode 1 '

        # if self.subTitleChkEnable:
        #     subtitle_type = video["type"]

        # connect uiautomator2
        for serialnumber in get_device():
            self.d = u2.connect(serialnumber)

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
        self.permission_check(uiautomator_type="u2")
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
        self.run_shell_cmd('setenforce 0;setprop vendor.sys.videoplayer.debug true')

        # get VideoPlayer's logcat
        if self.video_player_monitor_enable:
            self.video_player_monitor.player_check.logcatStart()

        # scan video and playback
        for video in self.videoList:
            # prepare video
            if not re.search(self.VIDEO_TAG_REGU, video):  # filter video type ,must be mp4,ts,....
                continue
            logging.info('Playing : %s' % video)
            video_for_command = re.sub(r'([\s\(\)])', r'\\\1', video)

            if "vp9" in video_for_command.lower():
                self.video_player_monitor.videoType = "vp9"
            if self.video_player_monitor_enable:
                # self.playerMonitor.videoPath = video.strip()
                self.video_player_monitor.player_check.setName(video.strip())
                self.video_player_monitor.player_check.setPath(video.strip())

            # prepare for play command
            play_command = 'am start -n ' + self.LOCALPLAYER_PACKAGE_TUPLE[0] + '/' + self.LOCALPLAYER_PACKAGE_TUPLE[
                1] + ' -d file:/storage/' + self.uuid + self.path + video_for_command

            # handle play command with randomseek fun
            if self.random_seek_enable:
                if self.video_player_monitor.player_check.seek.seek_type != 'press_seek':
                    play_command += self.random_seek_ext

            # handle play command with 3d fun
            if self.play_3d_enable:
                play_command += self.play_3d_ext

            # start to play
            if self.demux_enable and re.findall(r".*.ts", video_for_command):
                self.demux_check.start_get_dmx_logcat_thread(video_for_command)
            info = self.run_shell_cmd(play_command)[1]
            playcommand_time = time.strftime("%H:%M:%S")  # time.strftime("%H:%M:%S")
            logging.info(f'playcommand_time:{time.strftime("%H:%M:%S")}, Play Command {play_command}')
            time.sleep(10)
            # get dmx video and audio pid
            if self.demux_enable:
                dmx_video_pid, dmx_audio_pid = self.video_player_monitor.player_check.check_demux()
            # res = playerCheck.run_check_main_thread(30)
            if self.video_player_monitor_enable:
                if not self.video_player_monitor.player_check.check_vfm_map:
                    logging.info(f"check_vfm_map:{self.video_player_monitor.player_check.check_vfm_map}")
                    res = False
            # TODO @chao.li : add more except situation
            if 'error' in info:  # playback command with error
                logging.warning('Error! Disable to playback')
                if self.video_player_monitor_enable:
                    self.video_player_monitor.error = 'Error'
                    log.writeResultTXT(self.video_player_monitor.player_check.getvideoName(),
                                       self.video_player_monitor.player_check.videoType,
                                       self.video_player_monitor.player_check.decodeType,
                                       self.video_player_monitor.error)
                continue
            # time.sleep(1)

            # analyze VideoPlayer's logcat
            if self.video_player_monitor_enable:
                logging.info('playerMonitor')
                self.video_player_monitor.error = 'OK'
                self.video_player_monitor.get_logcat(playcommand_time=playcommand_time)
                if not (self.video_player_monitor.playfile_error or
                        self.video_player_monitor.eof or
                        self.video_player_monitor.play_error or
                        self.video_player_monitor.avSync):
                    res = False

            if self.demux_enable:
                if re.findall(r".*.ts", video_for_command):
                    video = video.strip(".ts")
                    destination_path = self.set_dest_path("~/video")
                    self.close_demux()
                    self.pull(f"/storage/{self.uuid}" + self.path + video_for_command, destination_path)
                    dmx_video = True if self.demux_check.analysis_dmx_video_info(dmx_video_pid, destination_path + "/" + video_for_command, f"packet_video_{video}.json") else False
                    dmx_audio = True if self.demux_check.analysis_dmx_audio_info(dmx_audio_pid, destination_path + "/" + video_for_command, f"packet_audio_{video}.json") else False
                    if (dmx_video is False) or (dmx_audio is False):
                        res = False

        # close app and write result
        self.app_stop(self.LOCALPLAYER_PACKAGE_TUPLE[0])
        self.stop_logcat()
        if self.yuv_enable:  # stop yuv
            self.analysis_yuv_data()

        # if self.randomSeekEnable:
        #     if not self.videoplayerMonitor.seek.res:
        #         res = False
        time.sleep(5)
        # for i in threading.enumerate()[1:]:
        #     logging.debug(i.__dict__)
        #         stop_thread(i)
        # logging.info(f"res:{res}")
        return res

    def set_dest_path(self, dest):
        destination_path = dest
        return destination_path

    def stop_logcat(self):
        if self.video_player_monitor_enable:  # stop video player monitor
            self.video_player_monitor.player_check.logcatStop()

    def analysis_yuv_data(self):
        log.write_yuv_excel()
        log.check_yuv_data()

    def close_demux(self):
        self.demux_check.close_file()

    def audio_play(self):
        res = True
        logging.info('start to play')
        self.clear_logcat()
        self.run_shell_cmd('setprop vendor.sys.videoplayer.debug true')
        if self.video_player_monitor_enable:
            self.video_player_monitor.yuv.local_logcat_start()
        play_command = 'am start -n ' + self.LOCALPLAYER_PACKAGE_TUPLE[0] + '/' + self.LOCALPLAYER_PACKAGE_TUPLE[
            1] + ' -d file:/storage/' + self.uuid + self.path
        for video in self.videoList:
            if not re.search(self.VIDEO_TAG_REGU, video):
                continue
            video_for_command = re.sub(r'([\s\(\)])', r'\\\1', video)
            play_command += video_for_command
            logging.info('Playing : %s' % video)
        if self.random_seek_enable:
            play_command += self.random_seek_ext
        if self.play_3d_enable:
            play_command += self.play_3d_ext
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
