#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/17
# @Author  : Jianhua.Huang
# @Site    :
# @File    : DVB.py
# @Email   : Jianhua.Huang@amlogic.com
# @Software: PyCharm

import logging
import re

from lib.common.system.ADB import ADB
import time
from tools.resManager import ResManager
from lib.common.checkpoint.DvbCheck import DvbCheck


dvb_check = DvbCheck()

LIVE_TV_TEST_APP_NAME = 'com.droidlogic.android.tv'


class DVB(ADB, ResManager):
    """
    Basic function broadcast api for DVB module
    """

    FRQ_LIST = ['474000', '578000', '322000', '330000', '338000', '346000', '354000', '362000']

    def __init__(self, set_channel_mode="cable"):
        ADB.__init__(self, "DVB", unlock_code="", stayFocus=True)
        self.channel_mode = set_channel_mode
        '''
            channel_mode:
                DVB-C: cable
                DVB-T: terrestrial
                DVB=S: satellite
        '''
        self.Livetv_test = 'livetv.test'
        self.DTVkit_test = 'android.action.search.channel'
        self.dvb_environment_detection()
        self.SUBTITLE_LIST = []

    def dvb_environment_detection(self):
        self.get_target('apk/inputsource.apk')
        self.get_target('apk/signed_platform_Tv-release.apk')
        # check LiveTv
        output = self.run_terminal_cmd(f'stat res/apk/signed_platform_Tv-release.apk')[1]
        livetv_for_server_time = str(re.findall(r"Change: (.+?) ", str(output)))[2:6]
        logging.info(f'livetv_for_server_time : {livetv_for_server_time}')
        livetv_for_dut_time = self.checkoutput(
            'dumpsys package com.droidlogic.android.tv | grep lastUpdateTime | head -n 1 ')
        logging.info(f'livetv_for_dut_time : {livetv_for_dut_time}')
        if livetv_for_server_time not in livetv_for_dut_time:
            cmd = ['install', '-r', '-d', 'res/apk/signed_platform_Tv-release.apk']
            logging.info(cmd)
            output = self.run_adb_cmd_specific_device(cmd)[1].decode().strip().split('\n')
            time.sleep(5)
            logging.info(output)
            if 'Success' in output:
                logging.info('APK install successful')
                assert True
            else:
                logging.info('APK install failed')
                assert False
        # check DTVkit
        output = self.run_terminal_cmd(f'stat res/apk/inputsource.apk')[1]
        inputsource_for_server_time = str(re.findall(r"Change: (.+?) ", str(output)))[2:6]
        logging.info(f'inputsource_for_server_time : {inputsource_for_server_time}')
        inputsource_for_dut_time = self.checkoutput(
            'dumpsys package com.droidlogic.dtvkit.inputsource | grep lastUpdateTime | head -n 1')
        logging.info(f'inputsource_for_dut_time : {inputsource_for_dut_time}')
        if inputsource_for_server_time not in inputsource_for_dut_time:
            self.run_adb_cmd_specific_device(['remount'])
            time.sleep(5)
            self.push('res/apk/inputsource.apk', '/vendor/app/inputsource/')
            logging.info("reboot , waiting for the device")
            self.reboot()
            start_time = time.time()
            logging.debug("Waiting for bootcomplete")
            while time.time() - start_time < 60:
                reboot_check = self.run_shell_cmd('getprop sys.boot_completed')[1]
                if reboot_check == '1':
                    logging.info("Device booted up !!!!")
                    break
                else:
                    time.sleep(5)
            logging.info("wait for the device enter the home page")
            check_time = time.time()
            while time.time() - check_time < 30:
                if self.find_element('Add account', 'text') or self.find_element('Search', 'text'):
                    break
                else:
                    time.sleep(5)
            self.root()
            self.run_adb_cmd_specific_device(['remount'])

    def broadcast_cmd(self, action, keywords):
        """

        Args:
            action:
            keywords:

        Returns:
            cmd
        """

        cmd = 'am broadcast -a ' + action + keywords
        logging.info(cmd)
        return cmd

    def set_channel_mode(self):
        logging.info("Set channel mode")
        self.run_shell_cmd(f'am broadcast -a android.action.set.channel.type -e search_type {self.channel_mode}')

    def start_livetv_apk(self, fre_count=1):
        # IPTV pipeline
        self.root()
        self.shell("setenforce 0")
        self.shell("setprop media.ammediaplayer.enable 1;setprop iptv.streamtype 1")

        cmd = 'am start -n ' + LIVE_TV_TEST_APP_NAME + '/com.android.tv.MainActivity'
        logging.info(cmd)
        self.clear_logcat()
        self.run_shell_cmd(cmd)
        time.sleep(5)
        if dvb_check.check_is_need_search():
            for i in range(fre_count):
                self.set_channel_mode()
                time.sleep(3)
                self.manual_search_by_freq(mode_qam='QAM16', frequency=self.FRQ_LIST[i])
                assert dvb_check.check_manual_search_by_freq()
                time.sleep(3)
            assert dvb_check.check_whether_search_missing()
        dvb_check.get_pvr_current_recording_pid()

    def start_livetv_apk_and_quick_scan(self):
        # IPTV pipeline
        self.root()
        self.shell("setenforce 0")
        self.shell("setprop media.ammediaplayer.enable 1;setprop iptv.streamtype 1")

        cmd = 'am start -n ' + LIVE_TV_TEST_APP_NAME + '/com.android.tv.MainActivity'
        logging.info(cmd)
        self.clear_logcat()
        self.run_shell_cmd(cmd)
        time.sleep(5)
        if dvb_check.check_is_need_search():
            self.set_channel_mode()
            time.sleep(3)
            self.quick_scan()
            assert dvb_check.check_quick_scan()

    def start_livetv_apk_and_auto_scan(self):
        # IPTV pipeline
        self.root()
        self.shell("setenforce 0")
        self.shell("setprop media.ammediaplayer.enable 1;setprop iptv.streamtype 1")

        cmd = 'am start -n ' + LIVE_TV_TEST_APP_NAME + '/com.android.tv.MainActivity'
        logging.info(cmd)
        self.clear_logcat()
        self.run_shell_cmd(cmd)
        time.sleep(5)
        if dvb_check.check_is_need_search():
            self.set_channel_mode()
            time.sleep(3)
            self.auto_search()
            assert dvb_check.check_search_ex()

    def stop_livetv_apk(self):
        self.app_stop(LIVE_TV_TEST_APP_NAME)

    def switch_channel(self, channel_id=1):
        logging.info('switch channel.')
        cmd = f"am start -a android.intent.action.VIEW -d content://android.media.tv/channel/{channel_id}"
        self.run_shell_cmd(cmd)

    def manual_search_by_id(self, symbolRate='6875', index='0'):
        logging.info('start manual search by ID.')
        action = 'android.action.search.channel'
        keywords = f' -e sync_status "sync_started" --ei searchmode 0 --ei symbolRate {symbolRate} --ei isfrequency 1 -e index {index}'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def manual_search_by_freq(self, symbolRate='6875', mode_qam='QAM64', frequency='602000'):
        logging.info('start manual search by freq.')
        action = 'android.action.search.channel'
        keywords = f' -e sync_status "sync_started" --ei searchmode 0 --ei symbolRate {symbolRate}  --ei isfrequency 0 -e mode_qam {mode_qam} -e frequency {frequency}'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def auto_search(self, action="", keywords=""):
        logging.info('start auto channel.')
        if not keywords:
            keywords = ' -e sync_status "sync_started" --ei searchmode 1 -e AutoscanType network -e operator KDG'
        if not action:
            action = self.DTVkit_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def quick_scan(self, action="", keywords=""):
        logging.info('start quick scan.')
        if not keywords:
            keywords = ' -e sync_status "sync_started" --ei searchmode 1 -e AutoscanType quick -e operator KDG'
        if not action:
            action = self.DTVkit_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def start_pvr_recording(self, action="", keywords=""):
        logging.info('start pvr recording')
        # dvb_check.get_pvr_current_recording_pid()
        if not keywords:
            keywords = ' --es command timely_recording'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def stop_pvr_recording(self, action="", keywords=""):
        logging.info('stop pvr recording')
        if not keywords:
            keywords = ' --es command stop_recording'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(5)

    def add_timer_recording(self, action="", keywords="", start_time=20, end_time=60):
        logging.info('add timed recording')
        # dvb_check.get_pvr_current_recording_pid()
        if not keywords:
            keywords = f' --es command timed_recording --el start_time {start_time} --el end_time {end_time}'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def delete_timer_recording(self):
        logging.info('deleter timer recording ')

    def pvr_start_play(self, action="", keywords_pvr="", keywords_replay='', intervals_time=2):
        logging.info('start pvr play')
        if not keywords_pvr:
            keywords_pvr = ' --es command pvr'
        if not keywords_replay:
            keywords_replay = ' --es command pvr_replay'
        if not action:
            action = self.Livetv_test
        cmd_pvr = self.broadcast_cmd(action=action, keywords=keywords_pvr)
        cmd_pvr_replay = self.broadcast_cmd(action=self.Livetv_test + '.pvr', keywords=keywords_replay)
        self.send_cmd(cmd_pvr)
        time.sleep(intervals_time)
        self.send_cmd(cmd_pvr_replay)

    def pvr_replay(self, action="", keywords_replay=''):
        logging.info('start pvr replay')
        if not keywords_replay:
            keywords_replay = ' --es command pvr_replay'
        if not action:
            action = self.Livetv_test
        cmd_pvr_replay = self.broadcast_cmd(action=action + '.pvr', keywords=keywords_replay)
        self.send_cmd(cmd_pvr_replay)

    def pvr_pause(self, action="", keywords=""):
        logging.info('pvr pause')
        if not keywords:
            keywords = ' --es command pvr_pause'
        if not action:
            action = self.Livetv_test + '.pvr.playback'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def pvr_resume(self, action="", keywords=""):
        logging.info('pvr resume')
        if not keywords:
            keywords = ' --es command pvr_resume'
        if not action:
            action = self.Livetv_test + '.pvr.playback'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def pvr_seek(self, action="", keywords="", seek_time=1000):
        logging.info('pvr seek')
        # if seek_time < 10:
        seek_time *= 1000
        if not keywords:
            keywords = f' --es command pvr_seek --ei seek_pos {seek_time}'
        if not action:
            action = self.Livetv_test + '.pvr.playback'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def pvr_current_seek(self, action="", keywords="", seek_time=1000):
        """
        Send pvr seek cmd that based on current position.

        Args:
            action:
            keywords:
            seek_time:

        Returns:

        """
        logging.info('pvr seek based on current position')
        if seek_time < 10:
            seek_time *= 1000
        if not keywords:
            keywords = f' --es command pvr_current_seek --ei seek_pos {seek_time}'
        if not action:
            action = self.Livetv_test + '.pvr.playback'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.clear_logcat()
        time.sleep(1)
        self.run_shell_cmd(cmd)

    def pvr_ff(self, action="", keywords=""):
        logging.info('pvr ff')
        if not keywords:
            keywords = ' --es command pvr_ff'
        if not action:
            action = self.Livetv_test + '.pvr.playback'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def pvr_fb(self, action="", keywords=""):
        logging.info('pvr fb')
        if not keywords:
            keywords = ' --es command pvr_fb'
        if not action:
            action = self.Livetv_test + '.pvr.playback'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def pvr_stop(self, action="", keywords=""):
        logging.info('pvr stop')
        if not keywords:
            keywords = ' --es command pvr_stop'
        if not action:
            action = self.Livetv_test + '.pvr.playback'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        # self.send_cmd(cmd)
        self.run_shell_cmd(cmd)

    def timeshift_start(self, action="", keywords=""):
        logging.info('timeshift start')
        if not keywords:
            keywords = ' --es command timeshift_start'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def timeshift_pause(self, action="", keywords=""):
        logging.info('timeshift pause')
        if not keywords:
            keywords = ' --es command timeshift_pause'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def timeshift_resume(self, action="", keywords=""):
        logging.info('timseshift resume')
        if not keywords:
            keywords = ' --es command timeshift_resume'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        return cmd

    def timeshift_seek(self, action="", keywords="", seek_time=1000):
        logging.info('timeshift seek')
        if not keywords:
            keywords = f' --es command timeshift_seek --ei seek_pos {seek_time}'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def timeshift_ff(self, action="", keywords=""):
        logging.info('timeshift ff')
        if not keywords:
            keywords = ' --es command timeshift_ff'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def timeshift_fb(self, action="", keywords=""):
        logging.info('timeshift fb')
        if not keywords:
            keywords = ' --es command timeshift_fb'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def timeshift_stop(self, action="", keywords=""):
        logging.info('timeshift stop')
        if not keywords:
            keywords = ' --es command timeshift_stop'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def switch_aspect_ratio(self, action="", keywords="", display_mode=0):
        logging.info('switch aspect ratio')
        """
            display_mode_list:
                0 :Auto
                1 :4:3
                2 :Panorama
                3 :16:9(Full screen)
                4 :dot by dot
        """
        logging.info('switch aspect ratio')
        if not keywords:
            keywords = f' --es command aspect_ratio_switch --ei display_mode {display_mode}'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def get_number_of_audio_track(self, action='', keywords='', logcat_filter=''):
        logging.info('get number of audio track')
        if not keywords:
            keywords = f' --es command get_audio_track'
        if not action:
            action = self.Livetv_test
        if not logcat_filter:
            logcat_filter = 'LiveTVTest'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        audio_track_number = 0
        self.root()
        log, logfile = self.save_logcat('logcat_get_audio_track.log', tag=logcat_filter)
        self.send_cmd(cmd)
        time.sleep(3)
        self.stop_save_logcat(log, logfile)
        logging.info('start getting the number of tracks')
        with open(logfile.name, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if 'Bundle' in line:
                logging.info(line)
                audio_track_number += 1
        logging.info(f'audio track number : {audio_track_number}')
        return audio_track_number

    def switch_subtitle_type(self, action="", keywords="", subtitle_type=1):
        self.clear_logcat()
        logging.info('switch subtitle type')
        q_subtitle_number = self.get_subtitle_list()
        logging.info(f'self.SUBTITLE_LIST : {self.SUBTITLE_LIST}')
        q_subtitle_type = self.SUBTITLE_LIST[subtitle_type]
        if not keywords:
            keywords = f' --es command subtitle_switch --es subtitle_option "{q_subtitle_type}"'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.run_shell_cmd(cmd)
        return q_subtitle_number

    def get_subtitle_list(self, action="", keywords=""):
        logging.info('Get subtitle list')
        if not keywords:
            keywords = f' --es command get_subtitle_list'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        logging.info('switch_subtitle')
        q_subtitle_number = 0
        self.root()
        log, logfile = self.save_logcat('logcat_get_subtitle.log', tag='LiveTVTest')
        self.run_shell_cmd(cmd)
        time.sleep(5)
        self.stop_save_logcat(log, logfile)
        logging.info('start getting the number of subtitle')
        with open(logfile.name, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if 'id=' in line:
                q_subtitle_number += 1
                line = line.split("\t")[0]
                q_subtitle_key_list = line.split(' ')
                q_subtitle_key = q_subtitle_key_list[len(q_subtitle_key_list) - 1]
                logging.debug(f"subtitle_key : {q_subtitle_key}")
                self.SUBTITLE_LIST.append(q_subtitle_key)
        logging.info(f'subtitle number : {q_subtitle_number}')
        return q_subtitle_number

    def get_current_channel_info(self):
        logging.info('Get current channel info')
        q_channel_id = ''
        q_channel_name = ''
        q_target_channel_number = ''
        self.run_shell_cmd('logcat -G 20m')
        log, logfile = self.save_logcat('get_channel_id.log', tag="MainActivity | grep 'tuneToChannel Channel'")
        time.sleep(20)
        self.stop_save_logcat(log, logfile)
        with open(logfile.name, 'r') as f:
            lines = f.readlines()
        logging.debug(f'lines : {lines}')
        for line in lines:
            logging.debug(f'line:{line}')
            if 'displayName' in line:
                q_channel_id = int(re.findall('id=(.*?),', line)[0])
                q_channel_name = re.findall('displayName=(.*?),', line)[0]
                q_target_channel_number = int(re.findall('displayNumber=(.*?),', line)[0])
        logging.debug(f'q_channel_name :{q_channel_name},  q_channel_id:{q_channel_id}, q_target_channel_number:'
                      f'{q_target_channel_number}')
        return q_channel_name, q_channel_id, q_target_channel_number

    def switch_teletext(self, action="", keywords=""):
        logging.info('switch_subtitle')
        if not keywords:
            keywords = f' --es command teletext_switch'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(3)
        self.keyevent(20)
        time.sleep(2)
        self.keyevent(23)
        self.keyevent(4)

    def check_display_mode(self):
        self.start_activity('com.android.tv.settings', '.system.CaptionSetupActivity')
        # self.uiautomator_dump()
        if self.find_element('com.android.tv.settings:id/preview_text', 'resource-id'):
            logging.debug('captions display is open')
            self.home()
        else:
            logging.debug('captions display is not open')
            self.wait_and_tap('Display', 'text')
            time.sleep(5)
            self.home()

    def switch_audio_track(self, action='', keywords='', audio_track_number=1):
        logging.info('switch audio track')
        if not keywords:
            keywords = f' --es command switch_audio --es switch_to {audio_track_number}'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def pvr_select_play(self, action='', keywords='', record_duration=16):
        logging.info('pvr select play')
        if not keywords:
            keywords = f' --es command pvr_select_play --es record_duration {record_duration}'
        if not action:
            action = self.Livetv_test + '.pvr'
        cmd_pvr = self.broadcast_cmd(action=self.Livetv_test, keywords=' --es command pvr')
        self.send_cmd(cmd_pvr)
        time.sleep(2)
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def change_switch_mode(self, mode):
        """
        mode:0 static frame
             1 black screen
        """
        prop = self.run_shell_cmd('getprop persist.switch.mode')[1]
        if not prop:
            prop = 0
        if prop == mode:
            logging.info(f'The switch mode is already {prop}')
        else:
            self.__change_switch_mode()
            self.run_shell_cmd(f'setprop persist.switch.mode {mode}')

    def __change_switch_mode(self):
        self.keyevent(82)
        self.wait_and_tap("TV Setting", "text")
        self.wait_and_tap("Settings", "text")
        self.wait_and_tap("Nosignal Screen Status", "text")
        self.wait_and_tap("Static Frame", "text")
        self.wait_and_tap("Black Screen", "text")

    def send_cmd(self, cmd):
        self.clear_logcat()
        logging.debug(f'cmd : {cmd}')
        self.run_shell_cmd(cmd)
