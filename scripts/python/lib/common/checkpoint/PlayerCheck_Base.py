#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/4/19 2022/4/19
# @Author  : yongbo.shao
# @Site    : SH #5
# @File    : PlayerCheck_Base.py
# @Email   : yongbo.shao@amlogic.com
# @Software: PyCharm
import atexit
import logging
import os
import re
import signal
import threading
import time
from typing import List, Tuple

import allure
import pytest
import threadpool
import operator

from lib import CheckAndroidVersion
from lib.common import config_yaml
from lib.common.checkpoint.MediaCheck_Keywords import MediaCheckKeywords
from lib.common.checkpoint.YoutubeCheck_Keywords import YoutubeCheckKeywords
from lib.common.checkpoint.GooglePlayMoviesCheck_Keywords import GooglePlayMoviesCheckKeywords
from lib.common.checkpoint.ExoplayerCheck_Keywords import ExoplayerCheckKeywords
from lib.common.checkpoint.KT_Keywords import KTKeywords
from lib.common.system.ADB import ADB
from lib.common.tools.Seek import SeekFun
from lib.common.tools.LoggingTxt import log
from lib.common.system.NetworkAuxiliary import getIfconfig
from util.Decorators import set_timeout, stop_thread
from . import Check
from lib import *
from lib.common.tools.YUV import YUV
from functools import partial


