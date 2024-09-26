#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/24 14:24
# @Author  : chao.li
# @Site    :
# @File    : DRM.py
# @Software: PyCharm

import logging
import re
import subprocess
import time

import pytest

from lib.common.playback.OnlineParent import Online
from lib.common import config_yaml
from lib.common.avsync.avmonitor.av_libplayer_monitor import AVLibplayerMonitor
from lib.common.checkpoint.PlayerCheck_Exoplayer import PlayerCheck_Exoplayer
from lib.common.playback.LocalPlayer import LocalPlayer
from lib.common.system.Permission import Permission
from lib.common.system.ADB import ADB

"""
skip only audio videos and UHD videos
http://opengrok.amlogic.com:8080/source/xref/androidp/frameworks/base/core/java/android/view/KeyEvent.java
"""

P_CONFIG_DRM = config_yaml.get_note('conf_drm')

P_CONFIG_DRM_SKIP_VIDEO = P_CONFIG_DRM['skip_video']
P_CONFIG_DRM_SKIP_ITEM = P_CONFIG_DRM['skip_item']
P_CONFIG_DRM_DURING_10_VIDEO = P_CONFIG_DRM['during_10_video']
P_CONFIG_DRM_DURING_10 = P_CONFIG_DRM['during_10']
P_CONFIG_DRM_DEFAULT_DURING = P_CONFIG_DRM['default_during']
online = Online()


