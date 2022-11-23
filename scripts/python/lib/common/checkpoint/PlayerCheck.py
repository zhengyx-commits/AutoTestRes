#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/19 2022/4/19
# @Author  : yongbo.shao
# @Site    : SH #5
# @File    : PlayerCheck.py
# @Email   : yongbo.shao@amlogic.com
# @Software: PyCharm

import fcntl
import logging
import os
import re
import signal
import subprocess
import threading
import time
from datetime import datetime

import pytest
import threadpool
import operator

from lib import CheckAndroidVersion
from lib.common import config_yaml
from lib.common.checkpoint.MediaCheck_Keywords import MediaCheckKeywords
from lib.common.system.ADB import ADB
from lib.common.tools.Seek import SeekFun
from lib.common.tools.LoggingTxt import log
from lib.common.system.NetworkAuxiliary import getIfconfig
from util.Decorators import set_timeout, stop_thread
from . import Check


def _bytes_repr(c):
    """py2: bytes, py3: int"""
    if not isinstance(c, int):
        c = ord(c)
    return '\\x{:x}'.format(c)


def _text_repr(c):
    d = ord(c)
    if d >= 0x10000:
        return '\\U{:08x}'.format(d)
    else:
        return '\\u{:04x}'.format(d)


def backslashreplace_backport(ex):
    s, start, end = ex.object, ex.start, ex.end
    c_repr = _bytes_repr if isinstance(ex, UnicodeDecodeError) else _text_repr
    return ''.join(c_repr(c) for c in s[start:end]), end