class PlayerCheck_Base(ADB, Check, CheckAndroidVersion):
    '''
    Base player checkpoint, now support OTT/OTT hybrid S IPTV/TV/IPTV
    '''
    _instance_lock = threading.Lock()

    # checkpoints
    VFM_MAP_COMMAND = "cat /sys/class/vfm/map | head -n 20"
    SOFT_DECODE_COMMAND = "top -n 1|grep -v 'grep'|grep swcodec"
    VIDEO_SYNC_COMMAND = "cat /sys/class/tsync/pts_video"
    DISPLAYER_FRAME_COMMAND = "cat /sys/module/amvideo/parameters/display_frame_count"
    VDEC_STATUS_COMMAND = "cat /sys/class/vdec/vdec_status | grep -E 'device name|frame rate' "
    CODEC_MM_DUMP_COMMAND = "cat /sys/class/codec_mm/codec_mm_dump"
    VIDEO_TYPE_COMMAND = "cat /sys/class/vdec/core"
    DUMP_VDEC_CHUNKS = "cat /sys/class/vdec/dump_vdec_chunks"
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

    # abnormal type log
    PRINT_EXCEPTION_CRASH = 'beginning of crash'
    PRINT_EXCEPTION_EOF = "unexpected EOF"

    # avsync logcat
    AVSYNC_IPTV_LOG = "logcat -s kernel"
    AVSYNC_OTT_LOG = "logcat -s NU-AmNuPlayerRenderer"
    AVSYNC_TV_LOG = "logcat -s NU-AmNuPlayerRenderer"

    def __init__(self, playerNum=1):
        ADB.__init__(self, "Player", unlock_code="", stayFocus=True)
        Check.__init__(self)
        CheckAndroidVersion.__init__(self)
        self.kt_keywords = KTKeywords()
        self.mediacheck_keywords = MediaCheckKeywords()
        self.youtubecheck_keywords = YoutubeCheckKeywords()
        self.googleplaymoviescheck_keywords = GooglePlayMoviesCheckKeywords()
        self.exoplayercheck_keywords = ExoplayerCheckKeywords()
        self.lock = threading.Lock()
        self.playerNum = playerNum
        self.sourceType = ""
        self.yuv = YUV()
        self.playerType = ""
        self.logcat = ""
        self.logcatOpened = False
        self.reset()
        self.flag_check_logcat_output_keywords = False
        self.exitcode = 0
        self.abnormal_observer_list = []
        self.vid_dmx_info_list = []
        self.aud_dmx_info_list = []
        self.hwc_logtime_pts_diff = 0
        self.count = 0
        self.checked_log_dict = {}
        self.common_task_pool = threadpool.ThreadPool(6)
        # 在构造函数中注册退出函数
        atexit.register(self.exit_handler)

    def exit_handler(self):
        # 在这里关闭线程池
        self.common_task_pool.dismissWorkers(6, do_join=True)

    def set_AndroidVersion_R_checkpoint(self):
        if self.getprop(self.get_android_version()) >= "11" or self.videoType == "vp9" or (
                self.sourceType == "tvpath"):
            logging.info("Android Version for this product is R or test type is tvpath")
            self.DISPLAYER_FRAME_COMMAND = "cat /sys/class/video_composer/receive_count"

    def start_check_keywords_thread(self, keywords, log, timeout, name="", getDuration=False):
        t = threading.Thread(target=self.start_check_keywords, args=(keywords, log, timeout, name),
                             kwargs={"getDuration": getDuration})
        # t.setDaemon(True)
        t.start()
        t.join()

    def start_check_keywords(self, keywords, log, timeout, name, getDuration=False):
        pass

    def get_startkpi_time(self):
        return self.__start_kpi_time

    def check_kpi(self, keywords, start_time):
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
        p_conf_wait_time = config_yaml.get_note("conf_checktime").get("wait_time")
        return p_conf_wait_time

    def get_checkavsync_stuck_time(self):
        p_conf_avsync_stuck_time = config_yaml.get_note("conf_checktime").get("avsync_stuck_time")
        return p_conf_avsync_stuck_time

    def get_avsyncdiffreference(self):
        p_conf_avDiff = config_yaml.get_note("conf_reference").get("avDiff")
        p_conf_audioDiff = config_yaml.get_note("conf_reference").get("audioDiff")
        p_conf_DiffCount = config_yaml.get_note("conf_reference").get("DiffCount")
        return p_conf_avDiff, p_conf_audioDiff, p_conf_DiffCount

    def get_startplay_kpitime(self):
        p_conf_startplay_time = config_yaml.get_note("conf_kpitime").get("start_play_time")
        return p_conf_startplay_time

    def get_switchchannel_kpitime(self):
        p_conf_switchchannel_time = config_yaml.get_note("conf_kpitime").get("switch_channel_time")
        return p_conf_switchchannel_time

    def get_audiostuck_error(self):
        p_conf_audiostuck_error = config_yaml.get_note("conf_audiostuckerror").get("audio_stuck_error")
        return p_conf_audiostuck_error

    @allure.step("Check Start Play")
    def check_startPlay(self, keywords=None, logFilter=None, getDuration=False, **kwargs):
        """
        Check if the video playback has started.
        :param keywords: list of strings, specific keywords to search in the logcat output (default: None).
        :param logFilter: string, the logcat filter to use (default: None).
        :param getDuration: bool, whether to get the duration of the video (default: False).
        :return: tuple of (bool, dict), where the bool indicates whether the specified keywords were found in the logcat
                 output, and the dict contains information about the logcat output.
        """
        self.reset()
        name = "check_stuck_avsync_audio.txt"
        if os.path.exists(os.path.join(self.logdir, name)):
            os.remove(os.path.join(self.logdir, name))
        if keywords is None:
            keywords = self.prepare_keywords(getDuration)
        if logFilter is None:
            logFilter = self.mediacheck_keywords.AMP_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_startPlay.__name__, getDuration, **kwargs)

    def check_disable_video(self):
        """
        Checks whether the video layer is covered by the OSD layer.
        Returns True if the video is not disabled, or False otherwise.
        """
        # Run the shell command to check if the video layer is disabled
        disable_video = self.run_shell_cmd(self.DISABLE_VIDEO)[1]

        # Check the output of the command and return the appropriate value
        if disable_video == "0":
            # If the video layer is not disabled, return True
            return True
        else:
            # If the video layer is disabled, log a debug message and return False
            logging.debug("checked disable video: 1")
            return False

    def prepare_keywords(self, getDuration):
        """
        Prepare keywords for media check based on number of players and whether to get media duration or not
        @param getDuration: boolean indicating whether to get media duration or not
        @return: list of keywords to be used for media check
        """
        keywords = []

        # If getDuration is True, get keywords for media duration check based on number of players
        if getDuration:
            for i in range(self.playerNum):
                keyword = self.mediacheck_keywords.START4PLAYER_KEYWORDS[i]
                keyword = \
                re.findall(r".*\[sourceffmpeg_info.cpp\]\[get_ffmpeg_streaminfo\]\[.* \](duration):.*", keyword)[0]
                keywords.append(keyword)
        # If getDuration is False, get last few keywords based on number of players
        else:
            if self.playerNum == 1:
                keywords = self.mediacheck_keywords.START_KEYWORDS[-1:]
            elif self.playerNum == 2:
                keywords = self.mediacheck_keywords.START2PLAYER_KEYWORDS[-2:]
            elif self.playerNum == 3:
                keywords = self.mediacheck_keywords.START3PLAYER_KEYWORDS[-3:]
            else:
                keywords = self.mediacheck_keywords.START4PLAYER_KEYWORDS[-4:]

        return keywords

    @allure.step("Check Pause")
    def check_pause(self, pause_playerNum: int = 0, keywords: List[str] = None, logFilter: str = None, **kwargs) -> Tuple[bool, dict]:
        """
        Check pause, include PIP way
        :param pause_playerNum: Specific pause playerNum, the first player: 0; the second player: 1; the third player: 2;
                                the fourth player: 3
        :param keywords: List of keywords to check in the logs
        :param logFilter: Filter to apply to the logcat output
        :param kwargs: Other arguments to pass to the `get_check_api_result` method
        :return: A tuple containing a boolean indicating whether the check was successful and a string with the logcat output
        """
        self.pause = True
        if keywords is None:
            keywords = self.mediacheck_keywords.PAUSE_KEYWORDS
        if logFilter is None:
            logFilter = self.mediacheck_keywords.PAUSE_RESUME_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_pause.__name__, pause_playerNum=pause_playerNum, **kwargs)

    @allure.step("Check Resume")
    def check_resume(self, keywords: str = "", logFilter: str = "", player_num: int = 0, **kwargs) -> Tuple[bool, dict]:
        """
        Check resume status, include PIP way
        :param player_num: Specific player number: 0 for the first player, 1 for the second player, 2 for the third player,
                           3 for the fourth player.
        :param keywords: Keywords to search for in log messages. Defaults to self.mediacheck_keywords.RESUME_KEYWORDS.
        :param logFilter: Logcat filters to apply. Defaults to self.mediacheck_keywords.PAUSE_RESUME_LOGCAT.
        :return: True if the media player resumed playback, False otherwise.
        """
        self.reset()
        name = "check_stuck_avsync_audio.txt"
        if os.path.exists(os.path.join(self.logdir, name)):
            os.remove(os.path.join(self.logdir, name))
        # self.resume_playerNum = player_num
        keywords = keywords if keywords else self.mediacheck_keywords.RESUME_KEYWORDS
        logFilter = logFilter if logFilter else self.mediacheck_keywords.PAUSE_RESUME_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_resume.__name__, resume_playerNum=player_num, **kwargs)

    @allure.step("Check Seek")
    def kt_check_seek(self, keywords: str = None, logFilter: str = None, **kwargs) -> bool:
        if keywords is None:
            keywords = self.kt_keywords.SEEK_KEYWORDS
        if logFilter is None:
            logFilter = self.kt_keywords.AMP_LOGCAT
        return self.kt_check(keywords, logFilter, self.kt_check_seek.__name__, **kwargs)

    @allure.step("Check Pause")
    def kt_check_pause(self, keywords: str = None, logFilter: str = None, **kwargs) -> bool:
        self.pause = True
        if keywords is None:
            keywords = self.kt_keywords.PAUSE_KEYWORDS
        if logFilter is None:
            logFilter = self.kt_keywords.TS_LOGCAT
        return self.kt_check(keywords, logFilter, self.kt_check_pause.__name__, **kwargs)

    @allure.step("Check Resume")
    def kt_check_resume(self, keywords: str = "", logFilter: str = "", **kwargs) -> bool:
        self.reset()
        # self.resume_playerNum = player_num
        keywords = keywords if keywords else self.kt_keywords.RESUME_KEYWORDS
        logFilter = logFilter if logFilter else self.kt_keywords.TS_LOGCAT
        return self.kt_check(keywords, logFilter, self.kt_check_resume.__name__, **kwargs)

    def kt_check(self, keywords, logFilter, name, getDuration=False):
        self.start_check_keywords_thread(keywords, logFilter, self.get_checktime(), name, getDuration)
        self.reset()
        return self.flag_check_logcat_output_keywords

    def get_check_api_result(self, keywords, logFilter, name, getDuration=False, **kwargs):
        # Initialize variables
        timeout = kwargs.get("timeout", self.get_checkavsync_stuck_time())  # Get timeout from kwargs or use default
        checked_display = False

        # Start keyword checking thread
        self.start_check_keywords_thread(keywords, logFilter, self.get_checktime(), name, getDuration)

        # If keyword is found in logs, start saving logs and wait for timeout
        if self.flag_check_logcat_output_keywords:
            if self.playerNum == 4:  # four way start play need wait
                time.sleep(2)
            self.start_save_log_thread(time_out=timeout, **kwargs)
            self.common_threadpool(**kwargs)
            start_time = time.time()
            while time.time() - start_time < timeout:
                # If checking startPlay and display has not been checked yet, check if video is disabled
                if name == "check_startPlay" and not checked_display:
                    if self.check_disable_video():
                        self.screenshot("1", "osd+video", 31)
                    else:
                        self.reset()
                        return checked_display, self.checked_log_dict
                    checked_display = True

                # If an abnormal observer is detected, reset and return False
                if self.get_abnormal_observer():
                    self.reset()
                    return False, self.checked_log_dict

        # If media player state is not pause, stop, speed, switchAudio, or randomSeekEnable, analyze AV sync and audio stuck
        if not any([self.pause, self.stop, self.speed, self.switchAudio, self.randomSeekEnable]):
            if pytest.target.get("prj") == "ott_hybrid_playback_strategy":
                logging.debug("no need check avsync")
            else:
                self.stuck_avsync_audio_analysis()

        # If an abnormal observer is detected, reset and return False
        if self.get_abnormal_observer():
            self.reset()
            return False, self.checked_log_dict

        # Reset and return True
        self.reset()
        return self.flag_check_logcat_output_keywords, self.checked_log_dict

    def check_switchWindow(self, keywords="", logFilter="", focused_playerNum=2, replace_window=0):
        """
        Check if the window has been switched, including PIP mode.
        :param keywords: List of keywords to search for in the logs. If empty, will use default keywords based on the
                         focused player number and whether or not the window is being replaced.
        :param logFilter: The logcat filter to use when searching for keywords.
        :param focused_playerNum: The specific player number that is focused. The first player is 0, and the second is 1.
        :param replace_window: If set to a non-zero value, indicates that the window is being replaced with a new player.
                               The value of this parameter indicates which player is replacing the current one.
        """
        # Set default keywords based on playerNum and focused_playerNum.
        if not keywords:
            if self.playerNum == 2:
                if focused_playerNum == 2:
                    keywords = self.mediacheck_keywords.FOCUSED2PLAYER_KEYWORDS.copy()
                else:
                    keywords = self.mediacheck_keywords.FOCUSED1PLAYER_KEYWORDS.copy()
            elif self.playerNum == 4:
                if focused_playerNum == 1 and replace_window == 0:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_2_1.copy()
                elif focused_playerNum == 0 and replace_window == 1:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_1_2.copy()
                elif focused_playerNum == 2 and replace_window == 0:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_3_1.copy()
                elif focused_playerNum == 0 and replace_window == 2:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_1_3.copy()
                elif focused_playerNum == 3 and replace_window == 0:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_4_1.copy()
                elif focused_playerNum == 0 and replace_window == 3:
                    keywords = self.mediacheck_keywords.FOCUSED_PLAYER_KEYWORDS_1_4.copy()
        # Set default logFilter if not provided.
        if not logFilter:
            logFilter = self.mediacheck_keywords.MULTI_TAG_LOGCAT
        return self.get_check_api_result(keywords, logFilter, self.check_switchWindow.__name__)

    @allure.step("Check Stop Play")
    def check_stopPlay(self, keywords="", logFilter="", stop_playerNum=1, **kwargs):
        """
        Checks if media playback has stopped.
        :param keywords: the keywords to search for in the logcat (default: the STOP_KEYWORDS constant)
        :param logFilter: the logcat filter to use (default: the STOP_LOGCAT constant)
        :param stop_playerNum: the player number (1-4) that stopped (default: 1)
        :param kwargs: additional keyword arguments for the get_check_api_result method
        :return: the result of the get_check_api_result method
        """
        # Set stop flag
        self.stop = True

        # Use default keywords if none provided
        if not keywords:
            keywords = self.mediacheck_keywords.STOP_KEYWORDS

        # Use default logFilter if none provided
        if not logFilter:
            logFilter = self.mediacheck_keywords.STOP_LOGCAT

        # Call get_check_api_result method with specified parameters
        return self.get_check_api_result(keywords, logFilter, self.check_stopPlay.__name__, stop_playerNum=stop_playerNum, **kwargs)

    def check_display(self):
        # get display info from shell command
        dumps = self.run_shell_cmd("dumpsys SurfaceFlinger")
        # split the output into each display configuration
        dumps = dumps[1].strip().split(
            "--------------------------------------------------------------------------------"
            "-------------")

        # extract the frame buffer sizes for each display
        display_frame_list = []
        for display in dumps:
            filter_display = display.split(
                "+------+-----+------------+-----+--------+-+--------+-------------------+---"
                "----------------+")
            for filter in filter_display:
                filter = filter.strip().split("|")
                if not filter[0]:
                    display_frame_list.append(filter[-2])

        logging.debug(f"display_frame_list: {display_frame_list}")

        # get the screen size
        screen_size = display_frame_list[1].strip().split()
        width = screen_size[-2]
        height = screen_size[-1]

        # check display configuration based on player number
        if self.playerNum >= 5:
            return False
        elif self.playerNum == 4:
            # get frame buffer sizes for each player
            one_way = display_frame_list[-1].strip().split()
            two_way = display_frame_list[-2].strip().split()
            three_way = display_frame_list[-3].strip().split()
            four_way = display_frame_list[-4].strip().split()
            # check if the frame buffer sizes match the expected configuration
            if (two_way == [one_way[-2], one_way[-4], width, str(2 * int(one_way[-3]))]
                    and three_way == [one_way[-2], str(2 * int(one_way[-3])), width, str(4 * int(one_way[-3]))]
                    and four_way == [one_way[-2], str(4 * int(one_way[-3])), width, height]):
                return True
        elif self.playerNum == 3:
            one_way = display_frame_list[-1].strip().split()
            two_way = display_frame_list[-2].strip().split()
            three_way = display_frame_list[-3].strip().split()
            if (two_way == [one_way[-2], one_way[-4], width, str(2 * int(one_way[-3]))]
                    and three_way == [one_way[-2], str(2 * int(one_way[-3])), width, str(4 * int(one_way[-3]))]):
                return True
        elif self.playerNum == 2:
            if (display_frame_list[-1].strip().split() == self.mediacheck_keywords.ONE_WAY_IN_TWO_DISPLAY
                    and display_frame_list[-2].strip().split() == self.mediacheck_keywords.TWO_WAY_IN_TWO_DISPLAY):
                return True
        else:
            if display_frame_list[-1].strip().split() == self.mediacheck_keywords.ONE_WAY_IN_TWO_DISPLAY:
                return True

    @allure.step("Check iptv path seek")
    def check_seek(self, keywords="", logFilter="", seek_playerNum=0, **kwargs):
        """
        Check if a media player is seeking.

        :param keywords: A list of keywords or a string of keywords to match in the log.
        :param logFilter: A regular expression to filter the log output.
        :param seek_playerNum: An integer indicating which media player to check seeking for.
            If 0, check seeking for all players.
            If 1, check seeking for the first player.
            If 2, check seeking for the second player.
            If 3, check seeking for the third player.
        :param kwargs: Additional keyword arguments to pass to the get_check_api_result() function.

        :return: True if seeking is detected, False otherwise.
        """
        self.randomSeekEnable = True

        if not keywords:
            if seek_playerNum == 0:
                keywords = self.mediacheck_keywords.SEEK_KEYWORDS
            elif seek_playerNum == 1:
                keywords = self.mediacheck_keywords.SEEK2_KEYWORDS
            elif seek_playerNum == 2:
                keywords = self.mediacheck_keywords.SEEK3_KEYWORDS
            elif seek_playerNum == 3:
                keywords = self.mediacheck_keywords.SEEK4_KEYWORDS

        if not logFilter:
            logFilter = self.mediacheck_keywords.SEEK_LOGCAT

        return self.get_check_api_result(keywords, logFilter, self.check_seek.__name__, **kwargs)

    def check_switchChannel(self, keywords=None, logFilter=None):
        """
        Check if the channel is successfully switched.
        :param keywords: List of strings to search in the logs. Default is the SWITCH_CHANNEL_KEYWORDS list.
        :param logFilter: Logcat filter string to apply. Default is the SWITCH_CHANNEL_LOGCAT filter.
        :return: Result of the check API.
        """
        self.switchChannel = True
        # If keywords are not provided, use the default SWITCH_CHANNEL_KEYWORDS list.
        if not keywords:
            keywords = self.mediacheck_keywords.SWITCH_CHANNEL_KEYWORDS.copy()
            # TODO: Uncomment the below line if needed to extract the vpid and fmt from the log message.
            # keywords[0] = re.findall(r".* (setVideoParams vpid): .*, fmt: .*", keywords[0])[0]
        # If logFilter is not provided, use the default SWITCH_CHANNEL_LOGCAT filter.
        if not logFilter:
            logFilter = self.mediacheck_keywords.SWITCH_CHANNEL_LOGCAT
        # Call the get_check_api_result method with the provided or default parameters and return the result.
        return self.get_check_api_result(keywords, logFilter, self.check_switchChannel.__name__)

    def check_audioChannelnum(self, keywords="", logFilter=""):
        """
        This method checks if audio track is switched or not.
        It takes two optional parameters - keywords and logFilter, and returns the result
        from the get_check_api_result method after executing check_switchAudioTrack.

        Args:
        - keywords (str): Optional parameter to specify the keywords for audio channel number
        - logFilter (str): Optional parameter to specify the log filter

        Returns:
        - result from get_check_api_result method after executing check_switchAudioTrack.
        """

        # Set switchAudio flag to True
        self.switchAudio = True

        # If keywords is empty, use default AUDIO_CHANNEL_NUM_KEYWORDS
        if not keywords:
            keywords = self.mediacheck_keywords.AUDIO_CHANNEL_NUM_KEYWORDS.copy()

            # The following line of code is commented out, but it is unclear why.
            # Revisit and refactor if necessary.
            # keywords[0] = re.findall(r".* (Audio numChannels): .*", keywords[0])[0]

        # If logFilter is empty, use default AUDIO_CHNUM_LOGCAT
        if not logFilter:
            logFilter = self.mediacheck_keywords.AUDIO_CHNUM_LOGCAT

        # Call get_check_api_result with appropriate arguments
        return self.get_check_api_result(keywords, logFilter, self.check_switchAudioTrack.__name__)

    def check_switchAudioTrack(self, keywords="", logFilter="", id=""):
        """
        This method checks if audio track is switched or not.
        It takes two optional parameters - keywords and logFilter, and returns the result
        from the get_check_api_result method after executing check_switchAudioTrack.

        Args:
        - keywords (str): Optional parameter to specify the keywords for audio track switch
        - logFilter (str): Optional parameter to specify the log filter

        Returns:
        - result from get_check_api_result method after executing check_switchAudioTrack.
        """

        # Set switchAudio flag to True
        self.switchAudio = True

        # If keywords is empty, use default SWITCH_AUDIO_KEYWORDS
        if not keywords:
            keywords = self.mediacheck_keywords.SWITCH_AUDIO_KEYWORDS.copy()
            if pytest.target.get("prj") == "ott_hybrid_switch_audio_track_stress":
                keywords[1] = keywords[1] + id[2:]

            # The following line of code is commented out, but it is unclear why.
            # Revisit and refactor if necessary.
            # keywords[0] = re.findall(r".* \[(switchAudioTrack):.*\] new apid: .*, fmt:.*",
            #                          keywords[0])[0]

        # If logFilter is empty, use default SWITCH_AUDIO_LOGCAT
        if not logFilter:
            logFilter = self.mediacheck_keywords.SWITCH_AUDIO_LOGCAT

        # Call get_check_api_result with appropriate arguments
        return self.get_check_api_result(keywords, logFilter, self.check_switchAudioTrack.__name__)

    def check_switchSubtitleTrack(self, keywords="", logFilter=""):
        """
        This method checks if subtitle track is switched or not.
        It takes two optional parameters - keywords and logFilter, and returns the result
        from the get_check_api_result method after executing check_switchSubtitleTrack.

        Args:
        - keywords (str): Optional parameter to specify the keywords for subtitle track switch
        - logFilter (str): Optional parameter to specify the log filter

        Returns:
        - result from get_check_api_result method after executing check_switchSubtitleTrack.
        """

        # If keywords is empty, use default SWITCH_SUBTITLE_KEYWORDS
        if not keywords:
            keywords = self.mediacheck_keywords.SWITCH_SUBTITLE_KEYWORDS.copy()

            # The following line of code is commented out, but it is unclear why.
            # Revisit and refactor if necessary.
            # keywords[0] = \
            #     re.findall(r"AmlMpPlayerImpl_0 \[(switchSubtitleTrack):.*\] new spid: .*, fmt:.*", keywords[0])[0]

        # If logFilter is empty, use default AMP_LOGCAT
        if not logFilter:
            logFilter = self.mediacheck_keywords.AMP_LOGCAT

        # Call get_check_api_result with appropriate arguments
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
            result = re.findall(
                r".* \[AUT\]playerNum:.*;videoPts:(.*);videoPPcr:.*;videoPTime:.*;curSysTime:(.*)\[AUT_END\]",
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
                logging.info(f"flag_speed:{flag_speed}, diff: {float(avg_speed)}-{float(speed)}")
                flag_speed = False
        return flag_speed

    def check_abnormal(self, line: str) -> bool:
        """
        Check if a log line contains any abnormal keywords.
        :param line: Log line to check.
        :return: True if the line contains any abnormal keyword, False otherwise.
        """
        # Initialize the flag to False.
        flag_abnormal = False
        # Copy the abnormal keywords list from the mediacheck_keywords object.
        keywords = self.mediacheck_keywords.ABNORMAL_KEYWORDS.copy()
        # Record the start time for performance measurement.
        start_time = time.time()
        # Iterate over the abnormal keywords list and check if any of them are in the log line.
        for keyword in keywords:
            if keyword in line:
                logging.info(f"{self.check_abnormal.__name__} keyword: {keyword}")
                # If an abnormal keyword is found, set the flag to True and exit the loop.
                flag_abnormal = True
                break
        # If the flag is True, register the current check function as an abnormal observer.
        if flag_abnormal:
            logging.info(f"flag_abnormal:{flag_abnormal}")
            self.register_abnormal_observer(self.check_abnormal.__name__)
        # Return the flag value.
        return flag_abnormal

    @allure.step("Check ott path playback status")
    def run_check_main_thread(self, during, **kwargs):
        # reset state and setup flags and lists
        self.reset()
        check_main_thread_flag = True
        self.abnormal_observer_list = []
        frame_count, vfm_map, dump_vdec_chunk = [], [], []
        start = time.time()

        # start log and AV sync threads
        self.start_save_log_thread(during, **kwargs)
        self.startAVSyncThread(during)

        # run checks until duration expires or an abnormal condition is detected
        while time.time() - start < during and len(self.abnormal_observer_list) == 0:
            # run checks and append results to lists
            frame_count.append('1' if self.checkFrame(**kwargs) else '0')
            vfm_map.append('1' if self.checkHWDecodePlayback(**kwargs) else '0')
            dump_vdec_chunk.append('1' if self.check_dump_vdec_chunks(**kwargs) else '0')

            # log the results
            logging.info(f'frame : {frame_count} , vfm : {vfm_map},  dump_vdec_chunk: {dump_vdec_chunk}')
            time.sleep(1)

            # prevent stop playback
            if pytest.target.get("prj") == "ott_hybrid_youtube_stress":
                self.run_shell_cmd("input keyevent 19")

        # analyze if the player gets stuck
        if "ott_stuck" not in kwargs:
            self.stuck_analysis_ott(**kwargs)

        # set flag based on results of checks
        if (not self.check_consecutive_zeros(frame_count)) or (not self.check_consecutive_zeros(vfm_map)) or \
                (not self.check_consecutive_zeros(dump_vdec_chunk)) or (
                len(self.abnormal_observer_list) != 0):
            check_main_thread_flag = False

        # log and return flag
        logging.info(f"{self.run_check_main_thread.__name__}: {check_main_thread_flag}")
        frame_count.clear()
        vfm_map.clear()
        dump_vdec_chunk.clear()
        return check_main_thread_flag

    def check_consecutive_zeros(self, lst):
        consecutive_count = 0
        for i in range(3, len(lst)):
            if lst[i] == '0':
                consecutive_count += 1
                if consecutive_count == 3:
                    return False
            else:
                consecutive_count = 0
        return True

    def get_abnormal_observer(self):
        if self.abnormal_observer_list:
            self.exitcode = 1  # if thread abnormal exit, set 1
            return True
        else:
            return False

    def register_abnormal_observer(self, name):
        self.abnormal_observer_list.append(name)
        logging.info(f"{self.register_abnormal_observer.__name__}: {self.abnormal_observer_list}")

    def abnormal_threadpool(self):
        # use a list with just one element instead of a list of strings
        abnormal_func_list = ["self.check_abnormal()"]
        abnormal_task_pool = threadpool.ThreadPool(1)
        requests = threadpool.makeRequests(self.check_abnormal_status, abnormal_func_list)
        [abnormal_task_pool.putRequest(req) for req in requests]

    # def common_threadpool(self):
    #     # use a list of functions instead of a list of strings
    #     common_func_list = ["self.check_v4lvideo_count()", "self.checkFrame()", "self.checkHWDecodePlayback()"]
    #     common_task_pool = threadpool.ThreadPool(6)
    #     requests = threadpool.makeRequests(self.check_common_status, common_func_list)
    #     [common_task_pool.putRequest(req) for req in requests]
    #     common_task_pool.wait()

    def common_threadpool(self, **kwargs):
        # 定义一个包含函数及其参数的元组列表
        common_func_list = [
            (self.checkHWDecodePlayback, []),
            (self.check_v4lvideo_count, []),
            (self.checkFrame, []),
        ]

        # self.common_task_pool = threadpool.ThreadPool(6)

        # 使用 makeRequests 构造请求
        requests = [
            threadpool.WorkRequest(self.check_common_status, args=[func], kwds=kwargs)
            for func, args in common_func_list
        ]

        # 将请求添加到线程池中
        [self.common_task_pool.putRequest(req) for req in requests]

        # 等待线程池执行完成
        self.common_task_pool.wait()

    def check_common_status(self, func, **kwargs):
        start_time = time.time()
        timeout = self.get_checkavsync_stuck_time()

        while time.time() - start_time < timeout:
            time.sleep(3)
            func(**kwargs)

            if self.get_abnormal_observer():
                break

    def start_save_log_thread(self, time_out, **kwargs):
        """
        Starts a new thread to check the log with the check_log function.
        If the scan_type argument in the kwargs is "Interlaced", the function returns True and does not start the log thread.
        :param time_out: timeout value
        :param kwargs: additional arguments
        :return: True if scan_type is Interlaced, otherwise None
        """
        # Check if "scan_type" argument in kwargs is "Interlaced"
        if len(kwargs) != 0:
            for k, v in kwargs.items():
                if (k == "scan_type") and (v == "Interlaced"):
                    return True
        # Start a new thread to check the log
        logging.info("start save log thread")
        stuck_avsync = threading.Thread(target=self.check_log, args=(time_out,))
        stuck_avsync.setDaemon(True)
        stuck_avsync.start()

    def check_play_after_restore(self, timeout, flag=True):
        self.reset()
        check_play = True
        self.restore = flag
        if self.checkFrame():
            logging.info("checkFrame true")
        else:
            check_play = False
        #     return check_play
        # start_time = time.time()
        # while time.time() - start_time < timeout:
        #     self.common_threadpool()
        #     if self.get_abnormal_observer():
        #         check_play = False
        #         break
        return check_play


    def check_abnormal_status(self, func):
        start_time = time.time()
        timeout = self.get_checkavsync_stuck_time()
        while time.time() - start_time < timeout:
            # logging.info("start abnormal thread")
            eval(func)
            if self.get_abnormal_observer():
                break

    def getVsync(self) -> float:
        """
        Get the VSYNC duration from the device.
        :return: VSYNC duration in seconds.
        """
        # Get the sync duration numerator from the device.
        vsync_info = self.run_shell_cmd('cat /sys/class/display/vinfo |grep "sync_duration_num"')[1]
        sync_duration_num = re.findall(r"sync_duration_num: (.*)?", vsync_info, re.S)[0]

        # Get the sync duration denominator from the device.
        vsync_info = self.run_shell_cmd('cat /sys/class/display/vinfo |grep "sync_duration_den"')[1]
        sync_duration_den = re.findall(r"sync_duration_den: (.*)?", vsync_info, re.S)[0]

        # Calculate the VSYNC duration by dividing the denominator by the numerator, and round it to 3 decimal places.
        vsync_duration = (int(sync_duration_den) / int(sync_duration_num)).__round__(3)

        # Log the VSYNC duration at debug level.
        logging.debug("vsync_duration: %s", vsync_duration)

        # Return the VSYNC duration.
        return vsync_duration

    def check_log(self, timeout: int) -> bool:
        """
        Check the log for abnormal lines and save the log to a file.
        :param timeout: The timeout in seconds for checking the log.
        :return: True if no abnormal line is found, False otherwise.
        """
        # If any of these conditions is true, skip the check.
        if self.speed or self.randomSeekEnable or self.switchAudio or self.pause or self.stop:
            return True

        # Log the start of the check.
        logging.info("start check stuck and avsync")

        # Set the media sync level for the device.
        self.setMediaSyncLevel()

        # Get the start time of the check.
        start_time = time.time()

        # Open a file to save the log to.
        with open(self.logdir + "/" + "check_stuck_avsync_audio.txt", "w+", encoding="utf-8") as f:
            # Keep reading the log until the timeout is reached.
            while time.time() - start_time < timeout:
                # Get a line from the log buffer, if available.
                outputValue_list = get_read_buffer()
                for line in outputValue_list:
                    # If a line is available, write it to the file and check if it's abnormal.
                    f.write(line)
                    # switch_subtitle_track_stress：stop writing data when displaying the last frame
                    if "loop_completed init" in line:
                        logging.info("video end")
                        logging.info(line)
                        if pytest.target.get("prj") == "ott_hybrid_switch_subtitle_track_stress":
                            return True
                    if self.check_abnormal(line):
                        # If an abnormal line is found, set the exit code to 1 and return False.
                        self.exitcode = 1
                        return False

        # The check is done, save and reset the media sync level.
        # name = "check_stuck_avsync_audio.txt"
        # self.save_need_logcat(name, self.get_checkavsync_stuck_time(),
        #                       tag="|grep -E 'AmCodecVDA|received_cnt|post_video_frame|prepare_display_buf|pw_vf_get"
        #                           "|v4lvideo|TsRenderer|updateVtBuffer|primary_swap_frame|output_pts|alsa "
        #                           "underrun|pes_pts|post_video_frame|aml_dtvsync|AML_MP_PLAYER_EVENT_DATA_LOSS'")
        # self.resetMediaSyncLevel()

        # Return True if no abnormal line is found.
        return True

    def stuck_avsync_audio_analysis(self):
        if (len(self.abnormal_observer_list) != 0):
            return False
        if self.speed or self.randomSeekEnable or self.switchAudio or self.pause or self.stop or self.playerNum >= 2:
            return True
        keywords = self.mediacheck_keywords.STUCK_KEYWORDS.copy()
        tsplayer_checkin_pts = []
        hwc_realtime_list = []
        mediasync_pts_list = []
        decoder_pts_list = []
        tsplayer_checkout_offset_pts = []
        pts_pes_list = []
        audio_output_pts = []
        alsa_underrun_list = []
        no_audio_count = 0
        video_data_loss_count = 0
        video_type = ""
        audio_stuck_start_flag = False
        vdec_core = self.print_vdec_core()
        if "h264" in vdec_core:
            video_type = "h264"
        elif "h265" in vdec_core:
            video_type = "h265"
        else:
            pass
        # DATA LOSS keyword
        data_loss_keywords = self.mediacheck_keywords.DATA_LOSS_KEYWORDS.copy()
        name = "check_stuck_avsync_audio.txt"
        if not os.path.exists(self.logdir + "/" + name):
            return True
        with open(self.logdir + "/" + name, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for l in lines:
                if self.speed or self.randomSeekEnable or self.switchAudio or self.pause or self.stop:
                    return True
                if l:
                    line = l.replace('\\r', '\r') \
                        .replace('\\n', '\n') \
                        .replace('\\t', '\t')
                    if data_loss_keywords[0] in line:
                        video_data_loss_count += 1
                        if video_data_loss_count >= 3:
                            flag_data = False
                            self.register_abnormal_observer(self.stuck_avsync_audio_analysis.__name__)
                            return flag_data
                    elif "AUDIO START" in line:
                        audio_stuck_start_flag = True
                    elif keywords["audio_hold"] in line:
                        time = self.getTime(line)
                        if "ResumeAudioDecoding finished" in self.checked_log_dict.keys():
                            resume_logtime = self.getTime(self.checked_log_dict["ResumeAudioDecoding finished"])
                            if time > resume_logtime:
                                no_audio_count += 1
                        if no_audio_count > 650:
                            logging.info(f"checked no audio:{no_audio_count}")
                            flag_audio = False
                            self.register_abnormal_observer(self.stuck_avsync_audio_analysis.__name__)
                            return flag_audio
                    elif keywords["tsplayer_checkin"] in line:
                        # print("poppy3", line)
                        # tsplayer_checkin = re.findall(r".*\[pts:.*\((.*)us\).*\[offset:(.*)\], checkinCount:(.*)", line)[0]
                        tsplayer_checkin = \
                            re.findall(r".*CheckinPtsSize -->size.* pts:.* pts64:(.*)us, offset:(.*)", line)[0]
                        tsplayer_checkin_logtime = self.getTime(line)  # ms
                        checkin_pts = float(tsplayer_checkin[0]) / 1000
                        tsplayer_checkin_pts.append((tsplayer_checkin_logtime, checkin_pts))
                    elif (keywords["hwcomposer"][0] and keywords["hwcomposer"][1]) in line:
                        # print("poppy6", keywords[6], line)
                        hwc_realtime = re.findall(r".*timestamp \((.*?) us\).*", line)[0]
                        hwc_logtime = self.getTime(line)
                        hwc_realtime_list.append((hwc_logtime, float(hwc_realtime) / 1000))
                    elif keywords["mediasync"] in line:
                        # print("poppy7", line)
                        # msync_info = re.findall(r".*\[pts:.*\((.*)us\)\]\[timestampNs:(.*)us\]", line)[0]
                        msync_info = \
                            re.findall(r".*onDrainTunnelVideoQueue \(rend\) ptsUs:(.*)\(.*\) timestampNs:(.*?)us.*",
                                       line)[
                                0]
                        msync_pts = float(msync_info[0]) / 1000  # ms
                        msync_realtime = msync_info[1]
                        # print("poppy8", msync_realtime)
                        msync_logtime = self.getTime(line)
                        mediasync_pts_list.append((msync_logtime, msync_pts, float(msync_realtime) / 1000))
                    elif keywords["tsplayer_checkout"] in line:
                        # print("poppy4", line)
                        # tsplayer_checkout = re.findall(r".*\[offset:(.*?)\)\]\[pts:.*\((.*)?us\)\]", line)[0]
                        tsplayer_checkout = \
                            re.findall(r".*CheckoutPtsOffset -->offset:(.*) duration:.* pts:.* pts64:(.*)us", line)[0]
                        tsplayer_checkout_logtime = self.getTime(line)
                        if "ffffffff" not in tsplayer_checkout[0]:
                            tsplayer_checkout_offset_pts.append(
                                (tsplayer_checkout_logtime, tsplayer_checkout[0], tsplayer_checkout[1]))
                    elif keywords["decoder_h264"] in line:  # decoder pts and logtime
                        # print("keywords[10]", line)
                        decoder_logtime = self.getTime(line)
                        if video_type == "h264":
                            # print("1107", line)
                            decoder_pts = re.findall(r".*post_video_frame: index.*pts64 .*\((.*)?\) ts", line)[0]
                            if "0xffffffffffffffff" not in decoder_pts:
                                decoder_pts_list.append(
                                    (decoder_logtime, int(decoder_pts, 16) & 0x00000000ffffffff))
                    elif keywords["decoder_h265"][0] in line and keywords["decoder_h265"][1] in line and \
                            keywords["decoder_h265"][2] in line:
                        decoder_logtime = self.getTime(line)
                        if video_type == "h265":
                            # print("1124", line)
                            # decoder_pts = re.findall(r".*post_video_frame\(type.*pts\(.*,(.*)\).*", line)[0]
                            decoder_pts = re.findall(r".*post_video_frame\(type.*pts\(.*,\s*(-?\d+)\(.*\)\).*", line)[0]
                            # print("decoder_pts", decoder_pts, line)
                            if "0xffffffffffffffff" not in decoder_pts:
                                decoder_pts_list.append((decoder_logtime, int(decoder_pts) & 0x00000000ffffffff))
                    elif keywords["decoder_mpeg"] in line:
                        decoder_logtime = self.getTime(line)
                        # decoder_pts = re.findall(r".*\[prepare_display_buf\].* pts: (.*?) .*", line)[0]
                        decoder_pts = re.findall(r"\[prepare_display_buf\].*pts64:.*?\((.*?)\)", line)[0]
                        if "0xffffffffffffffff" not in decoder_pts:
                            decoder_pts_list.append((decoder_logtime, int(decoder_pts, 16) & 0x00000000ffffffff))
                    elif keywords["audio_alsa"] in line:
                        alsa_logtime = self.getTime(line)
                        alsa_underrun_list.append((alsa_logtime, keywords["audio_alsa"]))
                    elif keywords["audio_pes_pts"][0] in line and keywords["audio_pes_pts"][1] in line and audio_stuck_start_flag:
                        # print("poppy9", keywords[9], line)
                        pts_pes_logtime = self.getTime(line)
                        pts_pes = \
                            re.findall(r".*pes_pts: (.*), frame_pts: .*, pcm\[.*total_dur:(.*)ms\]", line)[
                                0]
                        # pts_pes[0] = int(pts_pes[0], 16)/90  # ms
                        pts_pes_list.append((pts_pes_logtime, pts_pes[0], pts_pes[1]))
                    elif (keywords["audio_output_pts"][0] and keywords["audio_output_pts"][1]) in line and audio_stuck_start_flag:
                        audio_output_pts_logtime = self.getTime(line)
                        output_pts = re.findall(r".*frame_pts:.*, output_pts:([^.,]+)", line)[0]
                        output_pts_temp = "0x" + output_pts
                        if eval(output_pts_temp) & 0x8000000000000000 != 0x8000000000000000:
                            output_pts = int(output_pts, 16) / 90  # ms
                            audio_output_pts.append((audio_output_pts_logtime, output_pts))
                        else:
                            print(output_pts_temp)
                            logging.info("output_pts is abnormal, discard")
                    else:
                        pass
        flag_video_stuck = self.video_stuck_avsync_analysis(tsplayer_checkin_pts, tsplayer_checkout_offset_pts,
                                                            mediasync_pts_list, hwc_realtime_list, decoder_pts_list)
        flag_audio_stuck = self.audio_stuck_analysis(alsa_underrun_list, pts_pes_list, audio_output_pts)
        flag_avsync = self.avsync_analysis(mediasync_pts_list, hwc_realtime_list, audio_output_pts)
        logging.info("stuck and avsync analysis end")
        if flag_video_stuck or flag_audio_stuck or flag_avsync:
        # if flag_avsync:
            # if flag_video_stuck:
            self.register_abnormal_observer(self.stuck_avsync_audio_analysis.__name__)

    def video_stuck_avsync_analysis(self, tsplayer_checkin_pts, tsplayer_checkout_offset_pts, mediasync_pts_list,
                                    hwc_realtime_list, decoder_pts_list):
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
        # """
        # A: check if lost frame or not
        # """
        module_lost_frame = False
        #
        # """
        # 1. get hwc pts: mediasync has realtime and pts info, hwc has realtime info, according to corresponding realtime info, can get hwc pts
        # """
        for msync_ele in mediasync_pts_list:
            for hwc_ele in hwc_realtime_list:
                if hwc_ele[1] == msync_ele[2]:
                    hwc_pts_list.append((hwc_ele[0], msync_ele[1]))
        # logging.debug(f"hwc_pts_list: {hwc_pts_list}")
        """
        2. if hwc pts times < (checkin pts)*93%, think lost frame
        """
        checkin_pts = [checkin_pts[1] for checkin_pts in tsplayer_checkin_pts]
        logging.debug(f"hwc_pts_list: {hwc_pts_list}, checkin_pts: {checkin_pts}")
        hwc_pts = [hwc_pts[1] for hwc_pts in hwc_pts_list]
        if len(hwc_pts) != 0:
            if hwc_pts[-1] in checkin_pts:
                # if checkin_pts.index(hwc_pts[-1]):
                logging.debug(
                    f"hwc_pts: {hwc_pts}, len(hwc_pts): {len(hwc_pts)}, checkin_pts index: {sorted(checkin_pts).index(hwc_pts[-1]) + 1}")
                if len(hwc_pts) < (sorted(checkin_pts).index(hwc_pts[-1]) + 1) * 0.93:
                    flag_video_stuck = True
                    module_lost_frame = flag_video_stuck
        if module_lost_frame:
            logging.info(f"video stuck:  hwc pts times < (checkin pts)*93%")
            # return self.check_whichmodule_lost_frame(hwc_pts_list)
            return module_lost_frame

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
        pts_diff_list = [abs(float(checkout_pts_list[i + 1]) - float(checkout_pts_list[i])) for i in
                         range(len(checkout_pts_list) - 1)]
        logging.debug(f"pts_diff_list: {pts_diff_list}")
        if len(pts_diff_list) != 0:
            if min(pts_diff_list) != 0:
                stream_frame_rate = 1000000 / min(pts_diff_list)
        logging.debug(f"stream_frame_rate: {stream_frame_rate}")
        self.print_vdec_frame_rate(stream_frame_rate)
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
            # logging.info(f"total_pts:  {total_pts}")
            if float(total_pts) < float(stream_frame_rate) * 0.93:
                logging.info(f"video stuck:  total_pts < stream_frame_rate*0.93")
                flag_video_stuck = True

        if flag_video_stuck:
            logging.info(f"video stuck:  hwc pts output times < (strame frame rate)*96%")
            return flag_video_stuck

        """
        4. get hwc logtime diff, if hwc logtime diff < (3/stream_frame_rate), think frame output slowly or lost frame
        """
        flag_video_stuck = False
        hwc_logtime_diff = [(float(hwc_realtime_list[i + 1][0]) - float(hwc_realtime_list[i][0])) for i in
                            range(len(hwc_realtime_list) - 1)]
        logging.debug(f"hwc_logtime_diff: {hwc_logtime_diff}")
        count = 0
        try:
            for logtime_diff in zip(hwc_logtime_diff[1:], hwc_realtime_list[0]):
                if logtime_diff[0] > (3 / stream_frame_rate):
                    count += 1
                    if count > 6:
                        logging.info(f"video stuck: hwc logtime:{logtime_diff[1]}, logtime_diff:{logtime_diff}")
                        flag_video_stuck = True
        except Exception as e:
            logging.warning(f"{e}")
        if flag_video_stuck:
            logging.info(f"video stuck:  hwc logtime diff < (3/stream_frame_rate)")
            return flag_video_stuck
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
                logging.debug(
                    f"hwc_pts_list[i]: {hwc_pts_list[i]}, diffA:{diffA}, diffB:{diffB}, diffC: {diffC}, vsync_duration: {vsync_duration}, baseline: {baseline}")
                # calculate
                if (diffC - baseline > vsync_duration) and (diffA < 1):
                    logging.debug(f"diffC: {diffC}, baseline: {baseline}")
                    count += 1
                    logging.info("count fail")
                if diffC - baseline > vsync_duration:
                    baseline = diffC
            if count > 6:
                logging.info(f"count: {count}")
                flag_video_stuck = True
                module_frame_output_slowly = flag_video_stuck
        if module_frame_output_slowly:
            logging.info("video stuck: diffC > vsync_duration, need check which module stuck further")
            # return self.check_whichmodule_output_slowly(hwc_pts_list, diffC)
            return module_frame_output_slowly

    def print_vdec_frame_rate(self, stream_frame_rate):
        # check frame rate
        vdec_info = self.print_vdec_status()
        actual_frame_rate = vdec_info.split('frame rate : ')[1]
        logging.debug(f"actual_frame_rate: {actual_frame_rate}")
        if abs(float(re.findall(r"(.*) fps", actual_frame_rate)[0]) - float(stream_frame_rate)) < 1:
            stream_frame_rate = float(re.findall(r"(.*) fps", actual_frame_rate)[0])

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
        alsa_logtime_diff = [(alsa_underrun_list[ele + 1][0] - alsa_underrun_list[ele][0]) for ele in
                             range(len(alsa_underrun_list) - 1)]
        logging.debug(f"alsa_logtime_diff: {alsa_logtime_diff}")
        for ele in alsa_logtime_diff:
            if ele > 20 and len(alsa_underrun_list) >= 6:
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
        # Secondary processing, generating the last print list of each pes package
        for index, ele in enumerate(pts_pes_list):
            tmp_dict[int(ele[1], 16) / 90] = (ele[0], ele[1], ele[2])
        pts_pes_list = list(tmp_dict.values())
        logging.debug(f"pts_pes_list:{pts_pes_list}")
        # Start to calculate the total duration of each pes package
        flag_audio_stuck = False
        total_dur = 0
        pts_pes_diff = 0
        init_i = False
        old_i = 0
        standard_error = self.get_audiostuck_error()
        for i in range(len(pts_pes_list) - 1):
            # Adjust to ensure i and old_i not be less than 1 seconds, and will only be executed once at the beginning
            if not init_i and (pts_pes_list[i][0] - pts_pes_list[old_i][0]) < 1:
                total_dur = total_dur + int(pts_pes_list[i][2])
                continue
            init_i = True
            # check total duration
            pts_pes_diff = int(pts_pes_list[i][1], 16) / 90 - int(pts_pes_list[old_i][1], 16) / 90
            if pts_pes_diff / total_dur < 1 - standard_error or pts_pes_diff / total_dur > 1 + standard_error:
                logging.debug(f"audio stuck:  pes_pts diff/total_pcm_dur exceed 10% within 1s")
                logging.info(f"pts_pes_diff: {pts_pes_diff}, "f"total_dur:{total_dur}")
                flag_audio_stuck = True
                break
            else:
                logging.debug("non-ms12 Ok")
            total_dur = total_dur + int(pts_pes_list[i][2])
            # Adjust old_i, guarantee old_i and i not exceed 1 second
            while old_i + 1 < i and (pts_pes_list[i][0] - pts_pes_list[old_i][0]) >= 1:
                total_dur = total_dur - int(pts_pes_list[old_i][2])
                old_i = old_i + 1

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
        avdiff_list = []
        hwc_pts_list = []
        vsync_duration = self.getVsync()
        for msync_ele in mediasync_pts_list:
            for hwc_ele in hwc_realtime_list:
                if hwc_ele[1] == msync_ele[2]:
                    hwc_pts_list.append((hwc_ele[0], msync_ele[1] - 3 * vsync_duration))
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
                audio_output_pts.pop(min_avdiff_index)
                vpts = hwc_pts_list[i]
                avdiff_logtime = (apts[0] - vpts[0]) * 1000
                avdiff_pts = apts[1] - vpts[1]
                avdiff_list.append(((avdiff_pts - avdiff_logtime), hex(int(apts[1])), hex(int(vpts[1])), apts[0] * 1000))
                # print(apts, vpts)
            tmp_diff.clear()
        logging.debug(f"avdiff_list: {(avdiff_list)}")
        for ele in avdiff_list[20:]:
            if ele[0] < -200 or ele[0] > 200:
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

    def check_v4lvideo_count(self, **kwargs):
        if (len(self.abnormal_observer_list) != 0):
            return False
        if self.speed or self.switchAudio or self.randomSeekEnable or self.stop:
            return True
        logging.info("check v4lvideo count")
        if self.switchChannel:
            time.sleep(3)
        flag_v4l_count = True
        put_count, get_count, q_count, dq_count = self.get_v4lcount()
        if self.playerNum == 4:
            logging.info(
                f"temp: {self.four_way_put_count_temp, self.four_way_get_count_temp, self.four_way_q_count_temp, self.four_way_dq_count_temp},"
                f"count: {put_count, get_count, q_count, dq_count}")
            four_way_put_count = put_count.split('put_count: ')[1].split(',')[0:4]
            four_way_get_count = get_count.split('get_count: ')[1].split(',')[0:4]
            four_way_q_count = q_count.split('q_count: ')[1].split(',')[0:4]
            four_way_dq_count = dq_count.split('dq_count: ')[1].split(',')[0:4]
            # if ("0" in put_count.split(',')[0:4]) or ("0" in get_count.split(',')[0:4]) or (
            #         "0" in q_count.split(',')[0:4]) or ("0" in dq_count.split(',')[0:4]):
            #     flag_v4l_count = False

            for count_temp in list(
                    zip(four_way_put_count + four_way_get_count + four_way_q_count + four_way_dq_count,
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

        elif self.playerNum == 3:
            logging.info(
                f"temp: {self.three_way_put_count_temp, self.three_way_get_count_temp, self.three_way_q_count_temp, self.three_way_dq_count_temp},"
                f"count: {put_count, get_count, q_count, dq_count}")
            three_way_put_count = put_count.split('put_count: ')[1].split(',')[0:3]
            three_way_get_count = get_count.split('get_count: ')[1].split(',')[0:3]
            three_way_q_count = q_count.split('q_count: ')[1].split(',')[0:3]
            three_way_dq_count = dq_count.split('dq_count: ')[1].split(',')[0:3]
            # if ("0" in put_count.split(',')[0:3]) or ("0" in get_count.split(',')[0:3]) or (
            #         "0" in q_count.split(',')[0:3]) or ("0" in dq_count.split(',')[0:3]):
            #     flag_v4l_count = False

            for count_temp in list(
                    zip(three_way_put_count + three_way_get_count + three_way_q_count + three_way_dq_count,
                        (
                                self.three_way_put_count_temp + self.three_way_get_count_temp + self.three_way_q_count_temp + self.three_way_dq_count_temp))):
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

        elif self.playerNum == 2:
            logging.info(
                f"temp: {self.two_way_put_count_temp, self.two_way_get_count_temp, self.two_way_q_count_temp, self.two_way_dq_count_temp},"
                f"count: {put_count, get_count, q_count, dq_count}")
            two_way_put_count = put_count.split('put_count: ')[1].split(',')[0:2]
            two_way_get_count = get_count.split('get_count: ')[1].split(',')[0:2]
            two_way_q_count = q_count.split('q_count: ')[1].split(',')[0:2]
            two_way_dq_count = dq_count.split('dq_count: ')[1].split(',')[0:2]
            if self.pause:
                # print("pause: check v4lvideo")
                time.sleep(0.5)
                self.two_way_put_count_temp = two_way_put_count
                self.two_way_get_count_temp = two_way_get_count
                self.two_way_q_count_temp = two_way_q_count
                self.two_way_dq_count_temp = two_way_dq_count
                put_count, get_count, q_count, dq_count = self.get_v4lcount()
                if (set(self.two_way_put_count_temp) & set(put_count.split('put_count: ')[1].split(',')[0:2])) and (
                        set(self.two_way_get_count_temp) & set(
                    get_count.split('get_count: ')[1].split(',')[0:2])) and (
                        set(self.two_way_q_count_temp) & set(q_count.split('q_count: ')[1].split(',')[0:2])) and (
                        set(self.two_way_dq_count_temp) & set(dq_count.split('dq_count: ')[1].split(',')[0:2])):
                    pass
                else:
                    # logging.info(put_count.split('put_count: ')[1].split(',')[0:2])
                    flag_v4l_count = False
            else:
                # if ("0" in two_way_put_count) or ("0" in two_way_get_count) or (
                #         "0" in two_way_q_count) or ("0" in two_way_dq_count):
                #     flag_v4l_count = False
                for count_temp in list(
                        zip(two_way_put_count + two_way_get_count + two_way_q_count + two_way_dq_count,
                            (
                                    self.two_way_put_count_temp + self.two_way_get_count_temp + self.two_way_q_count_temp + self.two_way_dq_count_temp))):
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
            logging.info(
                f"temp: {self.put_count_temp, self.get_count_temp, self.q_count_temp, self.dq_count_temp},"
                f"count: {put_count, get_count, q_count, dq_count}")
            one_way_put_count = put_count.split('put_count: ')[1].split(',')[0:1]
            one_way_get_count = get_count.split('get_count: ')[1].split(',')[0:1]
            one_way_q_count = q_count.split('q_count: ')[1].split(',')[0:1]
            one_way_dq_count = dq_count.split('dq_count: ')[1].split(',')[0:1]
            # if ("0" in one_way_put_count) or ("0" in one_way_get_count) or (
            #         "0" in one_way_q_count) or ("0" in one_way_dq_count):
            #     flag_v4l_count = False
            if self.pause:
                # print("pause: check v4lvideo")
                time.sleep(0.1)
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
                    logging.info(put_count.split('put_count: ')[1].split(',')[0:1])
                    flag_v4l_count = False
            else:
                for count_temp in list(
                        zip(one_way_put_count + one_way_get_count + one_way_q_count + one_way_dq_count,
                            (
                                    self.put_count_temp + self.get_count_temp + self.q_count_temp + self.dq_count_temp))):
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
        return flag_v4l_count

    def get_audio_appl_ptr(self):
        audio_status = self.run_shell_cmd(self.AUDIO_APPL_PTR)[1]
        # logging.debug(f"audio_status: {audio_status}")
        appl_status = re.findall(r"appl_ptr.*\:(.*)\nclosed", audio_status, re.S)[0]
        appl_ptr = re.findall(r".*?\n", appl_status, re.S)[0]
        return appl_ptr

    def checkFrame(self, **kwargs):
        if ((self.check_disable_video() is False) and (pytest.target.get("prj") == "ott_sanity")) or (
                "evo" in kwargs.values()):
            return True
        # logging.info(f"kwargs: {kwargs}")  # {'pause_playerNum': 0, 'video_resolution': '4k_p60'}
        pause_playerNum = ""
        resume_playerNum = ""
        stop_playerNum = ""
        video_resolution = ""
        if "pause_playerNum" in kwargs:
            pause_playerNum = kwargs["pause_playerNum"]
        if "resume_playerNum" in kwargs:
            resume_playerNum = kwargs["resume_playerNum"]
        if "stop_playerNum" in kwargs:
            stop_playerNum = kwargs["stop_playerNum"]
        if "video_resolution" in kwargs:
            video_resolution = kwargs["video_resolution"]
            logging.info(f"video_resolution: {video_resolution}")

        start_time = time.time()
        if (len(self.abnormal_observer_list) != 0):
            return False
        flag_frame = False
        if not self.DISPLAYER_FRAME_COMMAND or self.randomSeekEnable or self.speed:
            logging.debug("frame count don't exist or in seek/speed status")
            flag_frame = True
            return flag_frame
        logging.info("check frame count")
        if self.getprop(self.get_android_version()) >= "11":
            # frame count only support at most 2 PIP way
            if self.playerNum == 2 and (pause_playerNum == 0 or resume_playerNum == 0 or stop_playerNum == 1) and (video_resolution != "4k_p60"):
                self.DISPLAYER_FRAME_COMMAND = "cat /sys/class/video_composer/receive_count_pip"
            elif self.getprop(self.get_android_version()) == "28":
                self.DISPLAYER_FRAME_COMMAND = "cat /sys/module/amvideo/parameters/new_frame_count"
            else:
                self.DISPLAYER_FRAME_COMMAND = "cat /sys/class/video_composer/receive_count"
        elif self.getprop(self.get_android_version()) == "9":
            self.DISPLAYER_FRAME_COMMAND = "cat sys/module/amvideo/parameters/new_frame_count"
        else:
            self.DISPLAYER_FRAME_COMMAND = "cat /sys/module/amvideo/parameters/display_frame_count"
        time.sleep(1)
        frame = self.run_shell_cmd(self.DISPLAYER_FRAME_COMMAND)[1]
        logging.info(f'frame_temp {self.frame_temp} - frame_current {frame}')
        if self.pause or self.stop:
            self.frame_temp = frame
            frame = self.run_shell_cmd(self.DISPLAYER_FRAME_COMMAND)[1]
            if int(frame) == int(self.frame_temp):
                logging.debug(f"true frame:{frame}, frame_temp:{self.frame_temp}")
                flag_frame = True
                logging.info(f'frame_temp {self.frame_temp} - frame_current {frame}')
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
        return flag_frame

    def checkHWDecodePlayback(self, **kwargs):
        """
        check vfm map, include PIP way
        """
        if ((self.check_disable_video() is False) and (pytest.target.get("prj") == "ott_sanity")) or (
                "evo" in kwargs.values()):
            return True
        if (len(self.abnormal_observer_list) != 0):
            return False
        logging.info(f"check vfm map: {self.playerNum}")
        stop_playerNum = ""
        if "stop_playerNum" in kwargs:
            stop_playerNum = kwargs["stop_playerNum"]
        flag_HWDecoder = False
        if not self.VFM_MAP_COMMAND:
            return False
        mapInfo_default = self.run_shell_cmd(f'{self.VFM_MAP_COMMAND}')[1]
        # logging.info(f"mapInfo_default:{mapInfo_default}")
        if self.getprop(self.get_android_version()) >= "11":
            if not self.check_player_path():  # ott path
                if "vcom-map-0 { video_composer.0(1) video_render.0}" in mapInfo_default:
                    flag_HWDecoder = True
                return flag_HWDecoder
            if self.stop:
                vdec_list = []
                # PIP way (self.playerNum > 1), stop_playerNum start from 1 to 4, represent from 1 way to 4 way
                if stop_playerNum in range(self.playerNum):
                    if (("vcom-map-0 { video_composer.0(1)" and "vcom-map-1 { video_composer.1(1)"
                         in mapInfo_default)):
                        for one in re.findall(r"vdec-map-.* \{ vdec.* v4lvideo.\d\}", mapInfo_default,
                                              re.S)[0].split("]  "):
                            if "vdec" in one:
                                vdec_list.append(one)
                        if len(vdec_list) == (self.playerNum - stop_playerNum):
                            logging.debug(f"len(vdec_list): {len(vdec_list)}")
                            flag_HWDecoder = True
                # single way
                else:
                    if ("vcom-map-0 { video_composer.0(1) video_render.0}" in mapInfo_default) and \
                            (len(re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\) dimulti.1\(1\) v4lvideo.0\}",
                                            mapInfo_default, re.S)) == 0):
                        flag_HWDecoder = True
            else:
                if self.playerNum == 2:
                    if (((
                                 "vcom-map-0 { video_composer.0(1)" and "vcom-map-1 { video_composer.1(1)") in mapInfo_default)
                            and re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\)",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-1 \{ vdec\..*.01\(1\)",
                                           mapInfo_default, re.S)):
                        flag_HWDecoder = True
                elif self.playerNum == 3:
                    if (((
                                 "vcom-map-0 { video_composer.0(1)" and "vcom-map-1 { video_composer.1(1)") in mapInfo_default)
                            and re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\)",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-1 \{ vdec\..*.01\(1\)",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-2 \{ vdec\..*.02\(1\)",
                                           mapInfo_default, re.S)):
                        flag_HWDecoder = True
                elif self.playerNum == 4:
                    if ((
                            "vcom-map-0 { video_composer.0(1)" and "vcom-map-1 { video_composer.1(1)" in mapInfo_default)
                            and re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\)",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-1 \{ vdec\..*.01\(1\)",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-2 \{ vdec\..*.02\(1\)",
                                           mapInfo_default, re.S)
                            and re.findall(r"vdec-map-3 \{ vdec\..*.03\(1\)",
                                           mapInfo_default, re.S)):
                        flag_HWDecoder = True
                else:
                    if (re.findall(r"vdec-map-0 \{ vdec\..*.00\(1\)", mapInfo_default,
                                   re.S)
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
        return flag_HWDecoder

    def setMediaSyncLevel(self):
        if "ott_sanity" not in pytest.target.get("prj"):
            self.run_shell_cmd(
                'setenforce 0;setprop vendor.media.mediahal.videodec.ptsserver_debug 1;'
                'setprop vendor.media.mediahal.videodec.ptsserver_debug 1;'
                'setprop vendor.media.mediahal.tsplayer.renderdebug 2;'
                'setprop vendor.hwc.debug 1;'
                'setprop vendor.hwc.debug.command "--log-verbose 1";'
                'dumpsys SurfaceFlinger > /dev/null;')
            self.run_shell_cmd(
                'echo 1 > /sys/module/amvdec_mh264/parameters/h264_debug_flag;'
                'echo 1 > /sys/module/amvdec_h265/parameters/debug;'
                'echo 0x0800 > /sys/module/amvdec_mmpeg12/parameters/debug_enable')
            self.run_shell_cmd('setprop vendor.media.audiohal.aut 1')
            if self.run_shell_cmd("cat /proc/sys/kernel/printk")[1][0] == "7":
                 self.run_shell_cmd("echo 4 > /proc/sys/kernel/printk")
        else:
            if self.getprop(self.get_android_version()) != "14":
                self.open_omx_info()

    def resetMediaSyncLevel(self):
        if "ott_sanity" not in pytest.target.get("prj"):
            self.run_shell_cmd("setprop vendor.media.mediahal.videodec.ptsserver_debug 0;"
                               "setprop vendor.media.mediahal.videodec.ptsserver_debug 0;"
                               "setprop vendor.media.mediahal.tsplayer.renderdebug 0;")
            self.run_shell_cmd("setprop vendor.hwc.debug 0;"
                               "echo 0 > /sys/module/amvdec_mh264/parameters/h264_debug_flag;"
                               "echo 0 > /sys/module/amvdec_h265/parameters/debug;"
                               "echo 0 > /sys/module/amvdec_mmpeg12/parameters/debug_enable")
            self.run_shell_cmd('setprop vendor.media.audiohal.aut 0')
        else:
            self.close_omx_info()

    def save_need_logcat(self, name, timeout, tag=''):
        """
        mediasync log include avsync, videoPts, videoDrop, stuck info and so on
        """
        # logging.info("save need logcat")
        log, logfile = self.save_logcat(name, tag)
        time.sleep(timeout)
        self.stop_save_logcat(log, logfile)
        # with open(logfile.name, "rb") as f:
        #     lines = f.readlines()
        # # print(lines)
        # return lines

    def checkavsync(self, during):
        """
        check ott path
        Returns:

        """
        if (len(self.abnormal_observer_list) != 0):
            return False
        flag_avsync = True
        if self.pause or self.stop or self.speed or self.randomSeekEnable or self.switchAudio:
            # logging.info("stop check avsync")
            return flag_avsync
        logging.info("check avsync")
        # IPTV/TV/OTT(<30): tsync, OTT(>=30) and vp9: mediasync, linux: msync
        # NU-AmNuPlayerRenderer: PTS: AV sync info:AV SYNCED
        if self.getprop(
                self.get_android_version()) >= "11" or self.videoType == "vp9" or self.sourceType == "tvpath":
            logging.debug("Android S: OTT path; Android R: MEDIASYNC TYPE; Analyze AmNuPlayer log")
            keywords = self.mediacheck_keywords.OTT_MEDIASYNC_KEYWORDS.copy()
            keywords = re.findall(r"(NU-AmNuPlayerRenderer: video late by) .* us \(.* secs\)", keywords[0])
            start_time = time.time()
            while time.time() - start_time < during:
                outputValue_list = get_read_buffer()
                # "NU-AmNuPlayerRenderer: video late by 145333616 us (145.33 secs)"
                # logging.info(f"outputValue: {outputValue}")
                for outputValue in outputValue_list:
                    # logging.info(f"checkavsync outputValue: {outputValue}")
                    actual_diff_pts = re.findall(r"NU-AmNuPlayerRenderer\: video late by (.*) us \((.*) secs\)",
                                                 outputValue)
                    if actual_diff_pts:
                        logging.info(f"[NU-AmNuPlayerRenderer] av diff pts is too large:{actual_diff_pts}")
                        flag_avsync = False
                    # "NU-AmNuPlayerRenderer: PTS: AV sync info:AV SYNCED"
                    else:
                        logging.debug("[NU-AmNuPlayerRenderer] think av synced!!!!!!")
                else:
                    logging.debug("[NU-AmNuPlayerRenderer] think av synced!!!!!!")
        else:
            logging.debug("TSYNC TYPE")
            # "I kernel  :  [68704.991449@0] VIDEO_TSTAMP_DISCONTINUITY failed, vpts diff is small, param:0x736cd4,
            # oldpts:0x7366f8, pcr:0x916671"
            keywords = self.mediacheck_keywords.TSYNC_KEYWORDS.copy()
            keywords = re.findall(
                r"(VIDEO_TSTAMP_DISCONTINUITY failed), vpts diff is small, param:.*, oldpts:.*, pcr:.*",
                keywords[0])
            for keyword in keywords:
                # "NU-AmNuPlayerRenderer: video late by 145333616 us (145.33 secs)"
                outputValue_list = get_read_buffer()
                for outputValue in outputValue_list:
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
        current_window = self.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
        if 'com.google.android.apps.youtube.tv.activity.MainActivity' in current_window or \
                "com.netflix.ninja/com.netflix.ninja.MainActivity" in current_window:
            return False
        else:
            if (self.getprop("media.ammediaplayer.enable") == "1" or self.getprop(
                    "vendor.media.ammediaplayer.normal.enable") == "1" or self.getprop(
                "vendor.media.ammediaplayer.drm.enable") == "1"):
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
        logging.debug(vdecInfo)
        return vdecInfo

    def print_codec_mm_dump(self):
        # print codec_mm dump info
        codec_dump = self.run_shell_cmd(self.CODEC_MM_DUMP_COMMAND)[1]
        logging.debug(codec_dump)
        return codec_dump

    def print_vdec_core(self):
        vdec_core = self.run_shell_cmd(self.VIDEO_TYPE_COMMAND)[1]
        logging.debug(vdec_core)
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
            logging.info(f"self.isPlaying:{self.isPlaying},isPlaying:{isPlaying}")
            try:
                logging.info("lock acquire")
                self.lock.acquire(timeout=10)
                self.isPlaying = isPlaying
                logging.info(f'setStateSafe isPlaying:{self.isPlaying}')
            finally:
                logging.info("lock release")
                self.lock.release()
                logging.info("lock release success")

    def setSourceType(self, sourceType):
        self.sourceType = sourceType

    def getSourceType(self):
        return self.sourceType

    def check_dump_vdec_chunks(self, **kwargs):
        """
        ott path: check if decoder has input buffer or not, if not, there will be no output buffer
        Returns:
        """
        if pytest.target.get("prj") == "ott_sanity":  # ott path
            dump_vdec_chunks = self.run_shell_cmd(self.DUMP_VDEC_CHUNKS)[1]
            if "evo" in kwargs.values():
                return True if "frame:0" in dump_vdec_chunks else False
            else:
                return False if "frame:0" in dump_vdec_chunks else True
        else:
            return True

    def stuck_analysis_ott(self, **kwargs):
        """
        For OTT path with Android S and U ref, check if playback stuck or not
        Args:
            **kwargs:

        Returns:

        """

        if (len(self.abnormal_observer_list) != 0):
            return False
        if self.speed or self.randomSeekEnable or self.switchAudio or self.pause or self.stop or self.playerNum >= 2:
            return True
        keywords = self.mediacheck_keywords.STUCK_KEYWORDS_OTT.copy()
        tunnel_mode = False
        name = "check_stuck_avsync_audio.txt"
        with open(self.logdir + "/" + name, "r", encoding="utf-8", errors="ignore") as f:
            outputValue = f.readlines()
        out_pts = []
        drop_pts = []
        for line in outputValue:
            if line and ("beginning of" not in line):
                line = line.replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t') \
                    .replace('\\', '')
                if re.match(r'\d{2}-\d{2}',line) and len(line) >= 11:
                    if line[8] == ':' and line[11] == ':' and line.count(line[:5]) == 1:
                        time = self.getTime(line)
                    else:
                        continue
                else:
                    continue

                if (keywords["Out PTS"][0] in line) and (keywords["Out PTS"][1] in line):
                    if keywords["Out PTS"][2] in line:  # Adaptation Netflix logs
                        out_pts_info = re.findall(r"Out PTS: (.*?), ", line)[0]
                        out_pts.append((time, out_pts_info))
                        tunnel_mode = True
                    else:
                        out_pts_info = re.findall(r"Out PTS: (.*?)\.\.", line)[0]
                        out_pts.append((time, out_pts_info))
                elif (keywords["MediaCodec"][0] in line):
                    out_pts_info = re.findall(r"render timeus:(\d+)", line)[0]
                    out_pts.append((time, out_pts_info))
                elif (keywords["MediaCodec"][1] in line):
                    drop_pts_info = re.findall(r"drop pts:(\d+)", line)[0]
                    drop_pts.append((time, drop_pts_info))
                elif (keywords["VideoTunnelWraper"][0] in line and keywords["VideoTunnelWraper"][1] in line):
                    out_pts_info = re.findall(r"queueBuffer \d+ (\d+)", line)[0]
                    out_pts.append((time, out_pts_info))
                else:
                    pass

        logging.debug(f"sanity ref out_pts {out_pts}")
        logging.debug(f"U sanity ref drop_pts {drop_pts}")

        # determine if there is output
        # if not out_pts:
        #     raise ValueError("out pts is empty")

        # judge drop, for android U ref
        drop_count = 0
        if len(drop_pts) > 2:
            base = 0
            for i in range(len(drop_pts) - 1):
                if drop_pts[i + 1][0] - drop_pts[base][0] <= 3000:
                    if float(drop_pts[i + 1][1]) - float(drop_pts[base][1]) >= 3000000:
                        drop_count += 1
                    if drop_count > 10:
                        self.register_abnormal_observer(self.stuck_analysis_ott.__name__)
                else:
                    base += 1
                    drop_count = 0

        # out pts increased, think pass
        # 通过Out PTS的打印，我们可以知道这一帧的pts信息。可以通过log中的系统时间和out pts的打印时间点，初步判断是否解码异常（卡顿、pts跳变
        out_pts_temp = []
        for i in range(len(out_pts) - 1):
            if out_pts[i + 1][0] >= out_pts[i][0]:
                if float(out_pts[i + 1][1]) > float(out_pts[i][1]):
                    pass
                elif float(out_pts[i + 1][1]) == float(out_pts[i][1]):
                    if out_pts[i + 1][0] - out_pts[i][0] < 1:
                        pass
                else:
                    out_pts_temp.append(out_pts[i])
        if len(out_pts_temp) >= 3:
            # check if stuck within 3s
            for i in range(len(out_pts_temp) - 1):
                if (out_pts_temp[i + 1][0] - out_pts_temp[i][0]) >= 3:
                    logging.info("checked android s ott path stuck", out_pts_temp[i + 1][0] - out_pts_temp[i][0])
                    self.register_abnormal_observer(self.stuck_analysis_ott.__name__)

    def check_demux(self):
        # single way
        if self.speed or self.switchAudio or self.randomSeekEnable or self.stop:
            return True
        logging.info("check demux")
        time.sleep(0.5)
        flag_demux = True
        flag_demux_list = []
        dmx_video_pid = ""
        dmx_audio_pid = ""
        dmx_filter_list = self.run_shell_cmd(self.DEMUX_FILTER)[1]
        dmx_filter_list = dmx_filter_list.split("\n")
        # print(f"dmx_filter_list, {dmx_filter_list} \n")
        for dmx_filter in dmx_filter_list:
            dmx_res = re.findall(
                r"(\d) dmx_id:(.*) sid:.* type:(.*) pid:(.*) mem total:.*, buf_base:.*, free size:.*, rp:(.*), wp:(.*), h rp:(.*), h wp:(.*), h mode:.*, sec_level:.*, aucpu:.*",
                dmx_filter)
            if dmx_res:
                print(dmx_res)
                if "vid" in dmx_res[0]:
                    self.vid_dmx_info_list.append(dmx_res[0][5:])
                    dmx_video_pid = dmx_res[0][3]
                if "aud" in dmx_res[0]:
                    self.aud_dmx_info_list.append(dmx_res[0][5:])
                    dmx_audio_pid = dmx_res[0][3]
        return dmx_video_pid, dmx_audio_pid

        # logging.debug(f"self.vid_dmx_info_list:{self.vid_dmx_info_list}")
        # logging.debug(f"self.aud_dmx_info_list:{self.aud_dmx_info_list}")
        # check demux normally if or not
        # for i in range(len(self.vid_dmx_info_list) - 1):
        #     # wp, write pointer
        #     if int(self.vid_dmx_info_list[i + 1][0], 16) - int(self.vid_dmx_info_list[i][0], 16) > 0:
        #         pass
        #     elif int(self.vid_dmx_info_list[i][1], 16) - int(self.vid_dmx_info_list[i][2], 16) == 0:
        #         pass
        #     else:
        #         flag_demux = False
        # for i in range(len(self.aud_dmx_info_list) - 1):
        #     # wp, write pointer
        #     if int(self.aud_dmx_info_list[i + 1][0], 16) - int(self.aud_dmx_info_list[i][0], 16) > 0:
        #         pass
        #     elif int(self.aud_dmx_info_list[i][1], 16) - int(self.aud_dmx_info_list[i][2], 16) == 0:
        #         pass
        #     else:
        #         flag_demux = False
        # if not flag_demux:
        #     flag_demux_list.append(1)
        #     if len(flag_demux_list) >= 3:
        #         self.register_abnormal_observer(self.check_demux.__name__)

    def reset(self):
        logging.info(f"[{self.__class__.__name__}][reset]")
        self.path = ""
        self.name = ""
        self.isPlaying = False
        self.restore = False
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
        self.abnormal_observer_list = []
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

        if self.yuv.yuvEnable:
            self.yuv.yuvChkSum = self.yuv.YUV_CHKSUM_NONE

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

    # def setYUVChkSum(self, chkSum):
    #     if self.yuvEnable:
    #         self.yuvChkSum = chkSum
    #
    # def getYUVChkSum(self):
    #     if self.yuvEnable:
    #         return self.yuvChkSum

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
        if self.getprop(self.get_android_version()) > "11":
            pass
        elif self.getprop(self.get_android_version()) == "11" or self.videoType == "vp9":
            self.p = self.popen(self.AVSYNC_OTT_LOG)
        else:
            self.p = self.popen(self.AVSYNC_IPTV_LOG)
        return self.p

    def startAVSyncThread(self, during):
        self.a = threading.Thread(target=self.checkavsync,
                                  args=(during,),
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

    def stopPlay(self):
        # Log playback end
        logging.info('Playback end')

        # Stop threads for checking VFM and frame count
        if "yuv" not in pytest.target.get("prj"):
            logging.info("Stop thread vfm and frame count")
            stop_thread(self.check_vfm_map_thread)
            stop_thread(self.check_frame_count_thread)
            logging.info("Stop thread vfm and frame count success")

        # Stop AV sync thread if enabled
        if self.avSyncChkEnable:
            self.stopAVSyncThread()

        # Stop seek thread if enabled
        if self.randomSeekEnable:
            self.seek = SeekFun()
            if self.sourceType == 'tvpath':
                self.seek.stopSeekThread()

        # Press back button twice to exit playback
        if "yuv" not in pytest.target.get("prj"):
            self.back()

        # Set player state to False
        self.setStateSafe(False)

        # Stop drop check thread if enabled
        if self.dropChkEnable:
            stop_thread(self.omxLogcat)
            self.dropCheck.count_iptv_drop()

    def saveYUVinfo(self, errType):
        logging.info(f'errType {errType}')

        # if yuv is enabled and there is no error
        if self.yuv.yuvEnable and errType == self.ERROR_TYPE_OK:
            # if decoding type is hw, get yuv result using hardware decoding
            if self.getDecodeType() == self.DECODE_TYPE_HW:
                self.yuv.setYUVChkSum(self.yuv.get_yuv_result())
            # if decoding type is sw, use pre-defined software decoding checksum
            elif self.getDecodeType() == self.DECODE_TYPE_SW:
                self.yuv.setYUVChkSum(self.yuv.YUV_CHKSUM_SW_DECODE)
            else:
                # TODO: handle other decoding types
                ...
        # if yuv is disabled, set error type and yuv checksum to "Yuv Off"
        elif not self.yuv.yuvEnable:
            self.setErrorType(errType)
            self.yuv.setYUVChkSum('Yuv Off')
        # if there is an error, set error type and yuv checksum to error checksum
        elif errType != self.ERROR_TYPE_OK:
            self.setErrorType(errType)
            self.yuv.setYUVChkSum(self.yuv.YUV_CHKSUM_ERR)

        # save the result with the current error and yuv checksum
        self.saveResult()

        # reset any internal state (if necessary)
        # self.reset()

    def logcatStop(self):
        """
        Stop logcat and logcat_avsync if they are running.

        Args:
            None

        Returns:
            None
        """
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
        """
        Returns the video name or path with ellipsis in between if it exceeds 48 characters.

        Args:
            None

        Returns:
            str: the video name or path
        """
        if self.name:
            if len(self.name) > 48:
                return self.name[:24] + '....' + self.name[-24:]
            else:
                return self.name
        else:
            return self.path

    def saveResult(self):
        """
        Saves the result of the video playback.

        Args:
            None

        Returns:
            None
        """
        log.save_yuv_resulttxt(self.getvideoName(), self.getPlayerType(), self.getDecodeType(), self.getErrorType(),
                               self.yuv.getYUVChkSum(), log.drop_times, self.avSyncChkEnable, self.counter)

    def setupDecodeType(self):
        """
        Sets up the decode type based on whether the video is being played using HW or SW decoder.

        Args:
            None

        Returns:
            None
        """
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
        """
        Checks the status of the video playback.

        Args:
            func (function): a function that returns True if the playback is successful, False otherwise
            errorType (str): the type of error if the playback fails

        Returns:
            None
        """
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
                    # logging.info(f"errorType:{errorType}")
                if len(count) > 30:
                    count.clear()
                # logging.debug("checkStatusLoop")
                time.sleep(3)

    def logcatStart(self):
        self.clear_logcat()
        if self.playerType == self.PLAYER_TYPE_LOCAL:
            self.logcat = self.popen('logcat -s %s' % self.TAG)
            self.logcatOpened = True
        elif self.getprop(self.get_android_version()) == "11" or self.videoType == "vp9":
            self.logcat_avsync = self.popen(self.AVSYNC_OTT_LOG)
            self.logcatOpened = True
        else:
            if self.sourceType == 'tvpath':
                self.logcat_avsync = self.popen(self.AVSYNC_TV_LOG)
                self.logcatOpened = True
            else:
                self.logcat_avsync = self.popen(self.AVSYNC_IPTV_LOG)
                self.logcatOpened = True

    def getLogcatRunTimerError(self):
        raise Exception('get logcat run time error')

    @set_timeout(50, getLogcatRunTimerError)
    def logcatReadLine(self):
        while True:
            if self.logcat and self.logcatOpened:
                log = self.logcat.stdout.readline()
                if log: return log.strip()

    def __repr__(self):
        return 'PlayerCheck_Base'