class DRM(ADB):
    TV_PACKAGE_NAME = "com.amazon.android.exoplayer2.demo"
    PRINTK_COMMAND = "echo 8 > /proc/sys/kernel/printk"
    DEBUG_MODE_COMMAND = "echo 0x30 > /sys/module/codec_mm/parameters/debug_mode"
    TV_EXOPLAYER_RUN_COMMAND = "monkey -p com.amazon.android.exoplayer2.demo 1"
    OTT_EXOPLAYER_RUN_COMMAND = "monkey -p com.droidlogic.exoplayer2.demo 1"
    RESET_DEBUG_MODE_COMMAND = "echo 0 > /sys/module/codec_mm/parameters/debug_mode"
    RESET_PRINTK_COMMAND = "echo 7 > /proc/sys/kernel/printk"

    def __init__(self, adb_cmd='', adb_tvp_cmd=''):
        super(DRM, self).__init__()
        self.playercheck = PlayerCheck_Exoplayer()
        self.avsync = AVLibplayerMonitor()
        self.permission = Permission()
        # self.localplayer = LocalPlayer(sourceType="tvpath")
        self.TVP_COMMAND = "cat /sys/class/codec_mm/codec_mm_dump | head -n 5 | grep -ir 'TVP' "
        self.adb_tvp_cmd = adb_tvp_cmd
        self.OMX_LOG_LEVEL = "setprop media.omx.log_levels 255"
        self.reset_OMX_LOG_LEVEL = "setprop media.omx.log_levels '' "
        self.adb_cmd = adb_cmd
        self.listed = False
        self.skip_video = False
        self.during_video = False
        self.ott_flag = False
        self.seek_advance_able = False
        self.seek_back_able = False
        self.home_able = False

    def set_ott_flag(self):
        self.ott_flag = True
        return self.ott_flag

    def playback(self):
        # start playback
        if not self.ott_flag:
            # set log level
            self.run_shell_cmd(self.OMX_LOG_LEVEL)
            self.run_shell_cmd(self.PRINTK_COMMAND)
            self.run_shell_cmd(self.DEBUG_MODE_COMMAND)
            self.run_shell_cmd("pm clear com.amazon.android.exoplayer2.demo")
            self.run_shell_cmd(self.TV_EXOPLAYER_RUN_COMMAND)
        else:
            if self.getprop("ro.build.version.sdk") == "34":
                self.run_shell_cmd("setprop debug.stagefright.c2-debug 3")
            self.run_shell_cmd("pm clear com.droidlogic.exoplayer2.demo")
            self.run_shell_cmd(self.OTT_EXOPLAYER_RUN_COMMAND)

    def player(self, video_name, video_sample_name, expect_vdec=None, expect_tvp=None):
        # TODO @chao.li : Cognitive Complexity from 19 to the 15 allowed
        logging.info(f"video_name:{video_name}, video_sample_name:{video_sample_name}, exprect_vdec:{expect_vdec}, "
                     f"expect_tvp:{expect_tvp}")
        # key down
        self.playercheck.reset()
        logging.info("keydown")
        self.keyevent(20)
        time.sleep(2)
        self.uiautomator_dump(self.logdir)
        self.keyevent(20)
        time.sleep(2)
        self.uiautomator_dump(self.logdir)
        # video = self.find_element(video_name, "text")
        if not video_name:
            return 'video_name is needed'
        if video_name not in P_CONFIG_DRM_SKIP_ITEM.values():
            if not self.listed:
                self.wait_and_tap(video_name, "text")
                self.keyevent(23)
                time.sleep(2)
                # self.uiautomator_dump(self.logdir)
                self.listed = True
            self.keyevent(20)
            time.sleep(2)
            self.uiautomator_dump(self.logdir)
        else:
            # if video_name skip, not wait_and_tap
            self.skip_video = True
            return True

        for skip_videos in P_CONFIG_DRM_SKIP_VIDEO.values():
            if skip_videos in video_sample_name:
                logging.debug(f"video_sample_name:{video_sample_name},skip_videos:{skip_videos}")
                self.skip_video = True
                self.uiautomator_dump(self.logdir)
                return True
        if self.skip_video:
            return None
        logging.debug(f"not skip self.skip_video:{self.skip_video}")
        for video in P_CONFIG_DRM_DURING_10_VIDEO.values():
            if video == video_sample_name or video == video_name:
                self.during_video = True
                result = self.config_video(video_sample_name, expect_vdec, expect_tvp,
                                           during_video=P_CONFIG_DRM_DURING_10)
                logging.info(f"return {'True' if result else 'False'}")
                return result
        # for video in during_2_video.values():
        #     if video==video_sample_name or video==video_name:
        #         self.during_video = True
        #         if self.config_video(video_sample_name, expect_vdec, expect_tvp, during_video=during_2):
        #             logging.info("return true")
        #             return True
        #         else:
        #             logging.info("return false")
        #             return False

        if not self.during_video:
            logging.info(f"default video_sample_name:{video_sample_name}")
            result = self.config_video(video_sample_name, expect_vdec, expect_tvp, during_video=False)
            logging.info(f"return {'True' if result else 'False'}")
            return result

    def config_video(self, video_sample_name, expect_vdec, expect_tvp=None, during_video=True):
        # time.sleep(3)
        print(during_video)
        self.during_video = during_video
        # clear dmesg
        self.run_shell_cmd("dmesg -c")
        self.wait_and_tap(video_sample_name, "text")
        if self.ott_flag:
            time.sleep(5)
        else:
            if self.during_video:
                time.sleep(5)
            else:
                time.sleep(2)
        if not self.during_video:
            result = self.video_sample_play(expect_vdec, expect_tvp, P_CONFIG_DRM_DEFAULT_DURING, video_sample_name)
            logging.info(f"video_sample_name default_during:{video_sample_name}" if result else '')
            return result
        else:
            result = self.video_sample_play(expect_vdec, expect_tvp, during_video, video_sample_name)
            logging.info(f"video_sample_name during:{video_sample_name}, during_video:{during_video}" if result else '')
            return result

    def check_secure(self, expect_tvp):
        codec_dump = self.run_shell_cmd(self.TVP_COMMAND)[1]
        codec_dump = str(codec_dump.split(",")[2])
        codec_dump = codec_dump.split(":")[1]
        logging.debug(f"codec_dump: {codec_dump}, expect_tvp: {expect_tvp}")
        if str(codec_dump) != "0":
            self.check_tvp_flag()
        elif str(codec_dump) == "0":
            assert str(expect_tvp) == str(codec_dump)

    def check_tvp_flag(self, timeout=40):
        start_time = time.time()
        # verify from logcat
        p = subprocess.Popen(self.adb_tvp_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        res = None
        while True:
            recv = p.stdout.readline()
            logging.debug(f"recv:{recv}")
            if re.search(b"decoder_bmmu_box_alloc_box, tvp_flags = 4", recv):
                res = True
                break
            else:
                res = False
                if time.time() - start_time > timeout:
                    break
        assert res

    def video_sample_play(self, expect_vdec, expect_tvp, during, video_sample_name):
        if not self.ott_flag:
            logging.info("TV exoplayer")
            if during == P_CONFIG_DRM_DEFAULT_DURING:
                self.playercheck.reset()
                self.playercheck.setSourceType("tvpath")
                play = online.check_playback_status()
                if play:
                    if self.pause(expect_vdec, expect_tvp,
                                  video_sample_name) and self.fastforward() and self.checkpoint(during):
                        self.avsync.stop_monitor()
                        # key back
                        self.keyevent(4)
                        return True
                else:
                    time.sleep(10)
                    error_time = self.checkoutput('TZ=UTC-8 date')
                    logging.info(f' ----- play error time : {error_time}')
                    logging.info('drm play error')
                    self.screenshot('drm_play_error')
                    return False
            else:
                self.playercheck.reset()
                self.playercheck.setSourceType("tvpath")
                if self.checkpoint(during):
                    self.avsync.stop_monitor()
                    # key back
                    self.keyevent(4)
                    return True
                else:
                    return False

        else:
            logging.info("ott exoplayer")
            self.playercheck.set_AndroidVersion_R_checkpoint()
            time.sleep(10)
            if self.seek_advance_able:
                self.keyevent(23)
                time.sleep(1)
                self.keyevent(20)
                time.sleep(2)
                self.keyevent(22)
                time.sleep(1)
                assert self.playercheck.check_seek(seek_advance_able=self.seek_advance_able)[0]
            elif self.seek_back_able:
                self.keyevent(23)
                time.sleep(1)
                self.keyevent(20)
                time.sleep(1)
                self.keyevent(21)
                self.keyevent(21)
                time.sleep(1)
                assert self.playercheck.check_seek(seek_back_able=self.seek_back_able)[0]
            elif self.home_able:
                logging.info("push home")
                self.keyevent("KEYCODE_HOME")
                time.sleep(2)
                logging.info("return to play")
                self.run_shell_cmd(self.OTT_EXOPLAYER_RUN_COMMAND)
                time.sleep(5)
                assert self.playercheck.check_home_play()[0]
            else:
                pass

            if self.seek_back_able or self.seek_advance_able:
                check_result = self.playercheck.run_check_main_thread(30, ott_stuck=True)
            else:
                check_result = self.playercheck.run_check_main_thread(30)
            if check_result:
                self.avsync.stop_monitor()
                # key back
                self.keyevent(4)
                return True
            else:
                self.screenshot('play_error')
                self.home()
                return False

    def pause(self, expect_vdec, expect_tvp, video_sample_name):
        logging.info("pause")
        # key pause
        # self.screenshot('drm_pause_before')
        self.keyevent(85)
        time.sleep(5)
        frame_before = self.run_shell_cmd(self.playercheck.DISPLAYER_FRAME_COMMAND)[1]
        time.sleep(3)
        self.playercheck.check_vdec_status(expect_vdec)
        logging.info(f'video_sample_name : {video_sample_name}')
        if 'Secure' in video_sample_name or 'secure' in video_sample_name:
            logging.info('check secure ...')
            assert self.playercheck.check_secure(), self.home()
        # assert self.playercheck.check_secure()
        frame_after = self.run_shell_cmd(self.playercheck.DISPLAYER_FRAME_COMMAND)[1]
        self.screenshot('drm_pause_after')
        logging.info(f"frame_before:{frame_before}, frame_after:{frame_after}")
        self.keyevent(85)
        time.sleep(1)
        return frame_after == frame_before

    def fastforward(self, timeout=55):
        logging.info("fastforward")
        # key fastforward
        self.keyevent(90)
        time.sleep(2)
        start_time = time.time()
        # verify from logcat
        p = subprocess.Popen(self.adb_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        res = None
        while True:
            recv = p.stdout.readline()
            logging.debug(f"recv:{recv}")
            if re.search(b"EventLogger: seekStarted", recv):
                res = True
                break
            else:
                res = False
                if time.time() - start_time > timeout:
                    break
        return res

    def checkpoint(self, during):
        logging.info("checkpoint")
        self.avsync.start_monitor()
        play_flag = self.playercheck.run_check_main_thread(during=during)
        if not play_flag:
            error_time = self.checkoutput('TZ=UTC-8 date')
            logging.info(f' ----- play error time : {error_time}')
            self.screenshot('checkpoint_error')
            self.home()
            self.reset()
        return play_flag

    def reset(self):
        # reset property
        self.run_shell_cmd(self.RESET_DEBUG_MODE_COMMAND)
        self.run_shell_cmd(self.RESET_PRINTK_COMMAND)
        self.run_shell_cmd(self.reset_OMX_LOG_LEVEL)
