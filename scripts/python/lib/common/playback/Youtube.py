#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/24 14:24
# @Author  : chao.li
# @Site    :
# @File    : Youtube.py
# @Software: PyCharm

import logging
import os
import re
import signal
import subprocess
import time

from lib.common.checkpoint.PlayerCheck_Youtube import PlayerCheck_Youtube
from lib.common.system.ADB import ADB
from lib.common.system.WIFI import WifiTestApk
from util.Decorators import set_timeout

from .OnlineParent import Online

playerCheck = PlayerCheck_Youtube()


class Youtube(Online):
    '''
    Youtube video playback

    Attributes:
        PLAYERACTIVITY_REGU : player command regular
        AMAZON_YOUTUBE_PACKAGENAME : amazon youtube package name
        PLAYTYPE : playback type
        DECODE_TAG : logcat tag
        GOOGLE_YOUTUBE_PACKAGENAME : google youtube package name
        YOUTUBE_DECODE_TAG : logcat tag
        VIDEO_INFO : video info
        VIDEO_TAG_LIST : play video info list [dict]

    '''

    PLAYERACTIVITY_REGU = 'am start -n com.google.android.youtube.tv/com.google.android.apps.youtube.tv.activity.ShellActivity -d https://www.youtube.com/watch?v={}'
    AMAZON_YOUTUBE_PACKAGENAME = 'com.amazon.firetv.youtube'
    PLAYTYPE = 'youtube'
    DECODE_TAG = 'AmlogicVideoDecoderAwesome2'
    GOOGLE_YOUTUBE_PACKAGENAME = 'com.google.android.youtube.tv'
    CURRENT_FOCUS = 'dumpsys window | grep -i mCurrentFocus'
    YOUTUBE_DECODE_TAG = 'C2VDAComponent'
    VIDEO_INFO = []

    VIDEO_TAG_LIST = [
        {'link': 'vX2vsvdq8nw', 'name': '4K HDR 60FPS Sniper Will Smith'},  # 4k hrd 60 fps
        # {'link': '9Auq9mYxFEE', 'name': 'Sky Live'},
        {'link': '-ZMVjKT3-5A', 'name': 'NBC News (vp9)'},  # vp9
        {'link': 'uKGWNdwBv8Y', 'name': 'Costa Rica 4K'},  # vp9
        {'link': 'LXb3EKWsInQ', 'name': 'COSTA RICA IN 4K 60fps HDR (ULTRA HD) (vp9)'},  # vp9
        {'link': 'b6fzbyPoNXY', 'name': 'Las Vegas Strip at Night in 4k UHD HLG HDR (vp9)'},  # vp9
        {'link': 'AtZrf_TWmSc', 'name': 'How to Convert,Import,and Edit AVCHD Files for Premiere (H264)'},  # H264
        {'link': 'LXb3EKWsInQ', 'name': 'COSTA RICA IN 4K 60fps HDR(ultra hd) (4k 60fps)'},  # 4k 60fps
        {'link': 'NVhmq-pB_cs', 'name': 'Mr Bean 720 25fps (720 25fps)'},
        {'link': 'ctwalU3o7MY', 'name': 'paid video'},
        {'link': 'rf7ft8-nUQQ', 'name': 'stress video'},
        {'link': 'hNAbQYU0wpg', 'name': 'VR 360 Video of Top 5 Roller (360)'},  # 360
        {'link': 'QjoYpj2G-ug', 'name': 'Optus Sport On The Road'},  # live vp9
        {'link': 'RO014qcVkJc', 'name': 'Spider man: Homecoming'},  # DRM
        {'link': 'NSxxrhnhjf4', 'name': 'Tokyo, Light Trail, 4K HDR HLG UHD (Shoot on RX100 VI)'},  # HLG
    ]

    def __init__(self, name=''):
        super(Youtube, self).__init__(name or 'Youtube')

    def youtube_playback(self, playback_format, repeat_time=0, seekcheck=False, switch_able=False, home_able=False):
        '''
        playback video from VIDEO_TAG_LIST
        @param seekcheck: seek check fun contril : boolean
        @return: None
        '''
        for i in self.VIDEO_TAG_LIST:
            if playback_format == "VP9":
                if i['link'] == "-ZMVjKT3-5A":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(30)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(30), f'play_error: {i}'
                    break
                elif i['link'] == "uKGWNdwBv8Y":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(30)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(300), f'play_error: {i}'
                    break
                else:
                    continue
            elif playback_format == "4kP60":
                if i['link'] == "vX2vsvdq8nw":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(10)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(10), f'play_error: {i}'
                    break
                else:
                    continue
            elif playback_format == "live":
                if i['link'] == "QjoYpj2G-ug":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(30)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(30), f'play_error: {i}'
                    break
                else:
                    continue
            elif playback_format == "AV1":
                if i['link'] == "NVhmq-pB_cs":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(30)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(30), f'play_error: {i}'
                    break
                else:
                    continue
            elif playback_format == "360":
                if i['link'] == "hNAbQYU0wpg":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(30)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(300), f'play_error: {i}'
                    break
                else:
                    continue
            elif playback_format == "paid_video":
                if i['link'] == "ctwalU3o7MY":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(30)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(30), f'play_error: {i}'
                    break
                else:
                    continue
            elif playback_format == "VP9 and AV1":
                if i['link'] == "NVhmq-pB_cs":
                    switch_able = not switch_able
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(30)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(30), f'play_error: {i}'
                    if not switch_able:
                        logging.info("switch successful")
                        return True
                elif i['link'] == "-ZMVjKT3-5A":
                    switch_able = not switch_able
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(30)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(30), f'play_error: {i}'
                    if not switch_able:
                        logging.info("switch successful")
                        return True
                else:
                    continue
            elif playback_format is None and seekcheck:
                if i['link'] == "-ZMVjKT3-5A":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(10)
                    playerCheck.check_secure()
                    self.keyevent("KEYCODE_DPAD_CENTER")
                    time.sleep(2)
                    self.keyevent("KEYCODE_DPAD_RIGHT")
                    time.sleep(2)
                    self.keyevent("KEYCODE_DPAD_CENTER")
                    time.sleep(30)
                    return playerCheck.check_seek()
                else:
                    continue
            elif playback_format is None and home_able:
                if i['link'] == "-ZMVjKT3-5A":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(10)
                    playerCheck.check_secure()
                    self.keyevent("KEYCODE_HOME")
                    time.sleep(2)
                    self.checkoutput(f'monkey -p {self.GOOGLE_YOUTUBE_PACKAGENAME} 1')
                    time.sleep(2)
                    return playerCheck.check_home_play()
                else:
                    continue
            elif playback_format == "stress":
                if i['link'] == "rf7ft8-nUQQ":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(10)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(repeat_time), f'play_error: {i}'
                    break
                else:
                    continue
            elif playback_format == "DRM":
                if i['link'] == "RO014qcVkJc":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(20)
                    playerCheck.check_secure()
                    #assert playerCheck.run_check_main_thread(repeat_time), f'play_error: {i}'
                    break
                else:
                    continue
            elif playback_format == "HLG":
                if i['link'] == "NSxxrhnhjf4":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(10)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(repeat_time), f'play_error: {i}'
                    break
                else:
                    continue
            elif playback_format == "HDR":
                if i['link'] == "LXb3EKWsInQ":
                    playerCheck.reset()
                    logging.info(f"Start playing Youtube - {i['name']}")
                    self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                    assert self.check_playback_status(), 'playback not success'
                    time.sleep(10)
                    playerCheck.check_secure()
                    assert playerCheck.run_check_main_thread(repeat_time), f'play_error: {i}'
                    break
                else:
                    continue
            else:
                playerCheck.reset()
                logging.info(f"Start playing Youtube - {i['name']}")
                self.playback(self.PLAYERACTIVITY_REGU, i['link'])
                assert self.check_playback_status(), 'playback not success'
                time.sleep(30)
                playerCheck.check_secure()
                if i['name'] == '4K HDR 60FPS Sniper Will Smith':
                    logging.info(playerCheck.check_frame_rate())
                    assert playerCheck.check_frame_rate() == '59', 'frame rate error'
                assert playerCheck.run_check_main_thread(30), f'play_error: {i}'
                if seekcheck == "True":
                    self.keyevent("KEYCODE_DPAD_CENTER")
                    time.sleep(5)
                    # TODO seek_check not found
                    playerCheck.seek_check()
                # self.home()

    def check_Youtube_exist(self):
        return True if self.GOOGLE_YOUTUBE_PACKAGENAME in self.checkoutput('pm list packages') else False

    def time_out(self):
        logging.warning('Time over!')
        if hasattr(self, 'logcat') and isinstance(self.logcat, subprocess.Popen):
            os.kill(self.logcat.pid, signal.SIGTERM)
            self.logcat.terminate()
        self.clear_logcat()

    def check_current_window(self):
        current_window = self.run_shell_cmd(self.CURRENT_FOCUS)[1]
        return current_window

    def stop_youtube(self):
        self.run_shell_cmd("am force-stop com.google.android.youtube.tv")
        time.sleep(2)
        count = 0
        while True:
            if self.GOOGLE_YOUTUBE_PACKAGENAME not in self.check_current_window():
                logging.info("youtube is closed successfully")
                break
            else:
                time.sleep(1)
                count = count + 1
            if count >= 5:
                self.run_shell_cmd("am force-stop com.google.android.youtube.tv")
                if self.GOOGLE_YOUTUBE_PACKAGENAME not in self.check_current_window():
                    logging.info("youtube is closed successfully")
                    break
                else:
                    raise ValueError("apk hasn't exited yet")
            else:
                logging.debug("continue check")
        self.kill_logcat_pid()
        self.run_shell_cmd("logcat -c")

    def init_youtube(self):
        # init youtube
        self.checkoutput(f'monkey -p {self.GOOGLE_YOUTUBE_PACKAGENAME} 1')
        time.sleep(20)

        # judge whether apk start is not
        start_time = time.time()
        current_window = self.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
        if 'com.google.android.apps.youtube.tv.activity.MainActivity' not in current_window:
            while time.time() - start_time < 60:
                self.run_shell_cmd('input keyevent 3')
                time.sleep(5)
                self.checkoutput(f'monkey -p {self.GOOGLE_YOUTUBE_PACKAGENAME} 1')
                time.sleep(10)
                current_window = self.run_shell_cmd('dumpsys window | grep -i mCurrentFocus')[1]
                if 'com.google.android.apps.youtube.tv.activity.MainActivity' not in current_window:
                    logging.debug("continue")
                else:
                    break
        else:
            logging.debug("APK OK")
        if 'com.google.android.apps.youtube.tv.activity.MainActivity' not in current_window:
            raise ValueError("apk hasn't exited yet")
        else:
            logging.debug("APK OK")

        self.uiautomator_dump()
        if 'Choose an account' in self.get_dump_info():
            logging.info('first time playback youtube ')
            self.enter()
            time.sleep(20)

    # @set_timeout(300, time_out)
    # def check_playback_status(self):
    #     '''
    #     check playback status
    #     @return:
    #     '''
    #     logging.info('start to check playback status')
    #     self.clear_logcat()
    #     self.logcat = self.popen("logcat -s %s" % self.YOUTUBE_DECODE_TAG)
    #     temp, count = 0, 0
    #     while True:
    #         line = self.logcat.stdout.readline()
    #         if 'onInputBufferDone' not in line:
    #             continue
    #         number = re.findall(r'bitstream id=(\d+)', line, re.S)[0]
    #         if int(number) > temp:
    #             count += 1
    #         if count > 30:
    #             logging.info('Video is playing')
    #             os.kill(self.logcat.pid, signal.SIGTERM)
    #             self.logcat.terminate()
    #             self.clear_logcat()
    #             return True
    #         temp = int(number)


