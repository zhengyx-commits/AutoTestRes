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
import os
import subprocess
import time
import pytest
from xml.dom import minidom
from lib.common.system.ADB import ADB
from tools.resManager import ResManager
from lib.common.checkpoint.DvbCheck import DvbCheck
from tools.yamlTool import yamlTool

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_freq = config_yaml.get_note('conf_freq')
wifi = config_yaml.get_note("external_wifi")
wifi_name = wifi["name"]
wifi_pwd = wifi["pwd"]

dvb_check = DvbCheck()
# serialnumber = pytest.config['device_id']
LIVE_TV_TEST_APP_NAME = 'com.droidlogic.android.tv'


class DVB(ADB, ResManager):
    """
    Basic function broadcast api for DVB module
    """

    # FRQ_LIST = ['474000', '578000', '322000', '330000', '338000', '346000', '354000', '362000']

    def __init__(self, set_channel_mode="cable"):
        ADB.__init__(self, "DVB", unlock_code="", stayFocus=True)
        self.channel_mode_dvbc = 'cable'
        self.channel_mode_dvbs = 'satellite'
        self.channel_mode_dvbt = 'terrestrial'
        '''
            channel_mode:
                DVB-C: cable
                DVB-T: terrestrial
                DVB=S: satellite
        '''
        self.Livetv_test = 'livetv.test'
        self.DTVkit_test = 'android.action.search.channel'
        self.DVBS_PARAMETER_ACTION = 'dtvkit.test'
        self.DVBS_SETUP_ACTION = 'android.action.dvbs.setup'
        self.DVBS_SCAN_ACTION = 'android.action.dvbs.scan'
        self.DVBT_SCAN_ACTION = 'android.action.dvbt.scan'
        self.SUBTITLE_LIST = []
        self.android_version = self.getprop(key="ro.build.version.release")
        self.dvb_environment_detection()

    def dvb_environment_detection(self):
        # android_version = self.getprop(key="ro.build.version.release")
        logging.info(f"android version: {self.android_version}")
        if self.android_version == '12':
            livetv_apk = 'androids/signed_platform_Tv-release.apk'
            dtvkit_apk = 'androids/inputsource.apk'
        elif self.android_version == '14':
            livetv_apk = 'androidu/Tv-release.apk'
            dtvkit_apk = 'androidu/inputsource.apk'
        elif self.android_version == '11':
            livetv_apk = 'androidr/Tv-release.apk'
            dtvkit_apk = 'androidr/inputsource.apk'
        else:
            assert False, "Can't get android version!"
        self.get_target(f'apk/{livetv_apk}')
        self.get_target(f'apk/{dtvkit_apk}')
        # check LiveTv
        output = self.run_terminal_cmd(f'stat res/apk/{livetv_apk}')[1]
        livetv_for_server_time = str(re.findall(r"Change: (.+?) ", str(output)))[2:6]
        logging.info(f'livetv_for_server_time : {livetv_for_server_time}')
        livetv_for_dut_time = self.checkoutput(
            'dumpsys package com.droidlogic.android.tv | grep lastUpdateTime | head -n 1 ')
        logging.info(f'livetv_for_dut_time : {livetv_for_dut_time}')
        if livetv_for_server_time not in livetv_for_dut_time:
            cmd = ['install', '-r', '-d', f'res/apk/{livetv_apk}']
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
        output = self.run_terminal_cmd(f'stat res/apk/{dtvkit_apk}')[1]
        inputsource_for_server_time = str(re.findall(r"Change: (.+?) ", str(output)))[2:6]
        logging.info(f'inputsource_for_server_time : {inputsource_for_server_time}')
        inputsource_for_dut_time = self.checkoutput(
            'dumpsys package com.droidlogic.dtvkit.inputsource | grep lastUpdateTime | head -n 1')
        logging.info(f'inputsource_for_dut_time : {inputsource_for_dut_time}')
        if inputsource_for_server_time not in inputsource_for_dut_time:
            logging.info("start reboot, root and remount.")
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
            self.root()
            time.sleep(3)
            self.run_adb_cmd_specific_device(['remount'])
            time.sleep(5)
            max_retries = 3
            retries = 0
            while retries < max_retries:
                try:
                    self.push(f'res/apk/{dtvkit_apk}', '/vendor/app/inputsource/')
                    # subprocess.check_output(['adb', '-s', self.serialnumber, 'push', 'res/apk/inputsource.apk', '/vendor/app/inputsource/'])
                    logging.info("inputsource is pushed！")
                    break
                except subprocess.CalledProcessError as e:
                    logging.info(f"push inputsource is failed：{e}")
                    retries += 1
                    # time.sleep(30)
                    self.root()
                    time.sleep(5)
                    self.remount()
                    time.sleep(5)
                    logging.info(f"retry push（the {retries} times）...")
            # self.push('res/apk/inputsource.apk', '/vendor/app/inputsource/')
            # self.push('res/apk/inputsource.apk', '/sdcard/')
            # self.run_shell_cmd(f'adb -s {self.serialnumber} shell pm install -r -d /sdcard/inputsource.apk')
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
            if self.android_version == '11':
                cmd = ['install', '-r', '-d', f'res/apk/{dtvkit_apk}']
                logging.info(cmd)
                output = self.run_adb_cmd_specific_device(cmd)[1].decode().strip().split('\n')
                time.sleep(5)
                logging.info(output)
                if 'Success' in output:
                    logging.info('inputsource apk install successful')
                    assert True
                else:
                    logging.info('inputsource apk install failed')
                    assert False

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

    def set_channel_mode_dvbc(self):
        logging.info("Set channel mode")
        cmd = f'am broadcast -a android.action.set.channel.type -e search_type {self.channel_mode_dvbc}'
        logging.info(f'cmd : {cmd}')
        self.run_shell_cmd(cmd)

    def start_livetv_apk(self):
        # IPTV pipeline
        self.root()
        self.shell("setenforce 0")
        self.shell("setprop media.ammediaplayer.enable 1;setprop iptv.streamtype 1")
        # start live TV
        cmd = 'am start -n ' + LIVE_TV_TEST_APP_NAME + '/com.android.tv.MainActivity'
        logging.info(cmd)
        self.send_cmd(cmd)
        time.sleep(5)
        if self.android_version == '11':
            logging.info('switch source to DTV')
            self.keyevent('KEYCODE_TV_INPUT')
            for i in range(10):
                self.keyevent('19')
                time.sleep(1)
            self.keyevent('20')
            self.keyevent('20')
            self.keyevent('23')
            time.sleep(3)

    def start_livetv_apk_and_manual_scan(self, fre_count=1, list_index=0):
        self.start_livetv_apk()
        if list_index:
            self.set_channel_mode_dvbc()
            time.sleep(3)
            self.manual_search_by_freq(mode_qam='AUTO', frequency=p_conf_freq[list_index] * 1000)
            assert dvb_check.check_manual_search_by_freq()
            time.sleep(3)
            assert dvb_check.check_whether_search_missing()
        else:
            if dvb_check.check_is_need_search():
                for i in range(fre_count):
                    self.set_channel_mode_dvbc()
                    time.sleep(3)
                    self.manual_search_by_freq(mode_qam='AUTO', frequency=p_conf_freq[i] * 1000)
                    assert dvb_check.check_manual_search_by_freq()
                    time.sleep(3)
                assert dvb_check.check_whether_search_missing()
        dvb_check.get_pvr_current_recording_pid()

    def start_livetv_apk_and_manual_scan_full_freq(self, freq=474):
        self.start_livetv_apk()
        if dvb_check.check_is_need_search():
            self.set_channel_mode_dvbc()
            time.sleep(3)
            self.manual_search_by_freq(mode_qam='AUTO', frequency=str(freq * 1000))
            if dvb_check.check_manual_search_by_freq() and dvb_check.check_whether_search_missing():
                assert True
            else:
                self.record_full_scan_failed_freq(freq)
                assert True
        # dvb_check.get_pvr_current_recording_pid()

    def record_full_scan_failed_freq(self, freq):
        """

        Args:
            freq:

        Returns:

        """
        with open('dvb_full_scan_failed_freq.log', 'a', encoding='utf-8') as f:
            f.write(str(freq) + '\n')
            f.close()

    def remove_full_scan_log(self):
        if os.path.isfile('./dvb_full_scan_failed_freq.log'):
            try:
                os.remove('./dvb_full_scan_failed_freq.log')
            except BaseException as e:
                print(e)
        else:
            logging.info('The dvb full scan log is not exit.')

    def start_livetv_apk_and_quick_scan(self, action="", keywords="", searchtype='quick', is_freq=False, frequency='362000', check_time=300):
        self.start_livetv_apk()
        if dvb_check.check_is_need_search():
            self.set_channel_mode_dvbc()
            time.sleep(3)
            logging.info(f'start auto {searchtype} scan.')
            if not keywords and is_freq:
                keywords = f' -e sync_status "sync_started" --ei searchmode 1 -e AutoscanType {searchtype} -e operator KDG -e frequency {frequency}'
            else:
                keywords = f' -e sync_status "sync_started" --ei searchmode 1 -e AutoscanType {searchtype} -e operator KDG'
            if not action:
                action = self.DTVkit_test
            cmd = self.broadcast_cmd(action=action, keywords=keywords)
            self.send_cmd(cmd)
            assert dvb_check.check_quick_scan(check_time=check_time)

    def start_livetv_apk_and_auto_scan(self, searchtype='full', check_time=900):
        self.start_livetv_apk()
        if dvb_check.check_is_need_search():
            self.set_channel_mode_dvbc()
            time.sleep(3)
            self.auto_search(searchtype=searchtype)
            assert dvb_check.check_search_ex(is_auto=True, check_time=check_time)

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

    def manual_search_by_freq(self, symbolRate='6875', mode_qam='AUTO', frequency='602000'):
        logging.info('start manual search by freq.')
        action = 'android.action.search.channel'
        keywords = f' -e sync_status "sync_started" --ei searchmode 0 --ei symbolRate {symbolRate}  --ei isfrequency 0 -e mode_qam {mode_qam} -e frequency {frequency}'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def auto_search(self, action="", keywords="", searchtype='full'):
        logging.info(f'start auto {searchtype} scan.')
        if not keywords:
            keywords = f' -e sync_status "sync_started" --ei searchmode 1 -e AutoscanType {searchtype} -e operator KDG'
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
        # if seek_time < 10:
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
        self.send_cmd(cmd)

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

    def close_teletext(self, action="", keywords=""):
        logging.info('close_subtitle')
        if not keywords:
            keywords = f' --es command teletext_switch'
        if not action:
            action = self.Livetv_test
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(3)
        self.keyevent(19)
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

    def switch_audio_during_pvr(self, track=0):
        logging.info('switch audio track during pvr playback')
        keywords = f' --es command switch_audio --ei switch_to {track}'
        action = self.Livetv_test + '.dvr'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def switch_subtitle_during_pvr(self, track=0):
        logging.info('switch subtitle track during pvr playback')
        keywords = f' --es command switch_subtitle --es switch_to {track}'
        action = self.Livetv_test + '.dvr'
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def timeshift_current_seek(self, duration=1000):
        logging.info('seek base on current time during timeshift')
        keywords = f' --es command timeshift_current_seek --ei seek_pos {duration}'
        action = self.Livetv_test
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
        time.sleep(1)
        # self.wait_and_tap("TV Setting", "text")
        # self.wait_and_tap("Settings", "text")
        # self.wait_and_tap("Nosignal Screen Status", "text")
        # self.wait_and_tap("Static Frame", "text")
        # self.wait_and_tap("Black Screen", "text")
        self.simulate_click('dvbtrunk', "TV Setting")
        self.simulate_click('dvbtrunk', "Settings")
        self.simulate_click('dvbtrunk', "Nosignal Screen Status")
        self.simulate_click('dvbtrunk', "Static Frame")
        self.simulate_click('dvbtrunk', "Black Screen")


    def get_ui_info(self, device):
        # os.system(f"adb -s {device} shell mkdir /sdcard/temp")
        os.system(f"adb -s {device} shell uiautomator dump > /dev/null")
        os.system(f"adb -s {device} pull /sdcard/window_dump.xml ./{device}_window_dump.xml > /dev/null")
        xml_path = f"./{device}_window_dump.xml"
        with open(xml_path, 'r') as f:
            temp = f.read()
        return temp

    def get_button_coordinates(self, device, text, attribute="text"):
        xml_path = f"./{device}_window_dump.xml"
        xml_file = minidom.parse(xml_path)
        item_list = xml_file.getElementsByTagName('node')
        bounds = None
        for item in item_list:
            # logging.debug(f'try to find {text} - {item.attributes[attribute].value}')
            if text == item.attributes[attribute].value:
                bounds = item.attributes['bounds'].value
                logging.info(f"Find {text} - {item.attributes[attribute].value}")
                break
        if bounds is None:
            logging.error("attr: %s not found" % attribute)
            return -1, -1
        bounds = re.findall(r"\[(\d+),(\d+)]", bounds)
        x_start, y_start = bounds[0]
        x_end, y_end = bounds[1]
        x_midpoint, y_midpoint = (int(x_start) + int(x_end)) / 2, (int(y_start) + int(y_end)) / 2
        return int(x_midpoint), int(y_midpoint)

    def simulate_click(self, device, searchKey):
        for i in range(6):
            assistant_info = self.get_ui_info(device)
            if f"text=\"{searchKey}\"" in assistant_info:
                x, y = self.get_button_coordinates(device, searchKey)
                logging.info(f">{searchKey}< coordinates:{x} {y}")
                os.system(f"adb -s {device} shell input tap {x} {y}")
                return
            else:
                logging.info(f'The searchKey {searchKey} is not found.')

    def send_cmd(self, cmd):
        self.clear_logcat()
        time.sleep(1)
        logging.debug(f'cmd : {cmd}')
        self.run_shell_cmd(cmd)

    # for DVB-S scan
    def set_channel_mode_dvbs(self):
        logging.info("Set channel mode")
        cmd = f'am broadcast -a android.action.set.channel.type -e search_type {self.channel_mode_dvbs}'
        logging.info(f'cmd : {cmd}')
        self.run_shell_cmd(cmd)
        time.sleep(2)
        if self.android_version == '14':
            for i in range(3):
                self.keyevent(20)
                time.sleep(1)
            self.keyevent(23)
        else:
            self.keyevent(23)
        time.sleep(1)

    def dvbs_scan(self, search_mode='satellite', channel_type=0, service_type=0, nit=0, lnb='1'):
        logging.info('start dvb-s scan.')
        # self.set_up_dvbs_parameter()
        self.keyevent('KEYCODE_PROG_BLUE')
        time.sleep(1)
        keywords = f' --es searchmode {search_mode} --ei channeltype {channel_type} --ei servicetype {service_type} --ei NIT {nit} --es LNB {lnb}'
        action = self.DVBS_SCAN_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def start_livetv_apk_and_dvbs_scan(self, search_mode='satellite', channel_type=0, service_type=0, nit=0, lnb='1'):
        logging.info('start LiveTV and start dvb_s scan')
        self.start_livetv_apk()
        if dvb_check.check_is_need_search():
            self.set_channel_mode_dvbs()
            self.dvbs_scan(search_mode, channel_type, service_type, nit, lnb)
            # assert dvb_check.check_dvbs_scan()

    def set_up_dvbs_parameter(self):
        logging.info('set up dvb_s parameter setting page.')
        # self.set_channel_mode_dvbs()
        # self.keyevent('KEYCODE_PROG_BLUE')
        action = self.DVBS_SETUP_ACTION
        cmd = self.broadcast_cmd(action=action, keywords='')
        self.send_cmd(cmd)
        time.sleep(2)

    def add_satellite(self, name='test', direction=True, longitude=0):
        logging.info('add satellite')
        keywords = f' --es command add_satellite --es satellite_name {name} --ez satellite_direction {direction} --ei satellite_longitude {longitude}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def edit_satellite(self, name_old='test', name_new='testEdit', direction=True, longitude=0):
        logging.info('edit satellite')
        keywords = f' --es command edit_satellite --es satellite_name_old {name_old} --es satellite_name_new {name_new} --ez satellite_direction {direction} --ei satellite_longitude {longitude}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def remove_satellite(self, name=''):
        logging.info('remove satellite')
        keywords = f' --es command remove_satellite --es satellite_name {name}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def select_satellite(self, satellite='0'):
        logging.info('select satellite')
        keywords = f' --es command select_satellite --es satellite {satellite}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(1)

    def reset_satellite_selection(self, satellite='0'):
        logging.info('reset satellite selection')
        keywords = f' --es command reset_satellite --es satellite {satellite}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(2)

    def reset_dvbs_param(self, satellite='0'):
        logging.info('reset dvb-s parameters.')
        self.start_livetv_apk()
        self.set_channel_mode_dvbs()
        self.set_up_dvbs_parameter()
        self.reset_satellite_selection(satellite)
        assert dvb_check.check_reset_satellite_selection()
        time.sleep(10)
        for i in range(5):
            self.keyevent(4)
            time.sleep(1)
            logging.info('----back----')
        # self.home()
        # time.sleep(1)

    def remove_dvbs_TP(self, sate_name='Thor 5/6', tp_name='4000H27500'):
        logging.info('remove TP.')
        self.start_livetv_apk()
        self.set_channel_mode_dvbs()
        self.set_up_dvbs_parameter()
        self.remove_transponder(sate_name, tp_name)
        assert dvb_check.check_remove_transponder()
        time.sleep(3)
        for i in range(5):
            self.keyevent(4)
            time.sleep(1)
            logging.info('----back----')
        # self.home()
        # time.sleep(1)

    def set_test_satellite(self, test_satellite=0):
        logging.info('set test satellite')
        keywords = f' --es command set_satellite --ei test_satellite {test_satellite}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(1)

    def add_transponder(self, sate_name='Thor 5/6', freq=10950, polarity='H', symbol=27500, is_dvbs2=False,
                        modulation='auto', fec='auto'):
        logging.info('add transponder')
        keywords = f' --es command add_transponder --es transponder_sate_name \"{sate_name}\" --ei transponder_freq {freq} --es transponder_polarity {polarity} --ei transponder_symbol {symbol} --ez transponder_is_dvbs2 {is_dvbs2} --es transponder_modulation {modulation} --es transponder_fec {fec}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(1)

    def remove_transponder(self, sate_name='Thor 5/6', tp_name='10950H27500'):
        logging.info('remove transponder')
        keywords = f' --es command remove_transponder --es transponder_sate_name \"{sate_name}\" --es transponder_name {tp_name}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(2)

    def set_test_transponder(self, test_transponder=0):
        logging.info('set test satellite')
        keywords = f' --es command set_transponder --ei test_transponder {test_transponder}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(1)

    def set_lnb_type(self, lnb_type='0', lowlocal=5150, highlocal=0):
        logging.info('set LNB type')
        if lnb_type != 'customize':
            keywords = f' --es command set_lnb_type --es lnb_type {lnb_type}'
        else:
            keywords = f' --es command set_lnb_type --es lnb_type customize --ei lnb_lowlocal {lowlocal} --ei lnb_highlocal {highlocal}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)
        time.sleep(1)

    def set_unicable(self, unicable_switch=0, user_band=0, ub_frequency=0, position=1):
        logging.info('set unicable')
        keywords = f' --es command set_unicable --ei unicable_switch {unicable_switch} --ei unicable_user_band {user_band} --ei unicable_ub_frequency {ub_frequency} --ei unicable_position {position}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def set_lnb_power(self, lnb_power=1):
        logging.info('set LNB power')
        keywords = f' --es command set_lnb_power --ei lnb_power {lnb_power}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def set_22khz(self, set_22khz=1):
        logging.info('set 22KHz')
        keywords = f' --es command set_22khz --ei 22khz {set_22khz}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def set_tone_burst(self, tone_burst=0):
        logging.info('set Tone Burst')
        keywords = f' --es command set_tone_burst --ei tone_burst {tone_burst}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def set_diseqc1_0(self, diseqc1_0=0):
        logging.info('set DisEqc1.0')
        keywords = f' --es command set_diseqc1_0 --ei diseqc1_0 {diseqc1_0}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def set_diseqc1_1(self, diseqc1_1=0):
        logging.info('set DisEqc1.1')
        keywords = f' --es command set_diseqc1_1 --ei diseqc1_1 {diseqc1_1}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def set_motor(self, motor=0):
        logging.info('set Motor')
        keywords = f' --es command set_motor --ei motor {motor}'
        action = self.DVBS_PARAMETER_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    # for DVB-T scan
    def set_channel_mode_dvbt(self):
        logging.info("Set channel mode")
        cmd = f'am broadcast -a android.action.set.channel.type -e search_type {self.channel_mode_dvbt}'
        logging.info(f'cmd : {cmd}')
        self.run_shell_cmd(cmd)
        time.sleep(3)

    def dvbt_manual_scan_by_freq(self, bandwidth='8MHZ', mode='2K', dvbtype='DVB-T', freq='474000'):
        logging.info('start dvb-s manual scan by freq.')
        keywords = f' --ei searchmode 0 --ei isfrequency 0 --es bandwidth {bandwidth} --es dvbtmode {mode} --es dvbttype {dvbtype} --es frequency {freq}'
        action = self.DVBT_SCAN_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def dvbt_manual_scan_by_id(self, index='0'):
        logging.info('start dvb-t scan.')
        keywords = f' --ei searchmode 0 --ei isfrequency 1 --es index {index}'
        action = self.DVBT_SCAN_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def dvbt_auto_scan(self, nit='true'):
        logging.info('start dvb-s auto scan.')
        keywords = f' --ei searchmode 1 --ez nit {nit}'
        action = self.DVBT_SCAN_ACTION
        cmd = self.broadcast_cmd(action=action, keywords=keywords)
        self.send_cmd(cmd)

    def connect_external_wifi(self):
        logging.info('connect test')
        count = 0
        connect_network_cmd = f"cmd wifi connect-network {wifi_name} wpa2 {wifi_pwd}"
        while count < 3:
            rc, connect_network_res = self.run_shell_cmd(connect_network_cmd)
            if "initiated" in connect_network_res:
                logging.debug("Connect wifi successfully!")
                break
            else:
                logging.info("Connect wifi failed! try again!")
                count += 1
        time.sleep(2)

    def open_ad_setting(self):
        self.keyevent("KEYCODE_MENU")
        for j in range(6):
            self.keyevent("KEYCODE_DPAD_DOWN")
        self.keyevent(22)
        self.keyevent(23)
        for j in range(5):
            self.keyevent("KEYCODE_DPAD_DOWN")
        self.keyevent(23)

    def skip_channel(self):
        self.keyevent("KEYCODE_MENU")
        for j in range(2):
            self.keyevent("KEYCODE_DPAD_DOWN")
        self.keyevent(22)
        for j in range(2):
            self.keyevent("KEYCODE_DPAD_DOWN")
        self.keyevent(23)
        for j in range(4):
            self.keyevent("KEYCODE_0")
        self.keyevent(23)
        time.sleep(1)
        self.keyevent(19)
        for i in range(7):
            self.keyevent(23)
            self.keyevent(19)
            time.sleep(1)
        for i in range(2):
            self.keyevent(19)
            self.keyevent(23)
            time.sleep(1)
        self.keyevent(4)