class PlayerCheck(ADB, Check, CheckAndroidVersion):
    '''
    Base player checkpoint, now support OTT/OTT hybrid S IPTV/TV/IPTV
    '''
    _instance_lock = threading.Lock()

    # checkpoints
    VFM_MAP_COMMAND = "cat /sys/class/vfm/map | head -n 20"
    SOFT_DECODE_COMMAND = "top -n 1|grep -v 'grep'|grep swcodec"
    VIDEO_SYNC_COMMAND = "cat /sys/class/tsync/pts_video"
    DISPLAYER_FRAME_COMMAND = "cat /sys/module/amvideo/parameters/display_frame_count"
    VDEC_STATUS_COMMAND = "cat /sys/class/vdec/vdec_status | grep 'device name' "
    CODEC_MM_DUMP_COMMAND = "cat /sys/class/codec_mm/codec_mm_dump"
    VIDEO_TYPE_COMMAND = "cat /sys/class/vdec/core"
    DISPLAY_MODE = "cat /sys/class/display/mode"
    FRAME_RATE = "cat /sys/class/video/frame_rate"
    V4LVIDEO_PUT_COUNT = "cat /sys/class/v4lvideo/put_count"
    V4LVIDEO_GET_COUNT = "cat /sys/class/v4lvideo/get_count"
    V4LVIDEO_Q_COUNT = "cat /sys/class/v4lvideo/q_count"
    V4LVIDEO_DQ_COUNT = "cat /sys/class/v4lvideo/dq_count"
    DISABLE_VIDEO = "cat /sys/class/video/disable_video"
    REMOTE_ENABLE = "echo 0x01 > /sys/class/remote/amremote/protocol"
    REMOTE_DISABLE = "echo 0x02 > /sys/class/remote/amremote/protocol"
    AUDIO_APPL_PTR = "cat /proc/asound/card0/pcm*/sub0/status"
    FRAME_WIDTH_COMMDND = "cat /sys/class/video_poll/frame_width"
    FRAME_HEIGHT_COMMAND = "cat /sys/class/video_poll/frame_height"
    DEMUX_FILTER = "cat /sys/class/dmx/dump_filter"

    # player type
    PLAYER_TYPE_LOCAL = "Local"
    PLAYER_TYPE_YOUTUBE = "Youtube"
    PLAYER_TYPE_NETFLIX = "Netflix"

    # decode type
    DECODE_TYPE_NONE = "NONE"
    DECODE_TYPE_HW = "HW"
    DECODE_TYPE_SW = "SW"

    # abnormal type
    ERROR_TYPE_OK = "OK"
    ERROR_TYPE_VFM_MAP = "Error: vfm error"
    ERROR_TYPE_FRAME_MAP = "Error: frame error"
    ERROR_TYPE_TIME_OUT = "Error: time out"
    ERROR_TYPE_PLAYER_CRASH = "Error: player crash"
    ERROR_TYPE_LOGCAT_ERR = "Error: logcat error"
    ERROR_TYPE_FILE_CHANGED = "Error: Not this file"
    ERROR_TYPE_VIDEO_PLAYER = "Error: Error in videoplayer"
    ERROR_TYPE_AVSYNC = "Error: AV Sync failed"

    # yuv abnormal type
    YUV_CHKSUM_NONE = ""
    YUV_CHKSUM_ERR = "yuvsum:error"
    YUV_CHKSUM_SW_DECODE = "yuvsum:soft-decode"

    # abnormal type log
    # PRINT_EXCEPTION_CRASH = 'beginning of crash'
    PRINT_EXCEPTION_EOF = "unexpected EOF"

    # avsync logcat
    AVSYNC_IPTV_LOG = "logcat -s kernel"
    AVSYNC_OTT_LOG = "logcat -s NU-AmNuPlayerRenderer"
    AVSYNC_TV_LOG = "logcat -s NU-AmNuPlayerRenderer"

    def __init__(self, playerNum=1):
        ADB.__init__(self, "Player", unlock_code="", stayFocus=True)
        Check.__init__(self)
        CheckAndroidVersion.__init__(self)
        self.mediacheck_keywords = MediaCheckKeywords()
        self.lock = threading.Lock()
        self.__playerNum = playerNum
        self.sourceType = ""
        self.yuvEnable = None
        self.yuv = None
        self.playerType = ""
        self.logcat = ""
        self.logcatOpened = False
        self.reset()
        self.exitcode = 0
        self.abnormal_observer_list = []
        self.vid_dmx_info_list = []
        self.aud_dmx_info_list = []
        self.hwc_logtime_pts_diff = 0
        self.count = 0
        self.video_type = ""

    def set_AndroidVersion_R_checkpoint(self):
        if self.getprop(self.get_android_version()) >= "30" or self.videoType == "vp9" or (
                self.sourceType == "tvpath"):
            logging.info("Android Version for this product is R or test type is tvpath")
            self.DISPLAYER_FRAME_COMMAND = "cat /sys/class/video_composer/receive_count"

    def check_logcat_output_keywords(self, keywords, log, timeout, name="", getDuration=False):
        logging.info(f"name is :{name}")
        self.expand_logcat_capacity()
        counter = 0
        flag_check_logcat_output_keywords = False
        checked_log_dict = {}
        checked_log_list = []
        logging.info("check logcat output")
        logging.info("start abnormal thread")
        self.abnormal_threadpool()
        start_time = time.time()
        if not self.check_player_path():
            logging.info("Not IPTV path!!!")
            return flag_check_logcat_output_keywords, checked_log_dict
        print('adb -s ' + f'{self.serialnumber}' + ' ' + f'{log}')
        logfilter = 'adb -s ' + self.serialnumber + ' ' + log

        p = subprocess.Popen(logfilter.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        flags = fcntl.fcntl(p.stdout, fcntl.F_GETFL)
        flags |= os.O_NONBLOCK
        fcntl.fcntl(p.stdout, fcntl.F_SETFL, flags)
        logging.info(f"keywords: {keywords}")
        while time.time() - start_time < timeout:
            # if check abnormal in thread, should exit
            if self.exitcode == 1:
                flag_check_logcat_output_keywords = False
                return flag_check_logcat_output_keywords, checked_log_dict
            if p:
                line = p.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                #logging.debug(f"line: {line}")
                for keyword in keywords:
                    if keyword in line:
                        logging.info(f"check_logcat_output_keywords keyword: {keyword}")
                        if (getDuration is True) or (name == "check_startPlay"):
                            checked_log_list.append(line)
                        else:
                            checked_log_dict[keyword] = line
                        counter += 1
            if counter == len(keywords):
                flag_check_logcat_output_keywords = True
                self.kill_logcat_pid()
                p.kill()
                p.wait()
                p = None
                # os.killpg(p.pid, signal.SIGTERM)
                break
            #else:
            #    logging.debug("retry")
        # if flag_check_logcat_output_keywords:
            # logging.info("check kpi true")
            # flag_kpi = self.check_kpi(keywords, start_time)
            # if not flag_kpi:
            #     flag_check_logcat_output_keywords = False
            #     self.checked_log_dict = checked_log_dict
            #     return flag_check_logcat_output_keywords

        if (getDuration is True) or (name == "check_startPlay"):
            checked_log_dict["keyword"] = checked_log_list
        self.checked_log_dict = checked_log_dict
        logging.info(f"{name} keywords found:{flag_check_logcat_output_keywords}")
        logging.info(f"self.checked_log_dict: {self.checked_log_dict}")
        return flag_check_logcat_output_keywords, self.checked_log_dict

    def set_check_keyword(self, cmd, keywords, name, timeout, getDuration=False):
        flag_check_logcat_output_keywords = False
        checked_log_dict = {}
        checked_log_list = []
        counter = 0
        start_time = time.time()
        pytest.device._adblogcat_reader.reset_flag()
        pytest.device._adblogcat_reader.set_check_keywords(keywords)
        if not cmd:
            logging.info("pls set player control command")
            return
        logging.info(f"cmd: {cmd}")
        self.run_shell_cmd(cmd)
        if not self.check_player_path():
            logging.info("Not IPTV path!!!")
            return flag_check_logcat_output_keywords, checked_log_dict
        for keyword in keywords:
            while time.time() - start_time < timeout:
                outputValue = pytest.device._adblogcat_reader.outputDict.get(keyword)
                if outputValue:
                    logging.info(f"outputValue: {outputValue}")
                    if (getDuration is True) or (name == "check_startPlay"):
                        checked_log_list.append(outputValue)
                    else:
                        checked_log_dict[keyword] = outputValue
                    counter += 1
                    break
        if counter == len(keywords):
            flag_check_logcat_output_keywords = True
        else:
            logging.debug("retry")
        self.abnormal_threadpool()
        # check KPI
        if flag_check_logcat_output_keywords:
            self.checked_log_dict = checked_log_dict
            # logging.info("check kpi true")
            flag_kpi = self.check_kpi(keywords, start_time)
            if not flag_kpi:
                # flag_check_logcat_output_keywords = False
                return flag_check_logcat_output_keywords
        logging.info(f"{name} keywords found:{flag_check_logcat_output_keywords}")
        logging.info(f"self.checked_log_dict: {self.checked_log_dict}")

    def get_startkpi_time(self):
        return self.__start_kpi_time

    def check_kpi(self, keywords, start_time):
        # logging.info(f"keywords-----------:{keywords}")
        flag_kpi = False
        if keywords == self.mediacheck_keywords.START_KEYWORDS[-1:]:
            startPlay_time = time.time() - start_time
            self.__start_kpi_time = startPlay_time
            if startPlay_time < self.get_startplay_kpitime():
                logging.info(f"start play time less than 2s:{startPlay_time}")
                flag_kpi = True
            else:
                logging.info(f"start play time more than 2s:{startPlay_time}")
        # check switch channel KPI
        elif keywords == self.mediacheck_keywords.SWITCH_CHANNEL_KEYWORDS:
            switchChannel_time = time.time() - start_time
            if switchChannel_time < self.get_switchchannel_kpitime():
                logging.info(f"switch channel time less than 3s:{switchChannel_time}")
                flag_kpi = True
            else:
                logging.info(f"switch channel time less than 3s:{switchChannel_time}")
        else:
            flag_kpi = True
        return flag_kpi

    def check_common_threadpool(self, timeout=""):
        flag_common_threadpool = True
        if not timeout:
            timeout = self.get_checkavsync_stuck_time()
        logging.info(f"start common thread: {timeout}")
        self.common_threadpool()
        start_time = time.time()
        # avsync and stuck check time need check during playing
        while time.time() - start_time < timeout:
            if self.get_abnormal_observer():
                flag_common_threadpool = False
                break
        # if self.get_abnormal_observer():
        #     flag_common_threadpool = False
        return flag_common_threadpool

    def check_abnormal_flag(self):
        flag = True
        # logging.info("start abnormal thread")
        self.abnormal_threadpool()
        return flag

    def get_current_playback_resolution(self):
        '''
        get current video resolution
        @return: height , width : tuple :int
        '''
        width = self.checkoutput(self.FRAME_HEIGHT_COMMAND)
        logging.info(f'width {width}')
        height = self.checkoutput(self.FRAME_WIDTH_COMMDND)
        logging.info(f'height {height}')
        return int(height), int(width)

    def get_checktime(self):
        p_conf_time = config_yaml.get_note("conf_checktime").get("time")
        p_conf_dc_time = config_yaml.get_note("conf_checktime").get("dc_time")
        return p_conf_time, p_conf_dc_time

    def get_checkabnormaltime(self):
        p_conf_abnormal_time = config_yaml.get_note("conf_checktime").get("abnormal_time")
        return p_conf_abnormal_time

    def get_checkavsync_stuck_time(self):
        p_conf_avsync_stuck_time = config_yaml.get_note("conf_checktime").get("avsync_stuck_time")
        return p_conf_avsync_stuck_time

    def get_checkstuck_refs(self):
        p_conf_lost_frame_count = config_yaml.get_note("conf_reference").get("lostFrameCount")
        p_conf_duration_diff = config_yaml.get_note("conf_reference").get("durationDiff")
        return p_conf_lost_frame_count, p_conf_duration_diff

    def get_avsyncdiffreference(self):
        p_conf_avDiff = config_yaml.get_note("conf_reference").get("avDiff")
        p_conf_audioDiff = config_yaml.get_note("conf_reference").get("audioDiff")
        p_conf_DiffCount= config_yaml.get_note("conf_reference").get("DiffCount")
        return p_conf_avDiff, p_conf_audioDiff, p_conf_DiffCount

    def get_startplay_kpitime(self):
        p_conf_startplay_time = config_yaml.get_note("conf_kpitime").get("start_play_time")
        return p_conf_startplay_time

    def get_switchchannel_kpitime(self):
        p_conf_switchchannel_time = config_yaml.get_note("conf_kpitime").get("switch_channel_time")
        return p_conf_switchchannel_time

    def check_startPlay(self, keywords="", logFilter="", getDuration=False, **kwargs):
        """
        check start play, include PIP way
        :param cmd: type: string, apk broadcast command
        :param keywords: type: string, default param, specific keywords as below
        :param logFilter: type: string, default param, specific keywords as below
        :param during: type: int, check time by run_check_main_thread api
        :return: type: tuple, (flag_check_logcat_output_keywords: boolean, self.checked_log_dict: checked log dict)
        """
        self.reset()
        if not keywords:
            keywords = self.prepare_keywords(getDuration)
        if not logFilter:
            if self.__playerNum == 3 or self.__playerNum == 4:
                logFilter = self.mediacheck_keywords.MULTIPLAYER_LOGCAT
            else:
                logFilter = self.mediacheck_keywords.AMP_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_startPlay.__name__, getDuration, **kwargs)

    def create_network_auxiliary(self):
        network_interface = ""
        iplist = getIfconfig()
        if "192.168.1.246" in iplist:
            network_interface = "eth0"
        else:
            network_interface = "eth0"
        return network_interface

    def offline_network(self, interface):
        self.run_shell_cmd(f"ifconfig {interface} down")
        return interface

    def restore_network(self, interface):
        self.run_shell_cmd(f"ifconfig {interface} up")

    def check_disable_video(self):
        """
        check whether video layer is covered by osd layer
        """
        disable_video = self.run_shell_cmd(self.DISABLE_VIDEO)[1]
        if disable_video == "0":
            return True
        else:
            return False

    def prepare_keywords(self, getDuration):
        if getDuration:
            """
            check file total length after call check_startPlay api
            """
            if self.__playerNum == 1:
                keywords = self.mediacheck_keywords.START_KEYWORDS.copy()
                keywords[0] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[0])[0]
            elif self.__playerNum == 2:
                keywords = self.mediacheck_keywords.START2PLAYER_KEYWORDS.copy()
                keywords[0] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[0])[0]
                keywords[1] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[1])[0]
            elif self.__playerNum == 3:
                keywords = self.mediacheck_keywords.START3PLAYER_KEYWORDS.copy()
                keywords[0] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[0])[0]
                keywords[1] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[1])[0]
                keywords[2] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[2])[0]
            else:
                keywords = self.mediacheck_keywords.START4PLAYER_KEYWORDS.copy()
                keywords[0] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[0])[0]
                keywords[1] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[1])[0]
                keywords[2] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[2])[0]
                keywords[3] = re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*",
                                         keywords[3])[0]
        else:
            if self.__playerNum == 1:
                keywords = self.mediacheck_keywords.START_KEYWORDS[-1:]
            elif self.__playerNum == 2:
                keywords = self.mediacheck_keywords.START2PLAYER_KEYWORDS[-2:]
            elif self.__playerNum == 3:
                keywords = self.mediacheck_keywords.START3PLAYER_KEYWORDS[-3:]
            else:
                keywords = self.mediacheck_keywords.START4PLAYER_KEYWORDS[-4:]
        return keywords

    def check_pause(self, keywords="", logFilter="", pause_playerNum=0):
        """
        check pause, include PIP way
        :param pause_playerNum: specific pause playerNum, the first player:0; the second player:1; the third player:2;
                                the forth player:3
        other params are the same as check_startPlay
        """
        # self.reset()
        self.pause = True
        self.pause_playerNum = pause_playerNum
        if not keywords:
            keywords = self.mediacheck_keywords.PAUSE_KEYWORDS
        if not logFilter:
            logFilter = self.mediacheck_keywords.PAUSE_RESUME_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_pause.__name__)

    def check_resume(self, keywords="", logFilter="", resume_playerNum=0):
        """
        check resume, include PIP way
        :param resume_playerNum: specific resume playerNum, the first player:0; the second player:1; the third player:2;
                                 the forth player:3
        other params are the same as check_startPlay
        """
        # self.reset()
        self.resume_playerNum = resume_playerNum
        if not keywords:
            keywords = self.mediacheck_keywords.RESUME_KEYWORDS
        if not logFilter:
            logFilter = self.mediacheck_keywords.PAUSE_RESUME_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_resume.__name__)

    def get_check_api_result(self, keywords, logFilter, name, getDuration=False, **kwargs):
        timeout = 0
        # logging.info(f"kwargs: {kwargs.keys(), kwargs.values()}")
        if len(kwargs) != 0:
            for k, v in kwargs.items():
                timeout = v
        flag_check_logcat_output_keywords, self.checked_log_dict = self.check_logcat_output_keywords(keywords, logFilter, self.get_checktime()[1], name, getDuration)
        self.reset()
        # if name == "check_startPlay" and flag_check_logcat_output_keywords == True:
        if name == "check_startPlay":
            # if self.check_display() and self.check_disable_video():
            if self.check_disable_video():
                self.screenshot("1", "osd+video", 31)
                flag_common_threadpool = self.check_common_threadpool(timeout=timeout)
                return flag_common_threadpool, self.checked_log_dict
        # if flag_check_logcat_output_keywords and len(self.abnormal_observer_list) == 0:
        if len(self.abnormal_observer_list) == 0:
            flag_common_threadpool = self.check_common_threadpool(timeout=timeout)
            return flag_common_threadpool, self.checked_log_dict
        return flag_check_logcat_output_keywords, self.checked_log_dict

    def check_switchWindow(self, keywords="", logFilter="", focused_playerNum=2, replace_window=0):
        """
        check switch window, include PIP way
        :param resume_playerNum: specific focused playerNum, the first player:0; the second player:1
        other params are the same as check_switchWindow
        """
        if self.__playerNum == 2:
            if focused_playerNum == 2:
                if not keywords:
                    keywords = self.mediacheck_keywords.FOCUSED2PLAYER_KEYWORDS.copy()
                    keywords[0] = re.findall(r"(\[MediaPlayerProxy_1\] surfaceChanged): SurfaceHolder@.*; width=1920; "
                                             r"height=1080", keywords[0])[0]
                    keywords[1] = re.findall(r"(\[MediaPlayerProxy_0\] surfaceChanged): SurfaceHolder@.*; width=640; "
                                             r"height=360", keywords[1])[0]
            else:
                if not keywords:
                    keywords = self.mediacheck_keywords.FOCUSED1PLAYER_KEYWORDS.copy()
                    keywords[0] = re.findall(r"(\[MediaPlayerProxy_0\] surfaceChanged): SurfaceHolder@.*; width=1920; "
                                             r"height=1080", keywords[0])[0]
                    keywords[1] = re.findall(r"(\[MediaPlayerProxy_1\] surfaceChanged): SurfaceHolder@.*; width=640; "
                                             r"height=360", keywords[1])[0]
        elif self.__playerNum == 4:
            if focused_playerNum == 1 and replace_window == 0:
                if not keywords:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_2_1.copy()
                    keywords[0] = re.findall(r"(\[MediaPlayerProxy_1\] surfaceChanged): SurfaceHolder@.*; width=1280; "
                                             r"height=720", keywords[0])[0]
                    keywords[1] = re.findall(r"(\[MediaPlayerProxy_0\] surfaceChanged): SurfaceHolder@.*; width=640; "
                                             r"height=360", keywords[1])[0]
            elif focused_playerNum == 0 and replace_window == 1:
                if not keywords:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_1_2.copy()
                    keywords[0] = re.findall(r"(\[MediaPlayerProxy_0\] surfaceChanged): SurfaceHolder@.*; width=1280; "
                                             r"height=720", keywords[0])[0]
                    keywords[1] = re.findall(r"(\[MediaPlayerProxy_1\] surfaceChanged): SurfaceHolder@.*; width=640; "
                                             r"height=360", keywords[1])[0]
            elif focused_playerNum == 2 and replace_window == 0:
                if not keywords:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_3_1.copy()
                    keywords[0] = re.findall(r"(\[MediaPlayerProxy_2\] surfaceChanged): SurfaceHolder@.*; width=1280; "
                                             r"height=720", keywords[0])[0]
                    keywords[1] = re.findall(r"(\[MediaPlayerProxy_0\] surfaceChanged): SurfaceHolder@.*; width=640; "
                                             r"height=360", keywords[1])[0]
            elif focused_playerNum == 0 and replace_window == 2:
                if not keywords:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_1_3.copy()
                    keywords[0] = re.findall(r"(\[MediaPlayerProxy_0\] surfaceChanged): SurfaceHolder@.*; width=1280; "
                                             r"height=720", keywords[0])[0]
                    keywords[1] = re.findall(r"(\[MediaPlayerProxy_2\] surfaceChanged): SurfaceHolder@.*; width=640; "
                                             r"height=360", keywords[1])[0]
            elif focused_playerNum == 3 and replace_window == 0:
                if not keywords:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_4_1.copy()
                    keywords[0] = re.findall(r"(\[MediaPlayerProxy_3\] surfaceChanged): SurfaceHolder@.*; width=1280; "
                                             r"height=720", keywords[0])[0]
                    keywords[1] = re.findall(r"(\[MediaPlayerProxy_0\] surfaceChanged): SurfaceHolder@.*; width=640; "
                                             r"height=360", keywords[1])[0]
            elif focused_playerNum == 0 and replace_window == 3:
                if not keywords:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_1_4.copy()
                    keywords[0] = re.findall(r"(\[MediaPlayerProxy_0\] surfaceChanged): SurfaceHolder@.*; width=1280; "
                                             r"height=720", keywords[0])[0]
                    keywords[1] = re.findall(r"(\[MediaPlayerProxy_3\] surfaceChanged): SurfaceHolder@.*; width=640; "
                                             r"height=360", keywords[1])[0]
        if not logFilter:
            logFilter = self.mediacheck_keywords.MULTI_TAG_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_switchWindow.__name__)

    def setMediaSyncLevel(self):
        self.run_shell_cmd('setenforce 0;setprop vendor.amportsAdaptor.debuglevel 1;setprop vendor.amportsAdaptor.debuglevel 2;setprop vendor.amtsplayer.renderdebug 1;'
                           'setprop vendor.hwc.debug 1;setprop vendor.hwc.debug.command "--log-verbose 1";dumpsys SurfaceFlinger;')
        self.run_shell_cmd('echo 1 > /sys/module/amvdec_mh264/parameters/h264_debug_flag;echo 1 > /sys/module/amvdec_h265/parameters/debug;echo 0x0800 > /sys/module/amvdec_mmpeg12/parameters/debug_enable')
        # self.run_shell_cmd('setprop vendor.media.mediahal.mediasync.debug_level 2')

        # self.run_shell_cmd("setprop vendor.media.mediahal.mediasync.debug_aut 255")
        # output frequency 0-5000ms
        # self.run_shell_cmd("setprop vendor.media.mediahal.mediasync.aut_time 1000")
        self.run_shell_cmd("echo 0x40 > /sys/class/video_composer/print_flag")

    def resetMediaSyncLevel(self):
        self.run_shell_cmd("setprop vendor.media.mediahal.mediasync.debug_aut 0")

    def check_stopPlay(self, keywords="", logFilter="", stop_playerNum=1):
        """
        check stop play
        :param stop_playerNum: specific stop playerNum, the first player:1; the second player:2; the third player:3;
                               the forth player:4
        other params are the same as check_startPlay
        """
        self.stop = True
        # which player stopped
        self.stop_playerNum = stop_playerNum
        if not keywords:
            keywords = self.mediacheck_keywords.STOP_KEYWORDS
        if not logFilter:
            logFilter = self.mediacheck_keywords.STOP_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_stopPlay.__name__)

    def check_display(self):
        display_frame_list = []
        dumps = self.run_shell_cmd("dumpsys SurfaceFlinger")
        # logging.info(f"dumps:{dumps[1]}")
        dumps = dumps[1].strip().split(
            "--------------------------------------------------------------------------------"
            "-------------")
        for display in dumps:
            filter_display = display.split(
                "+------+-----+------------+-----+--------+-+--------+-------------------+---"
                "----------------+")
            for filter in filter_display:
                filter = filter.strip().split("|")
                if not filter[0]:
                    display_frame_list.append(filter[-2])
        logging.info(f"display_frame_list: {display_frame_list}")
        screen_size = display_frame_list[1].strip().split()
        width = screen_size[-2]
        height = screen_size[-1]
        if self.__playerNum >= 5:
            return False
        elif self.__playerNum == 4:
            one_way = display_frame_list[-1].strip().split()
            two_way = display_frame_list[-2].strip().split()
            three_way = display_frame_list[-3].strip().split()
            four_way = display_frame_list[-4].strip().split()
            if (two_way == [one_way[-2], one_way[-4], width, str(2*int(one_way[-3]))]
                    and three_way == [one_way[-2], str(2*int(one_way[-3])), width, str(4*int(one_way[-3]))]
                    and four_way == [one_way[-2], str(4*int(one_way[-3])), width, height]):
                return True
        elif self.__playerNum == 3:
            one_way = display_frame_list[-1].strip().split()
            two_way = display_frame_list[-2].strip().split()
            three_way = display_frame_list[-3].strip().split()
            if (two_way == [one_way[-2], one_way[-4], width, str(2*int(one_way[-3]))]
                    and three_way == [one_way[-2], str(2*int(one_way[-3])), width, str(4*int(one_way[-3]))]):
                return True
        elif self.__playerNum == 2:
            if (display_frame_list[-1].strip().split() == self.mediacheck_keywords.ONE_WAY_IN_TWO_DISPLAY
                    and display_frame_list[-2].strip().split() == self.mediacheck_keywords.TWO_WAY_IN_TWO_DISPLAY):
                return True
        else:
            if display_frame_list[-1].strip().split() == self.mediacheck_keywords.ONE_WAY_IN_TWO_DISPLAY:
                return True

    def check_seek(self, keywords="", logFilter="", seek_playerNum=0):
        """
        check seek: include PIP way
        params are the same as check_stopPlay
        """
        self.randomSeekEnable = True
        if not keywords:
            if seek_playerNum == 0:
                keywords = self.mediacheck_keywords.SEEK_KEYWORDS
            elif seek_playerNum == 1:
                keywords = self.mediacheck_keywords.SEEK2_KEYWORDS
                keywords = re.findall(r"\[MediaPlayerBase_1\] changeStatus:Playing->Seeking",
                                      keywords[0])
            elif seek_playerNum == 2:
                keywords = self.mediacheck_keywords.SEEK3_KEYWORDS
                keywords = re.findall(r"\[MediaPlayerBase_2\] changeStatus:Playing->Seeking",
                                      keywords[0])
            elif seek_playerNum == 3:
                keywords = self.mediacheck_keywords.SEEK4_KEYWORDS
                keywords = re.findall(r"\[MediaPlayerBase_3\] changeStatus:Playing->Seeking",
                                      keywords[0])
        if not logFilter:
            logFilter = self.mediacheck_keywords.SEEK_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_seek.__name__)

    def check_switchChannel(self, keywords="", logFilter=""):
        """
        check switch channel
        params are the same as check_startPlay
        """
        self.switchChannel = True
        if not keywords:
            keywords = self.mediacheck_keywords.SWITCH_CHANNEL_KEYWORDS.copy()
            # keywords[0] = re.findall(r".* (setVideoParams vpid): .*, fmt: .*", keywords[0])[0]
        if not logFilter:
            logFilter = self.mediacheck_keywords.SWITCH_CHANNEL_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_switchChannel.__name__)

    def check_audioChannelnum(self, keywords="", logFilter=""):
        """
        check switch audio track
        params are the same as check_startPlay
        """
        self.switchAudio = True
        if not keywords:
            keywords = self.mediacheck_keywords.AUDIO_CHANNEL_NUM_KEYWORDS.copy()
            keywords[0] = re.findall(r".* (Audio numChannels): .*", keywords[0])[0]
        if not logFilter:
            logFilter = self.mediacheck_keywords.AUDIO_CHNUM_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_switchAudioTrack.__name__)

    def check_switchAudioTrack(self, keywords="", logFilter=""):
        """
        check switch audio track
        params are the same as check_startPlay
        """
        self.switchAudio = True
        if not keywords:
            keywords = self.mediacheck_keywords.SWITCH_AUDIO_KEYWORDS.copy()
            # keywords[0] = re.findall(r".* \[(switchAudioTrack):.*\] new apid: .*, fmt:.*",
            #                          keywords[0])[0]
        if not logFilter:
            logFilter = self.mediacheck_keywords.SWITCH_AUDIO_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_switchAudioTrack.__name__)

    def check_switchSubtitleTrack(self, keywords="", logFilter=""):
        """
        check switch subtitle track
        params are the same as check_startPlay
        """
        if not keywords:
            keywords = self.mediacheck_keywords.SWITCH_SUBTITLE_KEYWORDS.copy()
            keywords[0] = \
                re.findall(r"AmlMpPlayerImpl_0 \[(switchSubtitleTrack):.*\] new spid: .*, fmt:.*", keywords[0])[0]
        if not logFilter:
            logFilter = self.mediacheck_keywords.AMP_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_switchSubtitleTrack.__name__)

    def check_speed(self, cmd, speed, check_time, keywords="", logFilter=""):
        """
        check speed:micro speed < 2.0, speed >= 2.0
        :param speed: type: float, set speed what you want
        :param check_time: type: int, speed check time
        :return: type: boolean
        other params are the same as check_startPlay
        """
        return True
        self.speed = True
        if not keywords:
            keywords = self.mediacheck_keywords.SPEED_KEYWORDS.copy()
            keywords[0] = re.findall(r"AmlMpPlayerImpl_\d \[(setPlaybackRate):.*\] rate:.*", keywords[0])[0]

        if not logFilter:
            logFilter = self.mediacheck_keywords.MEDIASYNC_LOGCAT
        if speed < 2.0:
            return True
            # name = "check_speed.txt"
            # speed_list = []
            # self.clear_logcat()
            # self.run_shell_cmd(cmd)
            # # check abnormal
            # logging.info("check abnormal")
            # self.abnormal_threadpool()
            # self.common_threadpool()
            # lines = self.save_need_logcat(name, check_time, "AmMediaSync")
            # for l in lines:
            #     line = l.decode('utf-8', 'backslashreplace_backport') \
            #         .encode('unicode_escape') \
            #         .decode('utf-8', errors='ignore') \
            #         .replace('\\r', '\r') \
            #         .replace('\\n', '\n') \
            #         .replace('\\t', '\t')
            #     if (line != '') and (keywords[1] in line):
            #         # logging.info(f"line: {line}")
            #         speed_list.append(line)
            # logging.info(f"speed_list:{speed_list}")
            # flag_speed = self.calculate_speed(speed, speed_list)
            # return flag_speed
        else:
            # mediasync not support speed which more than 2.0
            return self.get_check_api_result(keywords, logFilter, self.check_speed.__name__)

    def calculate_speed(self, speed, speed_list):
        flag_speed = False
        videoPts_list = []
        sysTime_list = []
        videoPts_diff_list = []
        sysTime_diff_list = []
        for one in speed_list:
            result = re.findall(r".* \[AUT\]playerNum:.*;videoPts:(.*);videoPPcr:.*;videoPTime:.*;curSysTime:(.*)\[AUT_END\]",
                                one.strip(), re.S)
            videoPts = result[0][0]
            sysTime = result[0][1]
            if "fffffff" not in (videoPts or sysTime):
                videoPts_list.append(videoPts)
                sysTime_list.append(sysTime)
        logging.info(f"videoPts_list:{videoPts_list}, sysTime_list:{sysTime_list}")
        for i in range(len(videoPts_list) - 1):
            videoPts_diff = int(videoPts_list[i + 1], 16) - int(videoPts_list[i], 16)
            videoPts_diff_list.append(videoPts_diff)
        for i in range(len(sysTime_list) - 1):
            sysTime_diff = int(sysTime_list[i + 1], 16) - int(sysTime_list[i], 16)
            sysTime_diff_list.append(sysTime_diff)

        division_list = []
        logging.info(f"videoPts_diff_list:{videoPts_diff_list}, sysTime_diff_list:{sysTime_diff_list}")
        for x, y in zip(videoPts_diff_list, sysTime_diff_list):
            # logging.info(f"type y: {y}")
            if speed == 1.0:
                pass
            else:
                if y != 0:
                    division_list.append(x / y)

        logging.info(f"division_list:{division_list}")
        if len(division_list) != 0:
            avg_speed = sum(division_list) / len(division_list)
            if float(avg_speed) - float(speed) < 0.3:
                flag_speed = True
            else:
                logging.info(f"flag_speed:{flag_speed}, diff: {float(avg_speed) }-{float(speed)}")
                flag_speed = False
        return flag_speed

    def check_abnormal(self):
        # logging.info("start check abnormal-------------")
        flag_abnormal = False
        checked_abnormal_logdict = {}
        outputValue_found = False
        start_time = time.time()
        keywords = self.mediacheck_keywords.ABNORMAL_KEYWORDS.copy()
        keywords[0] = re.findall(r"(binder: undelivered transaction) .*, process died", keywords[0])[0]
        # pytest.device._adblogcat_reader.set_check_keywords(keywords)
        # logging.info(f"keywords: {keywords}")
        name = "check_abnormal.txt"
        lines = self.save_need_logcat(name, self.get_checkabnormaltime(), tag="|grep -E 'process died|newStatus=Error|get_buffer() failed|dim: err|VID: store VD0 path_id changed|tombstoned|call AMSTREAM_IOC_GET_MVDECINFO failed|MadDecoder: decoding error|Unexpected EOF|Kernel panic|PC is at dump_throttled_rt_tasks|AML_MP_PLAYER_EVENT_DATA_LOSS'")
        # while (time.time() - start_time < 15) and (outputValue_found is False):
        #     for keyword in keywords:
        #         outputValue = pytest.device._adblogcat_reader.outputDict.get(keyword)
        #         if outputValue:
        #             outputValue_found = True
        #             logging.info(f"{self.check_abnormal.__name__} outputValue: {outputValue}")
        #             checked_abnormal_logdict[keyword] = outputValue
        #             break
        #         else:
        #             continue

        for keyword in keywords:
            if outputValue_found:
                break
            for l in lines:
                line = l.decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                if (keyword in line) and (line != ""):
                    logging.info(f"{self.check_abnormal.__name__} keyword: {keyword}, log line: {line}")
                    if (keywords[0] in line) and ("process died" not in line):
                        flag_abnormal = False
                    else:
                        outputValue_found = True
                        flag_abnormal = True
                        checked_abnormal_logdict[keyword] = line
                    break
                else:
                    continue

        if flag_abnormal:
            logging.info(f"flag_abnormal:{flag_abnormal}, checked_abnormal_logdict: {checked_abnormal_logdict}")
            self.register_abnormal_observer(self.check_abnormal.__name__)
        return flag_abnormal

    def run_check_main_thread(self, during):
        check_main_thread_flag = True
        frame_count, vfm_map, pts_video = [], [], []
        start = time.time()
        logging.info('Checking frame and vfm status')
        while time.time() - start < during and len(self.abnormal_observer_list) == 0:
            frame_count.append('1' if self.checkFrame() else '0')
            vfm_map.append('1' if self.checkHWDecodePlayback() else '0')
            pts_video.append('1' if self.checkavsync() else '0')
            logging.info(f'frame : {frame_count} , vfm : {vfm_map} , pts_video : {pts_video}')
            time.sleep(1)
        self.logcatStop()
        if ("000" in "".join(frame_count)) or ("000" in "".join(vfm_map)) or ("000" in "".join(pts_video)):
            check_main_thread_flag = False
        logging.info(f"{self.run_check_main_thread.__name__}: {check_main_thread_flag}")
        frame_count.clear()
        vfm_map.clear()
        pts_video.clear()
        return check_main_thread_flag

    def get_abnormal_observer(self):
        set(self.abnormal_observer_list)
        if len(self.abnormal_observer_list) != 0:
            self.exitcode = 1  # if thread abnormal exit, set 1
            #logging.info(f"monitor abnormal!!!")
            # os.kill(os.getpid(), signal.SIGTERM)
            return True
        else:
            return False

    def register_abnormal_observer(self, name):
        self.abnormal_observer_list.append(name)
        logging.info(f"{self.register_abnormal_observer.__name__}: {self.abnormal_observer_list}")

    def abnormal_threadpool(self):
        abnormal_func_list = ["self.check_abnormal()"]
        abnormal_task_pool = threadpool.ThreadPool(2)
        requests = threadpool.makeRequests(self.check_abnormal_status, abnormal_func_list)
        [abnormal_task_pool.putRequest(req) for req in requests]

    def common_threadpool(self):
        self.common_thread = True
        common_func_list = ["self.check_stuck_avsync_audio()", "self.check_v4lvideo_count()", "self.checkFrame()",
                            "self.checkHWDecodePlayback()"]
        common_task_pool = threadpool.ThreadPool(6)
        requests = threadpool.makeRequests(self.check_common_status, common_func_list)
        [common_task_pool.putRequest(req) for req in requests]

    def check_play_after_restore(self, timeout, flag=True):
        self.reset()
        check_play = True
        self.restore = flag
        if self.checkFrame():
            logging.info("checkFrame true")
        else:
            check_play = False
            return check_play
        start_time = time.time()
        while time.time() - start_time < timeout:
            self.common_threadpool()
            if self.get_abnormal_observer():
                check_play = False
                break
        return check_play

    def check_common_status(self, func):
        while self.exitcode == 0:
            eval(func)
            if self.get_abnormal_observer():
                # break
                assert False

    def check_abnormal_status(self, func):
        while self.exitcode == 0:
            # logging.info("start abnormal thread")
            eval(func)
            if self.get_abnormal_observer():
                # break
                assert False

    def getTime(self, time=None):
        th = int(time[6:8])
        # print(th)
        tm = int(time[9:11])
        # print(tm)
        ts = int(time[12:14])
        # print(ts)
        tms = int(time[15:18])
        # print(tms)
        # print(time)
        return (tms + ts * 1000 + tm * 60 * 1000 + th * 3600 * 1000) / 1000

    def getVsync(self):
        # vsync_info = self.run_shell_cmd('cat /sys/class/display/vinfo |grep -E "sync_duration_num|sync_duration_den"')[1]
        vsync_info = self.run_shell_cmd('cat /sys/class/display/vinfo |grep "sync_duration_num"')[1]
        # print("vsync_info", vsync_info)
        sync_duration_num = re.findall(r"sync_duration_num: (.*)?", vsync_info, re.S)[0]
        # print("sync_duration_num", sync_duration_num)
        vsync_info = self.run_shell_cmd('cat /sys/class/display/vinfo |grep "sync_duration_den"')[1]
        sync_duration_den = re.findall(r"sync_duration_den: (.*)?", vsync_info, re.S)[0]
        # print("sync_duration_den", sync_duration_den)
        vsync_duration = (int(sync_duration_den)/int(sync_duration_num)).__round__(3)
        # logging.debug("vsync_duration", vsync_duration)
        return vsync_duration

    def check_stuck_avsync_audio(self):
        return True
        # self.lock.acquire()
        if (len(self.abnormal_observer_list) != 0):
            return False
        if self.speed or self.randomSeekEnable or self.switchAudio or self.pause or self.stop:
            return True
        logging.info("start check stuck pts")
        tsplayer_checkin_pts = []
        tsplayer_checkout_offset_pts = []
        video_composer_duration_offset = []
        hwc_realtime_list = []
        mediasync_pts_list = []
        alsa_underrun_list = []
        pts_pes_list = []
        decoder_pts_list = []
        # avsync
        audio_output_pts = []
        keywords = self.mediacheck_keywords.STUCK_KEYWORDS.copy()
        videotype_keywords = self.mediacheck_keywords.V4LVIDEO_KEYWORDS.copy()
        videotype_keywords[0] = re.findall(r".*(provider name).*", videotype_keywords[0])[0]
        # tsplayer_checkin: pts(us)
        keywords[3] = re.findall(r".*(tsplayer-checkin).*", keywords[3])[0]
        # tsplayer_checkout: offset, pts(us)
        keywords[4] = re.findall(r".*(tsplayer-checkout).*", keywords[4])[0]
        # video_composer: duration+offset
        keywords[5] = re.findall(r".*(received_cnt).*(index_disp).*", keywords[5])[0]
        # hwcomposer: realtime
        keywords[6] = re.findall(r".*(updateVtBuffer).*(shouldPresent:1).*", keywords[6])[0]
        # mediasync: realtime+pts
        keywords[7] = re.findall(r".*(mediasync-leave).*", keywords[7])[0]
        # alsa underrun: for audio stuck
        keywords[8] = re.findall(r".*(alsa underrun)", keywords[8])[0]
        # pts_pes
        keywords[9] = re.findall(r".*\[AUT-TEST\] (pes_pts): .*, (frame_pts): .*", keywords[9])[0]
        # decoder(h264/h265)
        keywords[10] = re.findall(r".*(post_video_frame).*", keywords[10])[0]
        # decoder(mpeg2)
        keywords[11] = re.findall(r".*\[(.*)\].*", keywords[11])[0]
        # audio output_pts: for avsync/audio stuck
        keywords[-1] = re.findall(r".*(\[AUT-TEST\]) frame_pts:.*, (output_pts):.*", keywords[-1])[0]
        name = "check_stuck_avsync_audio.txt"
        lines = self.save_need_logcat(name, self.get_checkavsync_stuck_time(),
                                      tag="|grep -E 'AmCodecVDA|received_cnt|post_video_frame|prepare_display_buf|pw_vf_get|v4lvideo|TsRenderer|updateVtBuffer|primary_swap_frame|output_pts|alsa underrun|pes_pts|post_video_frame|aml_dtvsync'")
        count = 0
        for l in lines:
            if l:
                line = l.decode('utf-8', 'backslashreplace_backport') \
                        .encode('unicode_escape') \
                        .decode('utf-8', errors='ignore') \
                        .replace('\\r', '\r') \
                        .replace('\\n', '\n') \
                        .replace('\\t', '\t')
                # print(line)
                if videotype_keywords[0] in line:
                    # print("keywords[0]", line)
                    type = re.findall(r".*provider name: (.*)", line)[0]
                    if "h264" in type:
                        self.video_type = "h264"
                    elif "h265" in type:
                        self.video_type = "h265"
                    elif "mpeg" in type:
                        self.video_type = "mpeg"
                elif keywords[0] in line:
                        # logging.info(f"line-------: {line}")
                        count += 1
                        # logging.info(f"count-------: {count}")
                        if count > 600:
                            logging.info("checked no audio")
                            flag_audio = False
                            self.register_abnormal_observer(self.check_stuck_avsync_audio.__name__)
                            return flag_audio
                elif (keywords[6][0] and keywords[6][1]) in line:
                    # print("poppy6", line)
                    hwc_realtime = re.findall(r".*timestamp \((.*?) us\).*", line)[0]
                    hwc_logtime = self.getTime(line)
                    hwc_realtime_list.append((hwc_logtime, hwc_realtime))
                elif keywords[7] in line:
                    # print("poppy7", line)
                    msync_info = re.findall(r".*\[pts:.*\((.*)us\)\]\[timestampNs:(.*)us\]", line)[0]
                    msync_pts = float(msync_info[0])/1000  # ms
                    msync_realtime = msync_info[1]
                    # print("poppy8", msync_realtime)
                    msync_logtime = self.getTime(line)
                    mediasync_pts_list.append((msync_logtime, msync_pts, msync_realtime))
                elif keywords[3] in line:
                    # print("poppy3")
                    # tsplayer_checkin = re.findall(r"(\d+-\d+ \d+:\d+:\d+\.\d+).*\[pts:.*\((.*)us\)\]", line)[0]
                    # tsplayer_checkin = re.findall(r".*\[pts:.*\((.*)us\).*\[offset:(.*)\]", line)[0]
                    tsplayer_checkin = re.findall(r".*\[pts:.*\((.*)us\).*\[offset:(.*)\]", line)[0]
                    tsplayer_checkin_logtime = self.getTime(line)
                    tsplayer_checkin_pts.append((tsplayer_checkin_logtime, float(tsplayer_checkin[0])/1000, int(tsplayer_checkin[1], 16)))
                elif keywords[4] in line:
                    # print("poppy4")
                    # tsplayer_checkout = re.findall(r"(\d+-\d+ \d+:\d+:\d+\.\d+).*\[offset:(.*?)\)\]\[pts:.*\((.*)?us\)\]", line)[0]
                    tsplayer_checkout = re.findall(r".*\[offset:(.*?)\)\]\[pts:.*\((.*)?us\)\]", line)[0]
                    tsplayer_checkout_logtime = self.getTime(line)
                    if "ffffffff" not in tsplayer_checkout[0]:
                        tsplayer_checkout_offset_pts.append((tsplayer_checkout_logtime, tsplayer_checkout[0], tsplayer_checkout[1]))
                elif keywords[5][0] in line and keywords[5][1] in line:
                # elif keywords[5] in line:
                #     print("poppy5", line)
                    video_composer = re.findall(r"(\d+-\d+ \d+:\d+:\d+\.\d+).*pts=.*\((.*)?\)", line)[0]
                    # video_composer_duration_offset.append((video_composer[0], video_composer[1][2:-8], video_composer[1][-8:]))
                    video_composer_duration_offset.append((video_composer[0], video_composer[1]))
                    # video_composer_offset.append(video_composer[-8:])
                elif keywords[8] in line:
                    alsa_logtime = self.getTime(line)
                    alsa_underrun_list.append((alsa_logtime, keywords[8]))
                elif keywords[9][0] in line and keywords[9][1] in line:
                    # print(keywords[9])
                    # print("poppy9", line)
                    pts_pes_logtime = self.getTime(line)
                    pts_pes = re.findall(r".*\[AUT-TEST\] pes_pts: (.*), frame_pts: .*, pcm\[.*total_dur:(.*)ms\]", line)[0]
                    # pts_pes[0] = int(pts_pes[0], 16)/90  # ms
                    pts_pes_list.append((pts_pes_logtime, pts_pes[0], pts_pes[1]))
                elif keywords[10] in line:  # decoder pts and logtime
                    # print("keywords[10]", line)
                    # print("self.video_type", self.video_type)
                    decoder_logtime = self.getTime(line)
                    if self.video_type == "h264":
                        decoder_pts = re.findall(r".*pts64 .*\((.*)?\) ts", line)[0]
                        if "0xffffffffffffffff" not in decoder_pts:
                            decoder_pts_list.append((decoder_logtime, int(decoder_pts, 16)&0x00000000ffffffff))
                    elif self.video_type == "h265":
                        # print("1046", line)
                        decoder_pts = re.findall(r".*pts\(.*,(.*)\).*", line)[0]
                        # print("decoder_pts", decoder_pts, line)
                        if "0xffffffffffffffff" not in decoder_pts:
                            decoder_pts_list.append((decoder_logtime, int(decoder_pts)&0x00000000ffffffff))
                elif keywords[11] in line:
                    decoder_logtime = self.getTime(line)
                    decoder_pts = re.findall(r".* pts: (.*?) .*", line)[0]
                    if "ffffffffffffffff" not in decoder_pts:
                        decoder_pts_list.append((decoder_logtime, int(decoder_pts, 16)&0x00000000ffffffff))
                elif (keywords[-1][0] and keywords[-1][1]) in line:
                    audio_output_pts_logtime = self.getTime(line)
                    output_pts = re.findall(r".*\[AUT-TEST\] frame_pts:.*, output_pts:(.*)?,", line)[0]
                    output_pts = int(output_pts, 16)/90  # ms
                    audio_output_pts.append((audio_output_pts_logtime, output_pts))
                    pass
                else:
                    pass
        flag_video_stuck = self.video_stuck_avsync_analysis(tsplayer_checkin_pts, tsplayer_checkout_offset_pts, mediasync_pts_list, hwc_realtime_list, decoder_pts_list)
        flag_audio_stuck = self.audio_stuck_analysis(alsa_underrun_list, pts_pes_list, audio_output_pts)
        flag_avsync = self.avsync_analysis(mediasync_pts_list, hwc_realtime_list, audio_output_pts)
        if flag_video_stuck or flag_audio_stuck or flag_avsync:
        # if flag_video_stuck:
            self.register_abnormal_observer(self.check_stuck_avsync_audio.__name__)
        # self.lock.release()

    def video_stuck_avsync_analysis(self, tsplayer_checkin_pts, tsplayer_checkout_offset_pts, mediasync_pts_list, hwc_realtime_list, decoder_pts_list):
        logging.info("start analysis")
        # analysis
        flag_video_stuck = False
        hwc_pts_list = []
        stream_frame_rate = 1
        logging.debug(f"tsplayer_checkin_pts: {tsplayer_checkin_pts}")
        logging.debug(f"tsplayer_checkout_offset_pts: {tsplayer_checkout_offset_pts}")
        logging.debug(f"mediasync_pts_list:{mediasync_pts_list}")
        logging.debug(f"hwc_realtime_list:{hwc_realtime_list}")
        logging.debug(f"decoder_pts_list:{decoder_pts_list}")
        """
        A: check if lost frame or not
        """
        module_lost_frame = False

        """
        1. get hwc pts: mediasync has realtime and pts info, hws has realtime info, according to corresponding realtime info, can get hwc pts
        """
        for msync_ele in mediasync_pts_list:
            for hwc_ele in hwc_realtime_list:
                if hwc_ele[1] == msync_ele[2]:
                    hwc_pts_list.append((hwc_ele[0], msync_ele[1]))
        logging.debug(f"hwc_pts_list: {hwc_pts_list}")
        """
        2. if hwc pts times < (checkin pts)*93%, think lost frame
        """
        checkin_pts = [checkin_pts[1] for checkin_pts in tsplayer_checkin_pts]
        logging.debug(f"hwc_pts_list: {hwc_pts_list}, checkin_pts: {checkin_pts}")
        hwc_pts = [hwc_pts[1] for hwc_pts in hwc_pts_list]
        if checkin_pts.index(hwc_pts[-1]):
            logging.debug(f"hwc_pts: {hwc_pts}, len(hwc_pts): {len(hwc_pts)}, checkin_pts index: {checkin_pts.index(hwc_pts[-1])+1}")
            if len(hwc_pts) < (sorted(checkin_pts).index(hwc_pts[-1])+1)*0.93:
                flag_video_stuck = True
                module_lost_frame = flag_video_stuck
        if module_lost_frame:
            logging.info(f"video stuck:  hwc pts times < (checkin pts)*93%")
            return self.check_whichmodule_lost_frame(mediasync_pts_list, tsplayer_checkin_pts, hwc_pts_list, decoder_pts_list)

        """
        B: check if frame output slowly or not
        """
        """
        1. get vSync info
        """
        vsync_duration = self.getVsync()
        """
        2. get stream frame rate: 1000000/diff(checkout-pts)
        """
        checkout_pts_list = [checkout_ele[2] for checkout_ele in tsplayer_checkout_offset_pts]
        pts_diff_list = [(float(checkout_pts_list[i + 1]) - float(checkout_pts_list[i])) for i in range(len(checkout_pts_list) - 1)]
        logging.debug(f"pts_diff_list: {pts_diff_list}")
        if len(pts_diff_list) != 0:
            if min(pts_diff_list) != 0:
                stream_frame_rate = 1000000/min(pts_diff_list)
        logging.debug(f"stream_frame_rate: {stream_frame_rate}")
        """
        3. if hwc pts output times < (strame frame rate)*96%, think frame output slowly or lost frame
        """
        total_pts = 0
        index_1 = 0
        for index, ele in enumerate(hwc_pts_list):
            if ele[0] - hwc_pts_list[0][0] > 1:
                total_pts = total_pts - len(hwc_pts_list)
                index_1 += 1
            total_pts = total_pts + len(hwc_pts_list)
            if total_pts < stream_frame_rate * 0.96:
                logging.info(f"video stuck:  total_pts < stream_frame_rate*0.96")
                flag_video_stuck = True

        if flag_video_stuck:
            logging.info(f"video stuck:  hwc pts output times < (strame frame rate)*96%")
            # return flag_video_stuck

        """
        4. get hwc logtime diff, if hwc logtime diff < (3/stream_frame_rate), think frame output slowly or lost frame
        """
        flag_video_stuck = False
        hwc_logtime_diff = [(float(hwc_realtime_list[i + 1][0]) - float(hwc_realtime_list[i][0])) for i in
         range(len(hwc_realtime_list) - 1)]
        logging.debug(f"hwc_logtime_diff: {hwc_logtime_diff}")
        count = 0
        for logtime_diff in hwc_logtime_diff[1:]:
            if logtime_diff > (3/stream_frame_rate):
                count += 1
                if count > 5:
                    logging.info(f"video stuck: hwc logtime diff count:{count}")
                    flag_video_stuck = True
        if flag_video_stuck:
            logging.info(f"video stuck:  hwc logtime diff < (3/stream_frame_rate)")
            # return flag_video_stuck
        """
        B1: frame output slowly: check which module lead to stuck: hwc_pts_list
        diffA: current hwc logtime - first hwc logtime
        diffB: current hwc pts - first hwc pts
        diffC=diffA-diffB, if diffC > vsync_duration
        """
        module_frame_output_slowly = False
        baseline = 0
        count = 0
        diffC = 0
        if len(hwc_pts_list) >= 1:
            for i, ele in enumerate(hwc_pts_list):
                diffA = float(hwc_pts_list[i][0]) - float(hwc_pts_list[0][0])
                diffB = float(int(hwc_pts_list[i][1]) - int(hwc_pts_list[0][1])) / 1000
                diffC = diffA - diffB
                logging.debug(f"diffA:{diffA}, diffB:{diffB}, diffC: {diffC}, vsync_duration: {vsync_duration}, baseline: {baseline}")
                # calculate
                if diffC - baseline > vsync_duration:
                    count += 1
                    logging.info("count fail")
                if abs(diffC - baseline) > vsync_duration:
                    baseline = diffC

            if count > 2:
                logging.info(f"count: {count}")
                flag_video_stuck = True
                module_frame_output_slowly = flag_video_stuck
        if module_frame_output_slowly:
            logging.info("video stuck: diffC > vsync_duration, need check which module stuck further")
            return self.check_whichmodule_output_slowly(mediasync_pts_list, tsplayer_checkin_pts, hwc_pts_list, decoder_pts_list, tsplayer_checkout_offset_pts, diffC)

    def check_whichmodule_output_slowly(self, mediasync_pts_list, tsplayer_checkin_pts, hwc_pts_list, decoder_pts_list, tsplayer_checkout_offset_pts, diffC):
        """
        A: check which module frame output slowly
        """
        logging.info(f"diffC: {diffC}")
        module_stuck_output_slowly = True
        vsync_duration = self.getVsync()
        count = 0
        index = 0
        # check checkin
        for ele in tsplayer_checkin_pts:
            if ele[1] == mediasync_pts_list[-1][1]:
                index = tsplayer_checkin_pts.index(ele)
                # print(index)
        # logging.info(f"tsplayer_checkin_pts: {tsplayer_checkin_pts[0:index+1]}")
        # logging.info(f"hwc_pts_list: {hwc_pts_list}")
        for i, ele in enumerate(tsplayer_checkin_pts[0:index+1]):
            diff_A_checkin = tsplayer_checkin_pts[0:index+1][i][0] - hwc_pts_list[0][0]
            diff_B_checkin = (tsplayer_checkin_pts[0:index+1][i][1] - hwc_pts_list[0][1])/1000
            diff_C_checkin = diff_A_checkin - diff_B_checkin
            logging.debug(
                f"diff_A_checkin:{diff_A_checkin}, diff_B_checkin:{diff_B_checkin}, diffC - diff_C_checkin: {diffC - diff_C_checkin}, vsync_duration: {vsync_duration}")
            # calculate
            if diffC - diff_C_checkin < vsync_duration:
                count += 1

            if count > 1:
                logging.info(f"checkin count: {count}")
                logging.info("checked checkin module stuck: output slowly")
                return module_stuck_output_slowly
        # check decoder
        decoder_pts = []
        # if self.video_type == "h264":
        #     decoder_offset = [(ele[0], ele[1][-8:].strip('0')) for ele in decoder_pts_list]
        # else:
        decoder_offset = [(ele[0], ele[1]) for ele in decoder_pts_list]
        tsplayer_checkout_offset_pts = [(ele[0], int(ele[1], 16), ele[2]) for ele in tsplayer_checkout_offset_pts]
        # logging.debug(f"poppy: {tsplayer_checkout_offset_pts}")
        for checkout in tsplayer_checkout_offset_pts:
            for offset in decoder_offset:
                if offset[1] == checkout[1]:
                    decoder_pts.append((offset[0], checkout[2]))
        count = 0
        logging.info(f"decoder_pts: {decoder_pts}")
        logging.info(f"hwc_pts_list: {hwc_pts_list}")
        for i, ele in enumerate(decoder_pts):
            diff_A_decoder = decoder_pts[i][0] - hwc_pts_list[0][0]
            diff_B_decoder = float(decoder_pts[i][1])/1000000 - float(hwc_pts_list[0][1])/1000
            diff_C_decoder = diff_A_decoder - diff_B_decoder
            logging.debug(
                f"diff_A_decoder:{diff_A_decoder}, diff_B_decoder:{diff_B_decoder}, diffC - diff_C_decoder: {diffC - diff_C_decoder}, vsync_duration: {vsync_duration}")
            # calculate
            if diffC - diff_C_decoder < vsync_duration:
                count += 1

            if count > 1:
                logging.info(f"decoder count: {count}")
                logging.info("checked decoder module stuck: output slowly")
                return module_stuck_output_slowly
        # # check mediasync
        # baseline = 0
        # count = 0
        # for i, ele in enumerate(mediasync_pts_list):
        #     diff_A_mediasync = mediasync_pts_list[i][0] - hwc_pts_list[0][0]
        #     diff_B_mediasync = mediasync_pts_list[i][1] - hwc_pts_list[0][1]
        #     diff_C_mediasync = diff_A_mediasync - diff_B_mediasync
        #     logging.debug(
        #         f"diff_A_mediasync:{diff_A_mediasync}, diff_B_mediasync:{diff_B_mediasync}, baseline - diff_C_mediasync: {baseline - diff_C_mediasync}, vsync_duration: {vsync_duration}")
        #     # calculate
        #     if baseline - diff_C_mediasync > vsync_duration:
        #         count += 1
        #
        #     if count > 2:
        #         logging.info(f"mediasync count: {count}")
        #         logging.info("checked mediasync module stuck: output slowly")
        #         return module_stuck_output_slowly
        logging.info("checked hwc module stuck: output slowly")
        return module_stuck_output_slowly

    def check_whichmodule_lost_frame(self, mediasync_pts_list, tsplayer_checkin_pts, hwc_pts_list, decoder_pts_list):
        module_stuck_lost_frame = False
        # check decoder
        # checkin_pts = [(checkin_pts[1], checkin_pts[2]) for checkin_pts in tsplayer_checkin_pts]
        # if self.video_type == "h264":
        #     decoder_offset = [(ele[0], ele[1][-8:].strip('0')) for ele in decoder_pts_list]
        # else:
        decoder_offset = [(ele[0], ele[1]) for ele in decoder_pts_list]
        # decoder_offset = [(ele[0], int(ele[1][-8:].strip('0'), 16)) for ele in decoder_pts_list]
        mediasync_pts = [mediasync_pts[1] for mediasync_pts in mediasync_pts_list]
        # logging.debug(f"checkin_pts: {checkin_pts}")
        logging.debug(f"decoder_offset: {decoder_offset}")
        tmp = []
        checkin_pts_filter = []
        decoder_pts_count = 0
        first_pts_index = 0
        for offset in decoder_offset:
            for checkin in tsplayer_checkin_pts:
                diff = float(offset[1]) - float(checkin[2])
                if diff > 0:
                    tmp.append((abs(diff), offset[1], checkin[0], checkin[1], checkin[2]))
                else:
                    if not first_pts_index:
                        first_pts_index = tsplayer_checkin_pts.index(tmp[-1][2:])
            if len(tmp) >= 1:
                decoder_pts_count += 1
            checkin_pts_filter = tmp
            tmp.clear()
        logging.debug(f"decoder_pts_count: {decoder_pts_count}")
        logging.debug(f"first_pts_index: {first_pts_index}")
        # logging.debug(f"decoder_pts: {decoder_pts}, len(decoder_pts): {len(decoder_pts)}, checkin_pts index: {checkin_pts.index(decoder_pts[-1])}")
        if decoder_pts_count < (len(tsplayer_checkin_pts)-first_pts_index)*0.93:
            logging.info("checked decoder module stuck: lost frame")
        # check mediasync
        elif len(mediasync_pts_list) < decoder_pts_count*0.93:
            logging.info("checked mediasync module stuck: lost frame")
        else:
            logging.info("checked hwc module stuck: lost frame")
        module_stuck_lost_frame = True
        return module_stuck_lost_frame

    def audio_stuck_analysis(self, alsa_underrun_list, pts_pes_list, audio_output_pts):
        logging.debug(f"alsa_underrun_list:{alsa_underrun_list}")
        logging.debug(f"pts_pes_list:{pts_pes_list}")
        logging.debug(f"audio_output_pts:{audio_output_pts}")
        flag_audio_stuck = False
        """
        D: check if audio stuck or not
        """

        """
        1. alsa underrun print within 20s and times > 3 due to data underrun, think audio stuck
        """
        alsa_logtime_diff = [(alsa_underrun_list[ele+1][0]-alsa_underrun_list[ele][0]) for ele in range(len(alsa_underrun_list)-1)]
        for ele in alsa_logtime_diff:
            if ele > 20 and len(alsa_underrun_list) >= 3:
                # logging.info(f"audio stuck: alsa underrun")
                flag_audio_stuck = True
        if flag_audio_stuck:
            logging.info(f"audio stuck: alsa underrun")
            return flag_audio_stuck
        """
        2. non-ms12: 
        a. if neighbouring pes_pts diff < total_pcm_dur*20% or <total_pcm_dur*10%, otherwise think audio stuck
        """
        tmp_dict = {}
        for index, ele in enumerate(pts_pes_list):
            tmp_dict[int(ele[1], 16) / 90] = (ele[0], int(ele[1], 16) / 90, ele[2])
        pts_pes_list = list(tmp_dict.values())
        flag_audio_stuck = False
        total_dur = 0
        index_1 = 0
        count = 0
        audio_stuck = []
        # print(len(pts_pes_list))
        for index, ele in enumerate(pts_pes_list):
            if ele[0] - pts_pes_list[0][0] > 1:
                total_dur = total_dur - int(pts_pes_list[index_1][2])
                index_1 += 1
            total_dur = total_dur + int(pts_pes_list[index][2])
            pts_pes_diff = pts_pes_list[index][1] - pts_pes_list[index_1][1]
            if index_1 > 20:
                logging.debug(f"pts_pes_diff / total_dur: {pts_pes_diff / total_dur}")
                if pts_pes_diff / total_dur > 1.2 or 0 < pts_pes_diff / total_dur < 0.8:
                    logging.info(f"pts_pes_diff / total_dur: {pts_pes_diff / total_dur}")
                    logging.info(f"audio stuck:  pes_pts diff/total_pcm_dur exceed 10% within 1s")
                    flag_audio_stuck = True
                    count += 1
                    audio_stuck.append(pts_pes_diff / total_dur)

        if flag_audio_stuck:
            logging.info(f"audio stuck:  pes_pts diff/total_pcm_dur exceed 10% within 1s")
            return flag_audio_stuck
        """
        3. b. output_pts diff < logtime 500ms*5%, otherwise think audio stuck
        """
        flag_audio_stuck = False
        audio_logtime = [ele[0] for ele in audio_output_pts]
        audio_pts = [ele[1] for ele in audio_output_pts]
        for i in range(len(audio_logtime) - 1):
            first_logtime = audio_logtime[0]
            first_pts = audio_pts[0]
            if audio_logtime[i] - first_logtime < 0.5:
                logtime_diff = audio_logtime[i] - first_logtime
                pts_diff = audio_pts[i] - first_pts
                if pts_diff != 0:
                    if (logtime_diff / pts_diff > 1.05) or (logtime_diff / pts_diff < 0.95):
                        # logging.debug(f"audio stuck:  logtime diff/total_pcm_dur exceed 5% within 500ms")
                        # flag_audio_stuck = True
                        pass
        if flag_audio_stuck:
            logging.info("audio stuck:  logtime diff/total_pcm_dur exceed 5% within 500ms")
            return flag_audio_stuck

    def avsync_analysis(self, mediasync_pts_list, hwc_realtime_list, audio_output_pts):
        flag_avsync = False
        """
        E: check avsync:
        actual_vpts=(hwc pts - 3*vsync): hwc_pts_list
        actual_apts=output_pts: 
        avdiff = (actual_apts - actual_vpts) - (logtime_audio - logtime_video)
        if avdiff < -185ms or avdiff > 90ms, think avsync failure
        """
        avdiff_preview_list = []
        avdiff_list = []
        hwc_pts_list = []
        for msync_ele in mediasync_pts_list:
            for hwc_ele in hwc_realtime_list:
                if hwc_ele[1] == msync_ele[2]:
                    hwc_pts_list.append((hwc_ele[0], msync_ele[1]))
        tmp_diff = []
        for i, vpts in enumerate(hwc_pts_list):
            for j, apts in enumerate(audio_output_pts):
                if str(vpts[0]).split(".")[0] == str(apts[0]).split(".")[0]:
                    tmp_diff.append((j, apts[0] - vpts[0]))
            if len(tmp_diff) != 0:
                diff = [abs(ele[1]) for ele in tmp_diff]
                index = [ele[0] for ele in tmp_diff]
                # print("diff", diff)
                # print("index", index)
                min_avdiff_index = index[diff.index(min(diff))]
                # print("min", min(diff), "min index", min_avdiff_index, "audio_output_pts[min_avdiff_index-1]",
                #               audio_output_pts[min_avdiff_index], "hwc_pts_list[i]", hwc_pts_list[i])
                apts = audio_output_pts[min_avdiff_index]
                vpts = hwc_pts_list[i]
                avdiff_logtime = (apts[0] - vpts[0]) * 1000
                avdiff_pts = apts[1] - vpts[1]
                avdiff_list.append(((avdiff_pts - avdiff_logtime), apts[1], vpts[1], apts[0]*1000))
                # print(apts, vpts)
            tmp_diff.clear()
        logging.debug(f"avdiff_list: {(avdiff_list)}")
        for ele in avdiff_list[20:]:
            if ele[0] < -185 or ele[0] > 90:
                logging.debug(f"avsync fail: {ele}")
                flag_avsync = True
        if flag_avsync:
            logging.info("avsync failed")
        return flag_avsync

    def get_v4lcount(self):
        put_count = self.run_shell_cmd(self.V4LVIDEO_PUT_COUNT)[1]
        get_count = self.run_shell_cmd(self.V4LVIDEO_GET_COUNT)[1]
        q_count = self.run_shell_cmd(self.V4LVIDEO_Q_COUNT)[1]
        dq_count = self.run_shell_cmd(self.V4LVIDEO_DQ_COUNT)[1]
        return put_count, get_count, q_count, dq_count

    def check_v4lvideo_count(self):
        if self.common_thread:
            self.lock.acquire()
        if (len(self.abnormal_observer_list) != 0):
            return False
        if self.speed or self.switchAudio or self.randomSeekEnable or self.stop or self.pause:
            return True
        logging.info("check v4lvideo count")
        if self.switchChannel:
            time.sleep(3)
        else:
            time.sleep(1)
        flag_v4l_count = True
        put_count, get_count, q_count, dq_count = self.get_v4lcount()
        logging.info(f"temp: {self.put_count_temp, self.get_count_temp, self.q_count_temp, self.dq_count_temp},"
                      f"count: {put_count, get_count, q_count, dq_count}")
        if self.__playerNum == 4:
            four_way_put_count = put_count.split('put_count: ')[1].split(',')[0:4]
            four_way_get_count = get_count.split('get_count: ')[1].split(',')[0:4]
            four_way_q_count = q_count.split('q_count: ')[1].split(',')[0:4]
            four_way_dq_count = dq_count.split('dq_count: ')[1].split(',')[0:4]
            if ("0" in put_count.split(',')[0:4]) or ("0" in get_count.split(',')[0:4]) or (
                    "0" in q_count.split(',')[0:4]) or ("0" in dq_count.split(',')[0:4]):
                flag_v4l_count = False

            for count_temp in list(zip(four_way_put_count + four_way_get_count + four_way_q_count + four_way_dq_count,
                                       self.four_way_put_count_temp + self.four_way_get_count_temp + self.four_way_q_count_temp + self.four_way_dq_count_temp)):
                count = count_temp[0]
                temp = count_temp[1]
                if int(count) > int(temp):
                    pass
                    # logging.info("operator.gt------------")
                else:
                    flag_v4l_count = False
                    # logging.info("operator.lt------------")
                self.four_way_put_count_temp = four_way_put_count
                self.four_way_get_count_temp = four_way_get_count
                self.four_way_q_count_temp = four_way_q_count
                self.four_way_dq_count_temp = four_way_dq_count

        elif self.__playerNum == 3:
            three_way_put_count = put_count.split('put_count: ')[1].split(',')[0:3]
            three_way_get_count = get_count.split('get_count: ')[1].split(',')[0:3]
            three_way_q_count = q_count.split('q_count: ')[1].split(',')[0:3]
            three_way_dq_count = dq_count.split('dq_count: ')[1].split(',')[0:3]
            if ("0" in put_count.split(',')[0:3]) or ("0" in get_count.split(',')[0:3]) or (
                    "0" in q_count.split(',')[0:3]) or ("0" in dq_count.split(',')[0:3]):
                flag_v4l_count = False

            for count_temp in list(zip(three_way_put_count + three_way_get_count + three_way_q_count + three_way_dq_count,
                                       (self.three_way_put_count_temp + self.three_way_get_count_temp + self.three_way_q_count_temp + self.three_way_dq_count_temp))):
                count = count_temp[0]
                temp = count_temp[1]
                if int(count) > int(temp):
                    # logging.info("operator.gt------------")
                    pass
                else:
                    # logging.info("operator.lt------------")
                    flag_v4l_count = False
                self.three_way_put_count_temp = three_way_put_count
                self.three_way_get_count_temp = three_way_get_count
                self.three_way_q_count_temp = three_way_q_count
                self.three_way_dq_count_temp = three_way_dq_count

        elif self.__playerNum == 2:
            two_way_put_count = put_count.split('put_count: ')[1].split(',')[0:2]
            two_way_get_count = get_count.split('get_count: ')[1].split(',')[0:2]
            two_way_q_count = q_count.split('q_count: ')[1].split(',')[0:2]
            two_way_dq_count = dq_count.split('dq_count: ')[1].split(',')[0:2]
            if ("0" in two_way_put_count) or ("0" in two_way_get_count) or (
                    "0" in two_way_q_count) or ("0" in two_way_dq_count):
                flag_v4l_count = False
            for count_temp in list(zip(two_way_put_count + two_way_get_count + two_way_q_count + two_way_dq_count,
                                       (self.two_way_put_count_temp + self.two_way_get_count_temp + self.two_way_q_count_temp + self.two_way_dq_count_temp))):
                count = count_temp[0]
                temp = count_temp[1]
                if int(count) > int(temp):
                    # logging.info("operator.gt------------")
                    pass
                else:
                    # logging.info("operator.lt------------")
                    flag_v4l_count = False
                self.two_way_put_count_temp = two_way_put_count
                self.two_way_get_count_temp = two_way_get_count
                self.two_way_q_count_temp = two_way_q_count
                self.two_way_dq_count_temp = two_way_dq_count

        else:
            one_way_put_count = put_count.split('put_count: ')[1].split(',')[0:1]
            one_way_get_count = get_count.split('get_count: ')[1].split(',')[0:1]
            one_way_q_count = q_count.split('q_count: ')[1].split(',')[0:1]
            one_way_dq_count = dq_count.split('dq_count: ')[1].split(',')[0:1]
            if ("0" in one_way_put_count) or ("0" in one_way_get_count) or (
                    "0" in one_way_q_count) or ("0" in one_way_dq_count):
                flag_v4l_count = False
            if self.pause:
                time.sleep(1)
                self.put_count_temp = one_way_put_count
                self.get_count_temp = one_way_get_count
                self.q_count_temp = one_way_q_count
                self.dq_count_temp = one_way_dq_count
                put_count, get_count, q_count, dq_count = self.get_v4lcount()
                if (operator.eq(self.put_count_temp, put_count.split('put_count: ')[1].split(',')[0:1]) and
                        operator.eq(self.get_count_temp, get_count.split('get_count: ')[1].split(',')[0:1]) and
                        operator.eq(self.q_count_temp, q_count.split('q_count: ')[1].split(',')[0:1]) and
                        operator.eq(self.dq_count_temp, dq_count.split('dq_count: ')[1].split(',')[0:1])):
                    pass
                else:
                    logging.info(self.put_count_temp)
                    logging.info(put_count.split('put_count: ')[1].split(',')[0:1])
                    flag_v4l_count = False
            else:
                for count_temp in list(zip(one_way_put_count + one_way_get_count + one_way_q_count + one_way_dq_count,
                             (self.put_count_temp + self.get_count_temp + self.q_count_temp + self.dq_count_temp))):
                    count = count_temp[0]
                    temp = count_temp[1]
                    if int(count) > int(temp):
                        # logging.info("operator.gt------------")
                        pass
                    else:
                        # logging.info("operator.lt------------")
                        flag_v4l_count = False
                    self.put_count_temp = one_way_put_count
                    self.get_count_temp = one_way_get_count
                    self.q_count_temp = one_way_q_count
                    self.dq_count_temp = one_way_dq_count

        if not flag_v4l_count:
            self.v4l_count_list.append(0)
            if len(self.v4l_count_list) >= 3:
                self.register_abnormal_observer(self.check_v4lvideo_count.__name__)
        if self.common_thread:
            self.lock.release()
        return flag_v4l_count

    def get_audio_appl_ptr(self):
        audio_status = self.run_shell_cmd(self.AUDIO_APPL_PTR)[1]
        # logging.debug(f"audio_status: {audio_status}")
        appl_status = re.findall(r"appl_ptr.*\:(.*)\nclosed", audio_status, re.S)[0]
        appl_ptr = re.findall(r".*?\n", appl_status, re.S)[0]
        return appl_ptr

    def checkFrame(self):
        if self.common_thread:
            self.lock.acquire()
        start_time = time.time()
        # check frame count
        if (len(self.abnormal_observer_list) != 0):
            return False
        flag_frame = False
        if not self.DISPLAYER_FRAME_COMMAND or self.randomSeekEnable or self.speed:
            logging.debug("frame count don't exist or in seek/speed status")
            flag_frame = True
            return flag_frame
        logging.info("check frame count")
        if self.getprop(self.get_android_version()) >= "30":
            # frame count only support at most 2 PIP way
            if self.__playerNum == 2 and (self.pause_playerNum == 1 or self.resume_playerNum == 1):
                self.DISPLAYER_FRAME_COMMAND = "cat /sys/class/video_composer/receive_count_pip"
            else:
                self.DISPLAYER_FRAME_COMMAND = "cat /sys/class/video_composer/receive_count"
        elif self.getprop(self.get_android_version()) == "28":
            self.DISPLAYER_FRAME_COMMAND = "cat sys/module/amvideo/parameters/new_frame_count"
        else:
            self.DISPLAYER_FRAME_COMMAND = "cat /sys/module/amvideo/parameters/display_frame_count"
        time.sleep(1)
        frame = self.run_shell_cmd(self.DISPLAYER_FRAME_COMMAND)[1]
        logging.debug(f'frame_temp {self.frame_temp} - frame_current {frame}')
        if self.pause or self.stop:
            self.frame_temp = frame
            frame = self.run_shell_cmd(self.DISPLAYER_FRAME_COMMAND)[1]
            if int(frame) == int(self.frame_temp):
                logging.debug(f"true frame:{frame}, frame_temp:{self.frame_temp}")
                flag_frame = True
            else:
                logging.debug(f"false  frame:{frame}, frame_temp:{self.frame_temp}")
        else:
            if int(frame) > int(self.frame_temp):
                get_frame_time = time.time()
                if self.restore:
                    logging.info("play time less than 4s after restore network")
                    flag_frame = True if ((get_frame_time - start_time) < 4) else False
                flag_frame = True
            self.frame_temp = frame

        if not flag_frame:
            self.frame_list.append(0)
            if len(self.frame_list) >= 3:
                self.register_abnormal_observer(self.checkFrame.__name__)
        if self.common_thread:
            self.lock.acquire()
        return flag_frame

    def checkHWDecodePlayback(self):
        if self.common_thread:
            self.lock.acquire()
        """
        check vfm map, include PIP way
        """
        if (len(self.abnormal_observer_list) != 0):
            return False
        logging.info("check vfm map")
        flag_HWDecoder = False
        if not self.VFM_MAP_COMMAND:
            return False
        mapInfo_default = self.run_shell_cmd(f'{self.VFM_MAP_COMMAND}')[1]
        # logging.info(mapInfo_default)
        if self.getprop(self.get_android_version()) >= "30":
            if not self.check_player_path():  # ott path
                return True
            if self.stop:
                vdec_list = []
                # PIP way (self.__playerNum > 1), self.stop_playerNum start from 1 to 4, represent from 1 way to 4 way
                if self.stop_playerNum in range(self.__playerNum):
                    if (("vcom-map-0 { video_composer.0(1)" and "vcom-map-1 { video_composer.1(1)"
                         in mapInfo_default)):
                        for one in re.findall(r"vdec-map-.* \{ vdec.* v4lvideo.\d\}", mapInfo_default,
                                                re.S)[0].split("]  "):
                            if "vdec" in one:
                                vdec_list.append(one)
                        if len(vdec_list) == (self.__playerNum-self.stop_playerNum):
                            logging.info(f"len(vdec_list): {len(vdec_list)}")
                            flag_HWDecoder = True
                # single way
                else:
                    if ("vcom-map-0 { video_composer.0(1) video_render.0}" in mapInfo_default) and \
                            (len(re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\) dimulti.1\(1\) v4lvideo.0\}",
                                            mapInfo_default, re.S)) == 0):

                        flag_HWDecoder = True
            else:
                if self.__playerNum == 2:
                    if ((("vcom-map-0 { video_composer.0(1)" and "vcom-map-1 { video_composer.1(1)") in mapInfo_default)
                            and re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\) dimulti.1\(1\) v4lvideo.0\}",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-1 \{ vdec\..*.01\(1\) deinterlace\(1\) v4lvideo.1\}",
                                           mapInfo_default, re.S)):
                        flag_HWDecoder = True
                elif self.__playerNum == 3:
                    if ((("vcom-map-0 { video_composer.0(1)" and "vcom-map-1 { video_composer.1(1)") in mapInfo_default)
                            and re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\) dimulti.1\(1\) v4lvideo.0\}",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-1 \{ vdec\..*.01\(1\) deinterlace\(1\) v4lvideo.1\}",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-2 \{ vdec\..*.02\(1\) v4lvideo.2\}",
                                           mapInfo_default, re.S)):
                        flag_HWDecoder = True
                elif self.__playerNum == 4:
                    logging.info("check vfm map: path 4")
                    if (("vcom-map-0 { video_composer.0(1)" and "vcom-map-1 { video_composer.1(1)" in mapInfo_default)
                            and re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\) dimulti.1\(1\) v4lvideo.0\}",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-1 \{ vdec\..*.01\(1\) deinterlace\(1\) v4lvideo.1\}",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-2 \{ vdec\..*.02\(1\) v4lvideo.2\}",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-3 \{ vdec\..*.03\(1\) v4lvideo.3\}",
                                           mapInfo_default, re.S)):
                        flag_HWDecoder = True
                else:
                    if (re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\) dimulti.1\(1\) v4lvideo.0\}", mapInfo_default, re.S)
                            and ("vcom-map-0 { video_composer.0(1) video_render.0}" in mapInfo_default)):
                        flag_HWDecoder = True
        else:
            if self.sourceType == "tvpath":
                if re.findall(r'tvpath { vdin0\(\d\)', mapInfo_default, re.S):
                    flag_HWDecoder = True
            elif self.videoType == "vp9":
                if (("vcom-map-0 { video_composer.0(1) video_render.0}" in mapInfo_default) and
                        ("vdec-map-0 { vdec.vp9.00(1) v4lvideo.0}" in mapInfo_default)):
                    flag_HWDecoder = True
            else:
                if (re.findall(r"default { decoder\(1\) ppmgr\(1\) deinterlace\(1\).*", mapInfo_default, re.S) and
                        ("vcom-map-0 { video_composer.0(1) video_render.0}" in mapInfo_default)):
                    flag_HWDecoder = True
                else:
                    logging.info("Can't find vfm map")
        if not flag_HWDecoder:
            self.vfmMap_list.append(0)
            if len(self.vfmMap_list) >= 3:
                self.register_abnormal_observer(self.checkHWDecodePlayback.__name__)
        if self.common_thread:
            self.lock.release()
        return flag_HWDecoder

    def save_need_logcat(self, name, timeout, tag=''):
        """
        mediasync log include avsync, videoPts, videoDrop, stuck info and so on
        """
        self.setMediaSyncLevel()
        log, logfile = self.save_logcat(name, tag)
        time.sleep(timeout)
        self.stop_save_logcat(log, logfile)
        self.resetMediaSyncLevel()
        with open(logfile.name, "rb") as f:
            lines = f.readlines()
        # print(lines)
        return lines

    def checkavsync(self):
        if self.common_thread:
            self.lock.acquire()
        if (len(self.abnormal_observer_list) != 0):
            return False
        flag_avsync = True
        if self.pause or self.stop or self.speed or self.randomSeekEnable or self.switchAudio:
            # logging.info("stop check avsync")
            return flag_avsync
        logging.info("check avsync")
        # IPTV/TV/OTT(<30): tsync, OTT(>=30) and vp9: mediasync, linux: msync
        if self.getprop(self.get_android_version()) > "30" and self.check_player_path():  # Android S and IPTV path
            logging.debug("Android S: IPTV path; Analyze mediaSync log")
            av_diff_pts_list = []
            audio_diff_pts_list = []
            keywords = self.mediacheck_keywords.MEDIASYNC_KEYWORDS.copy()
            keyword = re.findall(r".*\[AUT\]playerNum:.*;(avDiff):.*;audioDiff:.*;\[AUT_END\]", keywords[0])[0]
            name = "check_avsync.txt"
            lines = self.save_need_logcat(name, self.get_checkavsync_stuck_time()/6, "AmMediaSync")
            # logging.info("start check avsync")
            for l in lines:
                if l:
                    line = l.decode('utf-8', 'backslashreplace_backport') \
                        .encode('unicode_escape') \
                        .decode('utf-8', errors='ignore') \
                        .replace('\\r', '\r') \
                        .replace('\\n', '\n') \
                        .replace('\\t', '\t')
                    if keyword in line:
                        res = re.findall(r".*\[AUT\]playerNum:.*;avDiff:(.*);audioDiff:(.*);\[AUT_END\]", line)
                        if res:
                            av_diff_pts = res[0][0]
                            audio_diff_pts = res[0][1]
                            # logging.info(f"av_diff_pts: {av_diff_pts}, audio_diff_pts: {audio_diff_pts}")
                            # avDiff: self.get_avsyncdiffreference()[0] 200
                            # audioDiff: self.get_avsyncdiffreference()[1] 0
                            p_conf_avDiff, p_conf_audioDiff, p_conf_DiffCount = self.get_avsyncdiffreference()
                            if (abs(int(av_diff_pts)) > p_conf_avDiff or
                                    abs(int(audio_diff_pts)) < p_conf_audioDiff):
                                av_diff_pts_list.append(av_diff_pts)
                                audio_diff_pts_list.append(audio_diff_pts)
                            # DiffCount: self.get_avsyncdiffreference()[2]
                            if (len(av_diff_pts_list) >= p_conf_DiffCount or
                                    len(audio_diff_pts_list) >= p_conf_DiffCount):
                                flag_avsync = False
                                # logging.info(f"av_diff_pts_list: {av_diff_pts_list}, audio_diff_pts_list: {audio_diff_pts_list},"
                                #             f"avsync failed")
                            else:
                                pass
                                # logging.info("avsync ok")

        else:
            if self.getprop(
                    self.get_android_version()) >= "30" or self.videoType == "vp9" or self.sourceType == "tvpath":
                logging.debug("Android S: OTT path; Android R: MEDIASYNC TYPE; Analyze AmNuPlayer log")
                keywords = self.mediacheck_keywords.R_MEDIASYNC_KEYWORDS.copy()
                keywords = re.findall(r"(NU-AmNuPlayerRenderer: video late by) .* us \(.* secs\)", keywords[0])
                pytest.device._adblogcat_reader.set_check_keywords(keywords)
                for keyword in keywords:
                    # "NU-AmNuPlayerRenderer: video late by 145333616 us (145.33 secs)"
                    outputValue = pytest.device._adblogcat_reader.outputDict.get(keyword)
                    if outputValue:
                        logging.info(f"checkavsync outputValue: {outputValue}")
                        actual_diff_pts = re.findall(r"NU-AmNuPlayerRenderer\: video late by (.*) us \((.*) secs\)",
                                                     outputValue)
                        if actual_diff_pts:
                            logging.info(f"[NU-AmNuPlayerRenderer] av diff pts is too large:{actual_diff_pts}")
                            flag_avsync = False
                        # "NU-AmNuPlayerRenderer: PTS: AV sync info:AV SYNCED"
                        else:
                            logging.debug("[NU-AmNuPlayerRenderer] think av synced!!!!!!")
                    else:
                        logging.info("[NU-AmNuPlayerRenderer] think av synced!!!!!!")
            else:
                logging.debug("TSYNC TYPE")
                # "I kernel  :  [68704.991449@0] VIDEO_TSTAMP_DISCONTINUITY failed, vpts diff is small, param:0x736cd4,
                # oldpts:0x7366f8, pcr:0x916671"
                keywords = self.mediacheck_keywords.TSYNC_KEYWORDS.copy()
                keywords = re.findall(
                    r"(VIDEO_TSTAMP_DISCONTINUITY failed), vpts diff is small, param:.*, oldpts:.*, pcr:.*",
                    keywords[0])
                pytest.device._adblogcat_reader.set_check_keywords(keywords)
                for keyword in keywords:
                    # "NU-AmNuPlayerRenderer: video late by 145333616 us (145.33 secs)"
                    outputValue = pytest.device._adblogcat_reader.outputDict.get(keyword)
                    if outputValue:
                        logging.info(f"checkavsync outputValue: {outputValue}")
                        if "VIDEO_TSTAMP_DISCONTINUITY failed" in outputValue:
                            logging.info(f"[kernel] av diff pts is too large")
                            flag_avsync = False
                        else:
                            logging.debug("[kernel] think av synced!!!!!!")
                    else:
                        logging.info("havn't found tsync log")
        if not flag_avsync:
            self.register_abnormal_observer(self.checkavsync.__name__)
        if self.common_thread:
            self.lock.release()
        return flag_avsync

    def checkSWDecodePlayback(self):
        # 检测是否软解
        topInfo = self.run_shell_cmd(self.SOFT_DECODE_COMMAND)[1]
        logging.info(f'->{topInfo}<-')
        return True if topInfo else False

    def check_vdec_status(self, expect_vdec):
        # check vdec status
        actual_vdec = self.run_shell_cmd(self.VDEC_STATUS_COMMAND)[1]
        try:
            actual_vdec = actual_vdec.split('device name : ')[1]
        except Exception as e:
            logging.error(e)
        finally:
            logging.info(f"actual_vdec:{actual_vdec},expect_vdec:{expect_vdec}")
        if expect_vdec in actual_vdec:
            return True

    def check_player_path(self):
        if (self.getprop("media.ammediaplayer.enable") == "1" or self.getprop(
                    "vendor.media.ammediaplayer.normal.enable") == "1" or
                    self.getprop("vendor.media.ammediaplayer.drm.enable") == "1"):
            return True
        else:
            return False

    def check_display_mode(self):
        info = self.checkoutput(self.DISPLAY_MODE)
        return info.split('p')[0]

    def check_frame_rate(self):
        info = self.checkoutput(self.FRAME_RATE)
        return re.findall(r'fps (\d+)', info, re.S)[0]

    def check_secure(self):
        # check TVP keyword if in log or not, if have, it's secure
        info = self.print_info('codec_mm_dump')
        result = re.findall(r'TVP:(\d+)', info, re.S)
        if result:
            if result[0] == '0':
                logging.info('Not Secure')
                return False
            else:
                logging.info('Secure')
                return True
        else:
            logging.info('Not Secure')
            return False

    def print_vdec_status(self):
        # print vdec status
        vdecInfo = self.run_shell_cmd(self.VDEC_STATUS_COMMAND)[1]
        logging.info(vdecInfo)
        return vdecInfo

    def print_codec_mm_dump(self):
        # print codec_mm dump info
        codec_dump = self.run_shell_cmd(self.CODEC_MM_DUMP_COMMAND)[1]
        logging.info(codec_dump)
        return codec_dump

    def print_vdec_core(self):
        vdec_core = self.run_shell_cmd(self.VIDEO_TYPE_COMMAND)[1]
        logging.info(vdec_core)
        return vdec_core

    def set_vdec_map(self, vdec_map):
        self.vdec_map = vdec_map

    def get_vdec_map(self):
        return self.vdec_map

    def remoteEnable(self):
        self.run_shell_cmd(self.REMOTE_ENABLE)

    def remoteDisable(self):
        self.run_shell_cmd(self.REMOTE_DISABLE)

    def setPlayerType(self, type):
        self.playerType = type

    def getPlayerType(self):
        return self.playerType

    def setDecodeType(self, type):
        self.decodeType = type

    def getDecodeType(self):
        return self.decodeType

    def setPath(self, path):
        self.path = path

    def setName(self, name):
        self.name = name

    def setErrorType(self, type):
        self.errorType = type

    def getErrorType(self):
        return self.errorType

    def setStateSafe(self, isPlaying=False):
        if self.isPlaying != isPlaying:
            self.lock.acquire()
            self.isPlaying = isPlaying
            logging.info(f'setStateSafe isPlaying:{self.isPlaying}')
            self.lock.release()

    def setSourceType(self, sourceType):
        self.sourceType = sourceType

    def getSourceType(self):
        return self.sourceType

    def check_demux(self):
        # single way
        if self.speed or self.switchAudio or self.randomSeekEnable or self.stop:
            return True
        logging.info("check demux")
        time.sleep(0.5)
        flag_demux = True
        flag_demux_list = []
        dmx_filter_list = self.run_shell_cmd(self.DEMUX_FILTER)[1]
        dmx_filter_list = dmx_filter_list.split("\n")
        # print(f"dmx_filter_list, {dmx_filter_list} \n")
        for dmx_filter in dmx_filter_list:
            dmx_res = re.findall(r"(\d) dmx_id:(.*) sid:.* type:(.*) pid:(.*) mem total:.*, buf_base:.*, free size:.*, rp:(.*), wp:(.*), h rp:(.*), h wp:(.*), h mode:.*, sec_level:.*, aucpu:.*", dmx_filter)
            if dmx_res:
                # print(dmx_res[0])
                if "vid" in dmx_res[0]:
                    self.vid_dmx_info_list.append(dmx_res[0][5:])
                if "aud" in dmx_res[0]:
                    self.aud_dmx_info_list.append(dmx_res[0][5:])
        # logging.debug(f"self.vid_dmx_info_list:{self.vid_dmx_info_list}")
        # logging.debug(f"self.aud_dmx_info_list:{self.aud_dmx_info_list}")
        # check demux normally if or not
        for i in range(len(self.vid_dmx_info_list)-1):
            # wp, write pointer
            if int(self.vid_dmx_info_list[i+1][0], 16) - int(self.vid_dmx_info_list[i][0], 16) > 0:
                pass
            elif int(self.vid_dmx_info_list[i][1], 16) - int(self.vid_dmx_info_list[i][2], 16) == 0:
                pass
            else:
                flag_demux = False
        for i in range(len(self.aud_dmx_info_list)-1):
            # wp, write pointer
            if int(self.aud_dmx_info_list[i + 1][0], 16) - int(self.aud_dmx_info_list[i][0], 16) > 0:
                pass
            elif int(self.aud_dmx_info_list[i][1], 16) - int(self.aud_dmx_info_list[i][2], 16) == 0:
                pass
            else:
                flag_demux = False
        if not flag_demux:
            flag_demux_list.append(1)
            if len(flag_demux_list) >= 3:
                self.register_abnormal_observer(self.check_demux.__name__)

    def reset(self):
        logging.info(f"[{self.__class__.__name__}][reset]")
        self.path = ""
        self.name = ""
        self.isPlaying = False
        self.restore = False
        self.common_thread = False
        self.check_vfm_map_thread = ""
        self.check_frame_count_thread = ""
        self.setErrorType(self.ERROR_TYPE_OK)
        self.randomSeekEnable = False
        self.avMointer = None
        self.dropCheck = None
        self.ACTIVITY_TUPLE = None
        self.omxLogcat = None
        self.TAG = None
        self.dropChkEnable = None
        self.avSyncChkEnable = None
        self.avsync_thread = False
        self.videoType = None
        self.sourceType = None
        self.decodeType = None
        self.counter = 0
        self.frame_temp = 0
        self.audio_appl_ptr_temp = 0
        self.check_vfm_map = True
        self.build_configuration = "ro.build.configuration"
        self.logcat_avsync = ""
        self.pause = False
        self.stop = False
        self.speed = False
        self.switchAudio = False
        self.switchChannel = False
        self.name = ""
        self.vfmMap_list = []
        self.frame_list = []
        self.v4l_count_list = []
        self.audio_appl_ptr_list = []
        self.stop_playerNum = 0
        self.pause_playerNum = 0
        self.resume_playerNum = 0
        self.put_count_temp = ["0"]
        self.get_count_temp = ["0"]
        self.q_count_temp = ["0"]
        self.dq_count_temp = ["0"]
        self.two_way_put_count_temp = ["0", "0"]
        self.two_way_get_count_temp = ["0", "0"]
        self.two_way_q_count_temp = ["0", "0"]
        self.two_way_dq_count_temp = ["0", "0"]
        self.three_way_put_count_temp = ["0", "0", "0"]
        self.three_way_get_count_temp = ["0", "0", "0"]
        self.three_way_q_count_temp = ["0", "0", "0"]
        self.three_way_dq_count_temp = ["0", "0", "0"]
        self.four_way_put_count_temp = ["0", "0", "0", "0"]
        self.four_way_get_count_temp = ["0", "0", "0", "0"]
        self.four_way_q_count_temp = ["0", "0", "0", "0"]
        self.four_way_dq_count_temp = ["0", "0", "0", "0"]
        self.exitcode = 0
        self.__start_kpi_time = 0

        if self.yuvEnable:
            self.yuvChkSum = self.YUV_CHKSUM_NONE

        if self.playerType == self.PLAYER_TYPE_LOCAL:
            self.setStateSafe(False)
            self.decodeType = self.DECODE_TYPE_NONE
        elif self.playerType == self.PLAYER_TYPE_YOUTUBE:
            ...
            # TODO:
        elif self.playerType == self.PLAYER_TYPE_NETFLIX:
            ...
            # TODO:
        # self.wait_devices()

    def setYUVChkSum(self, chkSum):
        if self.yuvEnable:
            self.yuvChkSum = chkSum

    def getYUVChkSum(self):
        if self.yuvEnable:
            return self.yuvChkSum

    def startDecodeChkThread(self):
        if not hasattr(self, 't'):
            self.check_vfm_map_thread = threading.Thread(target=self.checkStatusLoop,
                                      args=(
                                          self.checkSWDecodePlayback if self.getDecodeType() == self.DECODE_TYPE_SW
                                          else self.checkHWDecodePlayback,
                                          self.ERROR_TYPE_VFM_MAP),
                                      name='decodeChkThread')
            self.check_vfm_map_thread.setDaemon(True)
            self.check_vfm_map_thread.start()
            logging.info('startDecodeChkThread')

    def startFrameChkThread(self):
        if not hasattr(self, 'f'):
            self.check_frame_count_thread = threading.Thread(target=self.checkStatusLoop,
                                      args=(self.checkFrame,
                                            self.ERROR_TYPE_FRAME_MAP),
                                      name='frameChkThread')
            self.check_frame_count_thread.setDaemon(True)
            self.check_frame_count_thread.start()
            logging.info('startFrameChkThread')

    def catch_avsync_logcat(self):
        self.clear_logcat()
        if self.getprop(self.get_android_version()) > "30":
            pass
        elif self.getprop(self.get_android_version()) == "30" or self.videoType == "vp9":
            self.p = self.popen(self.AVSYNC_OTT_LOG)
        else:
            self.p = self.popen(self.AVSYNC_IPTV_LOG)
        return self.p

    def startAVSyncThread(self):
        self.avsync_thread = True
        self.logcatStart()
        self.a = threading.Thread(target=self.checkStatusLoop,
                                  args=(self.checkavsync, self.ERROR_TYPE_AVSYNC),
                                  name='avSyncThread')
        self.a.setDaemon(True)
        self.a.start()
        logging.info('startAVSyncThread')

    # def stopDecodeChkThread(self):
    #     logging.info(f"self.isPlaying: {self.isPlaying}")
    #     if self.isPlaying and isinstance(self.t, threading.Thread):
    #         # if self.t.isAlive():
    #         logging.info('stopDecodeChkThread')
    #         stop_thread(self.t)

    # def stopFrameChkThread(self):
    #     if isinstance(self.f, threading.Thread):
    #         # if self.f.isAlive():
    #         logging.info('stopFrameChkThread')
    #         stop_thread(self.f)

    def stopAVSyncThread(self):
        if isinstance(self.a, threading.Thread):
            logging.info('stopAVSyncThread')
            stop_thread(self.a)
            self.logcatStop()

    def RandomSeekCheck(self):
        self.counter = self.counter + 1
        logging.debug(f"seek counter: {self.counter}")
        return self.counter

    def stopPlay(self, errType):
        # if self.getPlayerType() == self.PLAYER_TYPE_LOCAL:
        logging.info('Playback end')
        logging.info(f'errType {errType}')
        # self.stopDecodeChkThread()
        # self.stopFrameChkThread()
        if self.avSyncChkEnable:
            self.stopAVSyncThread()
        if self.randomSeekEnable:
            self.seek = SeekFun()
            if self.sourceType == 'tvpath':
                self.seek.stopSeekThread()
        self.back()
        self.back()
        self.setStateSafe(False)
        if self.yuvEnable and errType == self.ERROR_TYPE_OK:
            if self.getDecodeType() == self.DECODE_TYPE_HW:
                # self.yuvChkSum = self.yuv.getYUVResult()
                self.setYUVChkSum(self.yuv.get_yuv_result())
            elif self.getDecodeType() == self.DECODE_TYPE_SW:
                self.setYUVChkSum(self.YUV_CHKSUM_SW_DECODE)
            else:
                ...
                # TODO:
        elif not self.yuvEnable:
            self.setErrorType(errType)
            self.setYUVChkSum('Yuv Off')
        elif errType != self.ERROR_TYPE_OK:
            self.setErrorType(errType)
            self.setYUVChkSum(self.YUV_CHKSUM_ERR)
        if self.dropChkEnable:
            # omxLogcat.terminate()
            stop_thread(self.omxLogcat)
            self.dropCheck.count_iptv_drop()
        self.saveResult()
        self.reset()

    def logcatStop(self):
        if self.logcat and self.logcatOpened:
            self.logcat.terminate()
            os.kill(self.logcat.pid, signal.SIGTERM)
        if self.logcat_avsync and self.logcatOpened:
            self.logcat_avsync.terminate()
            os.kill(self.logcat_avsync.pid, signal.SIGTERM)
        logging.info('logcat.terminate()')
        self.logcatOpened = False
        # time.sleep(3)

    def getvideoName(self):
        if self.name:
            if len(self.name) > 48:
                return self.name[:24] + '....' + self.name[-24:]
            else:
                return self.name
        else:
            return self.path

    def saveResult(self):
        # if hasattr(self, 'avMointer') and self.avMointer is not None:
        #     av_res = 'Pass' if not self.avMointer.get_libplayer_status()['avsync'] != 1 and \
        #                        self.avMointer.get_libplayer_status()['frame_count'] == 0 else 'Fail'
        # else:
        #     av_res = ''
        log.save_yuv_resulttxt(self.getvideoName(), self.getPlayerType(), self.getDecodeType(), self.getErrorType(),
                               self.getYUVChkSum(), log.drop_times, self.avSyncChkEnable, self.counter)

    def setupDecodeType(self):
        if self.isPlaying:
            if not self.checkHWDecodePlayback():
                topInfo = self.run_shell_cmd("top -n 1|grep -v 'grep'|grep swcodec")[0]
                if topInfo:
                    self.setDecodeType(self.DECODE_TYPE_SW)
                else:
                    self.setDecodeType(self.DECODE_TYPE_NONE)
            else:
                self.setDecodeType(self.DECODE_TYPE_HW)
        else:
            pass

    def checkStatusLoop(self, func, errorType):
        count = []
        while True:
            if 'Error' not in self.getErrorType() and self.isPlaying:
                if not func():
                    count.append('0')
                else:
                    count.append('1')
                if '00000' in ''.join(count):
                    self.setErrorType(errorType)
                    self.setYUVChkSum(self.YUV_CHKSUM_ERR)
                    #logging.info(f"errorType:{errorType}")
                if len(count) > 30:
                    count.clear()
                # logging.debug("checkStatusLoop")
                time.sleep(3)

    def logcatStart(self):
        self.clear_logcat()
        if self.playerType == self.PLAYER_TYPE_LOCAL:
            self.logcat = self.popen('logcat -s %s' % self.TAG)
        self.logcatOpened = True
        if self.getprop(self.get_android_version()) > "30":
            if not self.check_player_path():
                pass
        elif self.getprop(self.get_android_version()) == "30" or self.videoType == "vp9":
            self.logcat_avsync = self.popen(self.AVSYNC_OTT_LOG)
        else:
            logging.info(self.sourceType)
            if self.sourceType == 'tvpath':
                self.logcat_avsync = self.popen(self.AVSYNC_TV_LOG)
            else:
                self.logcat_avsync = self.popen(self.AVSYNC_IPTV_LOG)

    def getLogcatRunTimerError(self):
        raise Exception('get logcat run time error')

    @set_timeout(50, getLogcatRunTimerError)
    def logcatReadLine(self):
        while True:
            if self.logcat and self.logcatOpened:
                log = self.logcat.stdout.readline()
                if log: return log.strip()

    def __repr__(self):
        return 'PlayerCheck'