class YoutubeFunc(WifiTestApk):

    YOUTUBE_PACKAGE = 'com.google.android.youtube.tv'
    YOUTUBE_APK = ''
    PLAY_COMMAND = "am start -n com.google.android.youtube.tv/com.google.android.apps.youtube.tv.activity.ShellActivity -d/' https://www.youtube.com/watch?v=DYptgVvkVLQ&list=RDMM8DvsTnWz3mo&index=3 /' "
    STOP_COMMAND = 'am force-stop com.google.android.youtube.tv'

    def __init__(self):
        super(YoutubeFunc, self).__init__()

    def check_Youtube_exist(self):
        return True if self.YOUTUBE_PACKAGE in self.checkoutput('pm list packages') else False

    def youtube_setup(self):
        if not self.check_Youtube_exist():
            assert self.install_apk("apk/" + self.YOUTUBE_APK)
        self.get_permissions()
        self.push_config()
        self.clear_logcat()

    def start_youtube(self):
        playerCheck.reset()
        name = "check_stuck_avsync_audio.txt"
        if os.path.exists(os.path.join(self.logdir, name)):
            os.remove(os.path.join(self.logdir, name))
        if not self.check_Youtube_exist():
            assert self.install_apk("apk/" + self.YOUTUBE_APK)
        self.run_shell_cmd(self.PLAY_COMMAND)
        time.sleep(60)
        playerCheck.check_secure()
        assert playerCheck.run_check_main_thread(30), 'play_error'
        logging.info("youtube is start successfully")

    def start_play(self):
        playerCheck.reset()
        if not self.check_Youtube_exist():
            assert self.install_apk("apk/" + self.YOUTUBE_APK)
        self.run_shell_cmd(self.PLAY_COMMAND)
        time.sleep(20)
        logging.info("youtube is start successfully")

    def stop_youtube(self):
        self.run_shell_cmd(self.STOP_COMMAND)
        logging.info("youtube is closed successfully")

    def connect_speed(self):
        self.clear_logcat()
        time.sleep(2)
        cmd_speed = 'Online_Playback'
        logging.info(f"{cmd_speed}")
        name = 'wifi_speed.log'
        log, logcat_file = self.save_logcat(name, 'WifiTest')
        self.run_shell_cmd(self.wifi_cmd.format(cmd_speed))
        self.stop_save_logcat(log, logcat_file)
        with open(logcat_file.name, 'r+') as f:
            for i in f.readlines():
                if 'Mbps' in i:
                    logging.info(f"Now the wifi speed is {i}")
