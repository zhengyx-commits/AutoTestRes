#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/24 14:24
# @Author  : chao.li
# @Site    :
# @File    : Netflix.py
# @Software: PyCharm

import logging
import os
import re
import signal
import time
import zipfile
import allure

from lib import CheckAndroidVersion
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from util.Decorators import set_timeout
from .OnlineParent import Online
from tools.resManager import ResManager
# from tools.OBS import OBS
#
#
# obs_config_dict = {
#     'Netflix_dvb_trunk': {'ip': '10.18.19.16', 'port': 4455, 'pwd': 'Linux2017', 'source_name': 'Netflix_dvb_trunk'},
#     'Netflix_dvb_stress_player_switch': {'ip': '10.18.19.16', 'port': 4455, 'pwd': 'Linux2017', 'source_name': 'Netflix_dvb_stress_player_switch'}
# }
res = ResManager()
check_android_version = CheckAndroidVersion()
player_check = PlayerCheck_Base()


class Netflix(Online):
    '''
    netflix test lib

    Attributes:
        PLAYBACK_COMMAND_FORMAT : netflix playback command format (need video link)
        PLAYTYPE : playback type
        ACCOUNT : test account
        PASSWORD : test passwd
        DECODE_TAG : logcat decode tag
        VIDEO_TAG_LIST : test video info : list [dict]
        VIDEO_INFO : video info

    '''

    PLAYBACK_COMMAND_FORMAT = ('am start -n com.netflix.ninja/com.netflix.ninja.MainActivity '
                               '-a android.intent.action.VIEW -d https://www.netflix.com/watch/{}?source=99')
    PACKAGE_NAME = 'com.netflix.ninja'
    PLAYTYPE = 'Netflix'
    # ACCOUNT = 'amlqatest2@amlogic.com'
    # PASSWORD = 'Amlqa456'
    ACCOUNT = 'tester_autsanity@netflix.com'
    PASSWORD = 'Amlogic@123m'
    # ACCOUNT = 'tester_ntsauto@netflix.com'
    # PASSWORD = 'Linux2017!'
    DECODE_TAG = 'AmlogicVideoDecoderAwesome2'
    VIDEO_INFO = []

    # VIDEO_TAG_LIST = [
    #     {'link': '80010857', 'name': 'Marco Polo S1:E2 The Wolf and the Deer'},  # H.265
    #     {'link': '80190487', 'name': 'Giri/Haji S1:E1'},  # DolbyVision + Atmos H265
    #     {'link': '80003008', 'name': 'Peaky Blinders S1:E1'},  # DolbyVision + Atmos av1
    #     {'link': '80138257', 'name': 'Lucifer S1:E2 Lucifer,Stay.Good Devil.'},
    #     # DolbyVision + 5.1 av1
    #     {'link': '80006792', 'name': 'Tears of Steel'},  # H265
    #     # {'link': '80221640', 'name': '超级破坏王'},
    #     # {'link': '80104446', 'name': 'SCREAM'},
    #     # {'link': '70118402', 'name': 'Salt'}
    #     {'link': '80164308', 'name': 'Minaculous'}
    # ]
    # VIDEO_TAG_LIST = [{"link": "80993016", "name": "Matilda The Musical", "core": "amvdec_h265_v4l"},
    #                   {"link": "70137742", "name": "Rango", "core": "amvdec_av1_v4l"},
    #                   {"link": "80196613", "name": "12 Strong", "core": "amvdec_h264_v4l"}]
    VIDEO_TAG_LIST = [{"link": "80993016", "name": "Matilda The Musical", "core": "amvdec_h265_v4l"}]

    def __init__(self, name=''):
        super(Netflix, self).__init__(name)

    def login(self):
        '''
        login netflix
        @return: None
        '''
        logging.info('input account')
        time.sleep(2)
        self.text(self.ACCOUNT)
        time.sleep(2)
        self.keyevent(20)
        time.sleep(2)
        self.keyevent(20)
        time.sleep(2)
        self.keyevent(20)
        self.enter()
        logging.info('input passwd')
        self.text(self.PASSWORD)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        time.sleep(1)
        self.keyevent(20)
        time.sleep(1)
        self.enter()
        time.sleep(60)
        self.enter()
        time.sleep(3)
        logging.info('login done')

    def check_Netflix_exist(self):
        return True if self.PACKAGE_NAME in self.checkoutput('pm list packages') else False

    def start_play(self):
        '''
        start playback
        @return: none
        '''
        player_check.reset()
        video = self.VIDEO_TAG_LIST[0]
        logging.info(f"Start playing Netflix - {video['name']}")
        self.playback(self.PLAYBACK_COMMAND_FORMAT, video['link'])
        time.sleep(20)  # wait Netflix start
        self.keyevent("23")  # enter play,skip preview
        play = self.check_playback_status()
        time.sleep(30)
        if play:
            player_check.check_secure()
            name = "check_stuck_avsync_audio.txt"
            if os.path.exists(os.path.join(self.logdir, name)):
                os.remove(os.path.join(self.logdir, name))
            assert player_check.run_check_main_thread(during=30), f'play_error'
            player_check.reset()  # reset frame_temp list
            logging.info("netflix is start successfully")
        else:
            return False

    def stop_netflix(self):
        '''
        stop netflix
        @return: None
        '''
        stop_cmd = f'am force-stop {self.PACKAGE_NAME}'
        self.run_shell_cmd(stop_cmd)
        logging.info("nexflix is closed successfully")

    def time_out(self):
        logging.warning('Time over!')

    @allure.step("Check Netflix playback status")
    @set_timeout(60, time_out)
    def check_playback_status(self):
        '''
        check if video is start playback
        @return: status : boolean
        '''
        logging.info('Start check playback status')
        self.clear_logcat()
        self.logcat = self.popen("logcat -s %s" % self.DECODE_TAG_AndroidS)
        android_version = self.getprop(check_android_version.get_android_version())
        temp, count = 0, 0
        while True:
            line = self.logcat.stdout.readline()
            if android_version == "31":
                if 'ServiceDeviceTask' not in line:
                    continue
            else:
                if 'AllocTunneledBuffers' not in line:
                    continue
            number = re.findall(r'IN\[(\d+),\d+\]', line, re.S)[0]
            logging.info(f'buffer count {number} , temp{temp}')
            if int(number) > temp:
                count += 1
            if count > 5:
                logging.info('Video is playing')
                os.kill(self.logcat.pid, signal.SIGTERM)
                self.logcat.terminate()
                self.clear_logcat()
                return True
            temp = int(number)

    @allure.step("Check login status and login Netflix")
    def netflix_setup(self):
        '''
        set ui enter login interface
        @return: None
        '''
        if self.getprop("ro.build.version.sdk") != "34":
            self.open_omx_info()
            self.checkoutput('tee_provision -q -t 0x43')
        check_account = str(self.subprocess_run('ls -la /data/data/com.netflix.ninja/files/activated'))
        logging.debug(f'check_account is {check_account}')
        if 'returncode=1' in check_account:
            self.run_shell_cmd(f"monkey -p {self.PACKAGE_NAME} 1")
            time.sleep(60)
            logging.info('start to login')
            self.keyevent(21)
            time.sleep(2)
            self.keyevent(23)
            time.sleep(2)
            self.keyevent(22)
            time.sleep(2)
            self.keyevent(23)
            time.sleep(6)
            self.text(self.ACCOUNT)
            logging.info('exit login')
            time.sleep(2)
            self.keyevent(20)
            time.sleep(2)
            self.keyevent(20)
            time.sleep(2)
            self.keyevent(20)
            time.sleep(2)
            self.keyevent(23)
            time.sleep(6)
            logging.info('input passwd')
            self.text(self.PASSWORD)
            time.sleep(2)
            logging.info('exit passwd')
            self.keyevent(20)
            time.sleep(2)
            self.keyevent(20)
            time.sleep(2)
            self.keyevent(20)
            time.sleep(2)
            self.keyevent(20)
            time.sleep(2)
            self.keyevent(20)
            time.sleep(2)
            self.keyevent(22)
            time.sleep(2)
            self.keyevent(23)
            time.sleep(30)
            #self.stop_netflix()
            # for i in range(5):
            #     self.keyevent(21)
            # time.sleep(1)
            # self.keyevent(22)
            # time.sleep(1)
            # self.enter()
            # time.sleep(1)
            # self.login()
            # time.sleep(20)
            # self.enter()
            # self.home()
            # time.sleep(3)
            # self.stop_netflix()
        else:
            logging.info('Netflix account logged in.start testing')

    @allure.step("Check login status and login Netflix")
    def login_netflix(self, device):
        '''
        set ui enter login interface
        @return: None
        '''
        if self.getprop("ro.build.version.sdk") != "34":
            self.open_omx_info()
            self.checkoutput('tee_provision -q -t 0x43')
        check_account = str(self.subprocess_run('ls -la /data/data/com.netflix.ninja/files/activated'))

        if 'returncode=1' in check_account:
            logging.info("Start to login Netflix")
            os.system(f"adb -s {device} shell monkey -p {self.PACKAGE_NAME} 1")
            time.sleep(60)
            os.system(f"adb -s {device} shell \"input keyevent 21;input keyevent 23\"")
            time.sleep(5)
            os.system(f"adb -s {device} shell \"input keyevent 22;input keyevent 23\"")
            time.sleep(2)
            os.system(f"adb -s {device} shell input text {self.ACCOUNT}")
            time.sleep(3)
            os.system(
                f"adb -s {device} shell \"input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 23\"")
            time.sleep(3)
            os.system(f"adb -s {device} shell input text {self.PASSWORD}")
            time.sleep(3)
            os.system(f"adb -s {device} shell \"input keyevent 20;input keyevent 20;input keyevent 23\"")
            time.sleep(30)
            os.system(f"adb -s {device} shell input keyevent 23")
            time.sleep(5)
            logging.info("Stop Netflix")
            os.system(f"adb -s {device} shell am force-stop {self.PACKAGE_NAME}")
        else:
            logging.info('Netflix account logged in.start testing')

    def netflix_setup_with_files(self, target=''):
        self.open_omx_info()
        self.checkoutput('tee_provision -q -t 0x43')
        check_account = str(self.subprocess_run('ls -la /data/data/com.netflix.ninja/files/activated'))
        logging.debug(f'check_account is {check_account}')
        if 'returncode=1' in check_account:
            res.get_target(f'Netflix/files_{target}.zip', source_path="Netflix")
            if not os.path.exists(f'./res/Netflix/files_{target}'):
                logging.info('start decompressing files_*.zip .')
                with zipfile.ZipFile(f'./res/Netflix/files_{target}.zip', 'r') as z:
                    z.extractall('res/Netflix/')
            self.root()
            self.push(f'res/Netflix/files/*', '/data/data/com.netflix.ninja/files/')
            time.sleep(5)
            self.home()
            time.sleep(3)

    # def netflix_setup_with_obs_check(self, source_name='Netflix_dvb_trunk'):
    #     '''
    #     set ui enter login interface
    #     @return: None
    #     '''
    #     global obs
    #     if source_name in obs_config_dict:
    #         config = obs_config_dict[source_name]
    #         obs = OBS(ip=config['ip'], port=config['port'], pwd=config['pwd'], source_name=config['source_name'])
    #     else:
    #         logging.info(f"Source name '{source_name}' not found in obs_config_dict.")
    #     self.open_omx_info()
    #     self.checkoutput('tee_provision -q -t 0x43')
    #     check_account = str(self.subprocess_run('ls -la /data/data/com.netflix.ninja/files/activated'))
    #     logging.debug(f'check_account is {check_account}')
    #     if 'returncode=1' in check_account:
    #         self.run_shell_cmd(f"monkey -p {self.PACKAGE_NAME} 1")
    #         time.sleep(60)
    #         logging.info('start to login')
    #         for i in range(5):
    #             self.keyevent(21)
    #         time.sleep(1)
    #         self.keyevent(22)
    #         time.sleep(1)
    #         self.enter()
    #         time.sleep(1)
    #         if not obs.screenshot_and_compare():
    #             self.enter()
    #             time.sleep(1)
    #         self.login()
    #         time.sleep(20)
    #         self.enter()
    #         self.home()
    #         time.sleep(3)
    #         self.stop_netflix()
    #     else:
    #         logging.info('Netflix account logged in.start testing')

    @allure.step("Start play Netflix video")
    def netflix_play(self, seekcheck=False):
        '''
        playback netflix video (from VIDEO_TAG_LIST)
        @param seekcheck: seek check status : boolean
        @return: playback status : boolean
        '''
        for i in self.VIDEO_TAG_LIST:
            logging.info(f"Start playing Netflix - name:{i['name']} - core:{i['core']}")
            self.playback(self.PLAYBACK_COMMAND_FORMAT, i['link'])
            time.sleep(10)  # wait Netflix start
            self.keyevent("23")  # enter play,skip preview
            if self.getprop(check_android_version.get_android_version()) != "34":
                play = self.check_playback_status()
            else:
                play = "standby"
            time.sleep(30)
            if play:
                player_check.check_secure()
                assert player_check.run_check_main_thread(during=30), f'play_error: {i}'
                player_check.reset()  # reset frame_temp list
            else:
                return False
            if seekcheck == "True":
                pass
            self.stop_netflix()
        return True
